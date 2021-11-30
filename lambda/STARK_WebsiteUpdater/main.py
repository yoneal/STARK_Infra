#This is the Lambda function of the Lamba-backed custom resource used by
#   during the deployment of STARK inftastructure itself.  
#   This will write the API Gateway ID into the JS config file.

#Python Standard Library
import base64
import json
import os

#Extra modules
import boto3
from crhelper import CfnResource

s3  = boto3.resource('s3')
api = boto3.client('apigatewayv2')

website_bucket_name = os.environ['WEBSITE_BUCKET_NAME']
api_gateway_id      = os.environ['API_GATEWAY_ID']
helper = CfnResource() #We're using the AWS-provided helper library to minimize the tedious boilerplate just to signal back to CloudFormation

@helper.create
@helper.update
def update_config_file(event, _):
    response = api.get_api(ApiId=api_gateway_id)
    endpoint = response['ApiEndpoint']

    print(f"Updating config file (stub) with {endpoint} within {website_bucket_name}...")

    source_code = f"""\
        const STARK={{
            'parser_url':'https://{endpoint}.amazonaws.com/parser',
            'deploy_url':'https://{endpoint}.amazonaws.com/deploy',
            'deploy_check_url':'https://{endpoint}.amazonaws.com/deploy_check'
        }};"""

    print(source_code)


@helper.delete
def delete_action(event, _):
    print("Delete action - no action...")
    pass

def lambda_handler(event, context):
    helper(event, context)
