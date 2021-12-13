#Handles the POST action of the STARK DEPLOY POC, but using YAML

#Python Standard Library
import base64
import json
import os
import textwrap
from time import sleep

#Extra modules
import yaml
import boto3
from botocore.exceptions import ClientError

#Private modules
import convert_friendly_to_system as converter

cfn = boto3.client('cloudformation')
s3  = boto3.client('s3')

def lambda_handler(event, context):

    isBase64Encoded = event.get('isBase64Encoded', False)
    raw_data_model = event.get('body', '')

    if isBase64Encoded:
        raw_data_model = base64.b64decode(raw_data_model).decode()

    codegen_bucket_name = os.environ['CODEGEN_BUCKET_NAME']
    jsonified_payload   = json.loads(raw_data_model)
    data_model          = yaml.safe_load(jsonified_payload["data_model"])
    project_varname     = converter.convert_to_system_name(data_model.get('__STARK_project_name__'))
    project_stack_name  = converter.convert_to_system_name(data_model.get('__STARK_project_name__'), "cf-stack")
    response            = s3.get_bucket_location(Bucket=codegen_bucket_name)
    bucket_location     = response['LocationConstraint']
    CF_url              = f'https://{codegen_bucket_name}.s3-{bucket_location}.amazonaws.com/codegen_dynamic/{project_varname}/STARK_SAM_{project_varname}.yaml'
    CF_stack_name       = f'CICD-pipeline-{project_stack_name}'

    #We need the service role for Cloudformation from our central config file
    response = s3.get_object(
        Bucket=codegen_bucket_name,
        Key=f'STARKConfiguration/STARK_config.yml'
    )
    config = yaml.safe_load(response['Body'].read().decode('utf-8')) 
    cf_deploy_role_arn = config['CFDeployRole_ARN']

    print (f'Trying to execute CF for template: STARK_SAM_{project_varname}.yaml')
    print (f'URL: {CF_url}')

    payload = ""
    try:
        response = cfn.create_stack(
            StackName=CF_stack_name,
            TemplateURL=CF_url,
            TimeoutInMinutes=10,
            Capabilities=[
                'CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM', 'CAPABILITY_AUTO_EXPAND',
            ],
            RoleARN=cf_deploy_role_arn,
            OnFailure='DELETE',
            EnableTerminationProtection=False
        )

    except ClientError as error:

        if error.response['Error']['Code'] == 'AlreadyExistsException':
            response = cfn.update_stack(
                StackName=CF_stack_name,
                TemplateURL=CF_url,
                Capabilities=[
                    'CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM', 'CAPABILITY_AUTO_EXPAND',
                ],
                RoleARN=cf_deploy_role_arn,
            )            
        else:
            payload = {
                'status': 'CloudFormation Execution Failed',
                'message': "Sorry, STARK failed to deploy due to an internal error. It's not you, it's us! {" + error.response['Error']['Code'] + " for template " + project_varname + ".yaml}",
                'retry': False
            }
            print(error.response['Error'])


    if payload == "":
        payload = {
            'status': 'CloudFormation Execution Started',
            'message': "Look at you, testing out next-gen serverless tech! Don't worry, it's coming!",
            'retry': True
        }




    return {
        "isBase64Encoded": False,
        "statusCode": 200,
        "body": json.dumps(payload),
        "headers": {
            "Content-Type": "application/json",
        }
    }