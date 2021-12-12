#This will create files needed to bootstrap a new system after the CI/CD pipeline for it is created by STARK,
#   but before the actual system infra is laid out.

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
import bootstrap_buildspec as boot_build
import bootstrap_sam_template as boot_sam
import bootstrap_template_conf as boot_conf
import convert_friendly_to_system as converter

s3  = boto3.client('s3')
lmb = boto3.client('lambda')
git = boto3.client('codecommit')

lambda_path_filename = '/tmp/lambda_function.py'
lambda_path_zipfile = '/tmp/lambda.zip'

helper = CfnResource() #We're using the AWS-provided helper library to minimize the tedious boilerplate just to signal back to CloudFormation

@helper.create
@helper.update
def create_handler(event, context):
    project_name    = event.get('ResourceProperties', {}).get('Project','')
    repo_name       = event.get('ResourceProperties', {}).get('RepoName','')
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
    files_to_commit = []

    ###########################################
    #Create build files we need to bootstrap our pipeline:
    # - template.yml
    # - buildspec.yml
    data = {
        'project_varname': project_varname,
        'cicd_bucket': cicd_bucket
    }

    source_code = boot_build.create(data)
    files_to_commit.append({
        'filePath': "buildspec.yml",
        'fileContent': source_code.encode()
    })

    data = { 
        'cloud_resources': cloud_resources,
        'repo_name': repo_name
    }
    source_code = boot_sam.create(data)
    files_to_commit.append({
        'filePath': "template.yml",
        'fileContent': source_code.encode()
    })   

    source_code = boot_conf.create()
    files_to_commit.append({
        'filePath': "template_configuration.json",
        'fileContent': source_code.encode()
    })   


    ##################################################
    #Commit files to the project repo
    response = git.create_commit(
        repositoryName=repo_name,
        branchName='master',
        authorName='STARK::Bootstrapper',
        email='STARK@fakedomainstark.com',
        commitMessage='Initial commit - bootstrapper',
        putFiles=files_to_commit
    )


@helper.delete
def no_op(_, __):
    pass


def lambda_handler(event, context):
    helper(event, context)