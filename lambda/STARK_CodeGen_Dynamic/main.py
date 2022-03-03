#STARK Code Generator component.
#Produces the customized dynamic content for a STARK system (Lambda / serverless resources)

#Python Standard Library
import base64
import json
import os
import textwrap

#Extra modules
import yaml
import boto3
from crhelper import CfnResource

#Private modules
import cgdynamic_login as cg_login
import cgdynamic_logout as cg_logout
import cgdynamic_modules as cg_mod
import cgdynamic_dynamodb as cg_ddb
import cgdynamic_buildspec as cg_build
import cgdynamic_authorizer as cg_auth
import cgdynamic_sam_template as cg_sam
import cgdynamic_template_conf as cg_conf
import convert_friendly_to_system as converter

s3  = boto3.client('s3')
lmb = boto3.client('lambda')
git = boto3.client('codecommit')

helper = CfnResource() #We're using the AWS-provided helper library to minimize the tedious boilerplate just to signal back to CloudFormation

@helper.create
@helper.update
def create_handler(event, context):
    #Project name from our CF template
    project_name    = event.get('ResourceProperties', {}).get('Project','')
    repo_name       = event.get('ResourceProperties', {}).get('RepoName','')
    website_bucket  = event.get('ResourceProperties', {}).get('Bucket','')
    cicd_bucket     = event.get('ResourceProperties', {}).get('CICDBucket','')

    project_varname = converter.convert_to_system_name(project_name)

    #DynamoDB table name from our CF template
    ddb_table_name = event.get('ResourceProperties', {}).get('DDBTable','')

    #Cloud resources document
    codegen_bucket_name = os.environ['CODEGEN_BUCKET_NAME']
    response = s3.get_object(
        Bucket=codegen_bucket_name,
        Key=f'STARK_cloud_resources/{project_varname}.yaml'
    )
    cloud_resources = yaml.safe_load(response['Body'].read().decode('utf-8')) 


    models   = cloud_resources["Data Model"]
    entities = []
    for entity in models: entities.append(entity)

    ##########################################
    #Create code for our entity Lambdas (API endpoint backing)
    files_to_commit = []
    for entity in entities:
        entity_varname = converter.convert_to_system_name(entity) 
        #Step 1: generate source code.
        data = {
            "Entity": entity, 
            "Columns": models[entity]["data"], 
            "PK": models[entity]["pk"], 
            "DynamoDB Name": ddb_table_name
        }
        source_code = cg_ddb.create(data)

        #Step 2: Add source code to our commit list to the project repo
        files_to_commit.append({
            'filePath': f"lambda/{entity_varname}/main.py",
            'fileContent': source_code.encode()
        })


    ################################################
    #Create our Lambda for the /sys_modules API endpoint
    source_code, yaml_code = cg_mod.create({"Entities": entities})
    files_to_commit.append({
        'filePath': f"lambda/sys_modules/main.py",
        'fileContent': source_code.encode()
    })
    files_to_commit.append({
        'filePath': f"lambda/sys_modules/modules.yml",
        'fileContent': yaml_code.encode()
    })

    ###########################################################
    #Create our Lambda for the /login and /logout API endpoints
    source_code, stark_scrypt = cg_login.create({"DynamoDB Name": ddb_table_name})    
    files_to_commit.append({
        'filePath': f"lambda/login/main.py",
        'fileContent': source_code.encode()
    })
    files_to_commit.append({
        'filePath': f"lambda/login/stark_scrypt.py",
        'fileContent': stark_scrypt.encode()
    })
    

    source_code = cg_logout.create({"DynamoDB Name": ddb_table_name})
    files_to_commit.append({
        'filePath': f"lambda/logout/main.py",
        'fileContent': source_code.encode()
    })

    #################################################
    #Create our Lambda Authorizer for our API Gateway
    source_code = cg_auth.create({"DynamoDB Name": ddb_table_name})
    files_to_commit.append({
        'filePath': f"lambda/authorizer_default/main.py",
        'fileContent': source_code.encode()
    })

    ############################################
    #Create build files we need for our pipeline:
    # - template.yml
    # - buildspec.yml
    # - template_configuration.json
    data = { 'project_varname': project_varname }

    source_code = cg_build.create(data)
    files_to_commit.append({
        'filePath': "buildspec.yml",
        'fileContent': source_code.encode()
    })

    data = { 'cloud_resources': cloud_resources, 'entities': entities }
    source_code = cg_sam.create(data)
    files_to_commit.append({
        'filePath': "template.yml",
        'fileContent': source_code.encode()
    })

    data = {
        'cicd_bucket': cicd_bucket,
        'website_bucket': website_bucket
    }
    source_code = cg_conf.create(data)
    files_to_commit.append({
        'filePath': "template_configuration.json",
        'fileContent': source_code.encode()
    })
   


    ##################################################
    #Commit files to the project repo
    #   There's a codecommit limit of 100 files - this will fail if more than 100 static files are needed,
    #   such as if a dozen or so entities are requested for code generation. Implement commit chunking here for safety.
    ctr                 = 0
    key                 = 0
    chunked_commit_list = {}
    for item in files_to_commit:
        if ctr == 100:
            key = key + 1
            ctr = 0
        ctr = ctr + 1
        if chunked_commit_list.get(key, '') == '':
            chunked_commit_list[key] = []
        chunked_commit_list[key].append(item)

    ctr         = 0
    batch_count = key + 1
    for commit_batch in chunked_commit_list:
        ctr = ctr + 1

        response = git.get_branch(
            repositoryName=repo_name,
            branchName='master'        
        )
        commit_id = response['branch']['commitId']

        response = git.create_commit(
            repositoryName=repo_name,
            branchName='master',
            parentCommitId=commit_id,
            authorName='STARK::CGDynamic',
            email='STARK@fakedomainstark.com',
            commitMessage=f'Initial commit of Lambda source codes (commit {ctr} of {batch_count})',
            putFiles=files_to_commit
        )


@helper.delete
def no_op(_, __):
    #Nothing to do, our Lambdas will be deleted by CloudFormation
    pass


def lambda_handler(event, context):
    helper(event, context)
