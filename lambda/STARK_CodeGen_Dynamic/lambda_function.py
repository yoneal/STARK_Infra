#STARK Code Generator component.
#Produces the customized dynamic content for a STARK system (Lambda / serverless resources)

#Python Standard Library
import base64
import json
import textwrap
import zipfile

#Extra modules
import yaml
import boto3
from crhelper import CfnResource

#Private modules
import cgdynamic_modules as cg_mod
import cgdynamic_dynamodb as cg_ddb

s3  = boto3.client('s3')
ssm = boto3.client('ssm')
lmb = boto3.client('lambda')

lambda_path_filename = '/tmp/lambda_function.py'
lambda_path_zipfile = '/tmp/lambda.zip'

helper = CfnResource() #We're using the AWS-provided helper library to minimize the tedious boilerplate just to signal back to CloudFormation

@helper.create
@helper.update
def create_handler(event, context):
    #Project name from our CF template
    project_name    = event.get('ResourceProperties', {}).get('Project','')
    project_varname = project_name.replace(" ", "_").lower()

    #UpdateToken = we need this as part of the Lambda deployment package path, to force CF to redeploy our Lambdas
    update_token = event.get('ResourceProperties', {}).get('UpdateToken','')

    #DynamoDB table name from our CF template
    ddb_table_name = event.get('ResourceProperties', {}).get('DDBTable','')

    #Bucket for our generated lambda deploymentment packages
    codegen_bucket_name = ssm.get_parameter(Name="STARK_CodeGenBucketName").get('Parameter', {}).get('Value')


    #FIXME: Temporary way to retrieve cloud_resources. PROD version will use S3 file for unlimited length.
    cloud_resources = yaml.safe_load(ssm.get_parameter(Name="STARK_cloud_resources_" + project_varname).get('Parameter', {}).get('Value'))

    entities = cloud_resources['CodeGen_Metadata']['Entities']
    #FIXME: Now that we're using the DynamoDB models, we don't actually need the Entities metatada... consider removing it
    models   = cloud_resources["DynamoDB"]["Models"]


    cleanup_tmp() #just to make we have a consistent starting point in /tmp, no matter the potential error state of the last execution

    ##########################################
    #Create our entity Lambdas (API endpoint backing)
    for entity in entities:
        #Step 1: generate source code.
        data = {
            "Entity": entity.replace(" ", "_").lower(), 
            "Columns": models[entity]["data"], 
            "PK": models[entity]["pk"], 
            "DynamoDB Name": ddb_table_name
        }
        source_code = cg_ddb.create(data)

        #Step 2: write source code to a source file in /tmp
        create_source_file(source_code)

        #Step 3: zip the source file to create a Lambda deployment package
        create_zip_file()

        #Step 4: create Lambda deployment package, send to S3
        deploy_lambda({
            'Project': project_varname, 
            'Entity': entity.replace(" ", "_").lower(),
            'Bucket': codegen_bucket_name,
            'Update Token': update_token
        })

        #Step 5: cleanup /tmp
        cleanup_tmp()

    ################################################
    #Create our Lambda for the /modules API endpoint
    source_code = cg_mod.create({"Entities": entities})
    create_source_file(source_code)
    create_zip_file()
    deploy_lambda({
            'Project': project_varname, 
            'Entity': 'sys_modules',
            'Bucket': codegen_bucket_name,
            'Update Token': update_token
    })


@helper.delete
def no_op(_, __):
    #Nothing to do, our Lambdas will be deleted by CloudFormation
    #I suppose we could do cleanup like emptying our deployment packages
    #in S3, but that doesn't really matter

    pass


def lambda_handler(event, context):
    helper(event, context)


def create_source_file(source_code):

    with open(lambda_path_filename, 'w') as source_file:
        source_file.write(source_code)

    return 0

def create_zip_file():
    zipfile.ZipFile(lambda_path_zipfile, mode='w').write(lambda_path_filename, arcname="lambda_function.py")

    return 0

def deploy_lambda(data):
    project = data['Project']
    entity  = data['Entity']
    bucket  = data['Bucket']
    token   = data['Update Token']
    key     = f"{project}/{token}/{entity}.zip"

    print(f"Deploying {key}...")

    response = s3.upload_file(lambda_path_zipfile, bucket, key)

    print(response)

    print(f"Deployed {key}...")


    return response

def cleanup_tmp():
    #FIXME: Actually implement this if still needed, otherwise remove
    status = ""

    return status
