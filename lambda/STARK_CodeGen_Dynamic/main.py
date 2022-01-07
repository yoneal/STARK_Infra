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

    #UpdateToken = we need this as part of the Lambda deployment package path, to force CF to redeploy our Lambdas
    update_token = event.get('ResourceProperties', {}).get('UpdateToken','')

    #DynamoDB table name from our CF template
    ddb_table_name = event.get('ResourceProperties', {}).get('DDBTable','')

    #Bucket for our generated lambda deploymentment packages and cloud resources document
    codegen_bucket_name = os.environ['CODEGEN_BUCKET_NAME']

    #Cloud resources document
    response = s3.get_object(
        Bucket=codegen_bucket_name,
        Key=f'STARK_cloud_resources/{project_varname}.yaml'
    )
    cloud_resources = yaml.safe_load(response['Body'].read().decode('utf-8')) 


    entities = cloud_resources['CodeGen_Metadata']['Entities']
    #FIXME: Now that we're using the DynamoDB models, we don't actually need the Entities metatada... consider removing it
    models   = cloud_resources["DynamoDB"]["Models"]

    ##########################################
    #Creat code for our entity Lambdas (API endpoint backing)
    files_to_commit = []
    for entity in entities:
        entity_varname = converter.convert_to_system_name(entity) 
        #Step 1: generate source code.
        data = {
            "Entity": entity_varname, 
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
    source_code = cg_mod.create({"Entities": entities})
    files_to_commit.append({
        'filePath': f"lambda/sys_modules/main.py",
        'fileContent': source_code.encode()
    })

    ###########################################################
    #Create our Lambda for the /login and /logout API endpoints
    source_code = cg_login.create({"DynamoDB Name": ddb_table_name})    
    files_to_commit.append({
        'filePath': f"lambda/login/main.py",
        'fileContent': source_code.encode()
    })
    source_code = cg_logout.create({"DynamoDB Name": ddb_table_name})
    files_to_commit.append({
        'filePath': f"lambda/logout/main.py",
        'fileContent': source_code.encode()
    })

    ###########################################
    #Create build files we need fo our pipeline:
    # - template.yml
    # - buildspec.yml
    # - template_configuration.json
    data = { 'project_varname': project_varname }

    source_code = cg_build.create(data)
    files_to_commit.append({
        'filePath': "buildspec.yml",
        'fileContent': source_code.encode()
    })

    data = { 
        'codegen_bucket_name': codegen_bucket_name,
        'cloud_resources': cloud_resources
    }
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
        commitMessage='Initial commit of Lambda source codes',
        putFiles=files_to_commit
    )


@helper.delete
def no_op(_, __):
    #Nothing to do, our Lambdas will be deleted by CloudFormation
    #I suppose we could do cleanup like emptying our deployment packages
    #in S3, but that doesn't really matter

    pass


def lambda_handler(event, context):
    helper(event, context)