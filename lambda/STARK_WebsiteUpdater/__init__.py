#This is the Lambda function of the Lamba-backed custom resource used
#   during the deployment of STARK infrastructure itself.  
#   This will write the API Gateway ID into the JS config file.

#Python Standard Library
import base64
import json
import os
import textwrap

#Extra modules
import boto3
from crhelper import CfnResource

s3  = boto3.client('s3')
api = boto3.client('apigatewayv2')

website_bucket_name = os.environ['WEBSITE_BUCKET_NAME']
api_gateway_id      = os.environ['API_GATEWAY_ID']
helper = CfnResource() #We're using the AWS-provided helper library to minimize the tedious boilerplate just to signal back to CloudFormation


@helper.create
@helper.update
def update_config_file(event, _):
    response = api.get_api(ApiId=api_gateway_id)
    endpoint = response['ApiEndpoint']

    print(f"Updating config file with {endpoint} within {website_bucket_name}...")

    source_code = f"""\
        const STARK={{
            'parser_url':'{endpoint}/parser',
            'deploy_url':'{endpoint}/deploy',
            'deploy_check_url':'{endpoint}/deploy_check'
        }};"""

    source_code = textwrap.dedent(source_code)
    print(source_code)
    deploy(source_code=source_code, bucket_name=website_bucket_name, key=f"js/STARK_settings.js")


@helper.delete
def delete_action(event, _):
    print("Delete action - no action...")

def lambda_handler(event, context):
    helper(event, context)

def deploy(source_code, bucket_name, key):

    response = s3.put_object(
        ACL='public-read',
        Body=source_code.encode(),
        Bucket=bucket_name,
        Key=key,
        ContentType="text/javascript",
    )

    return response
