#Handles the POST action of the STARK DEPLOY POC, but using YAML

#Python Standard Library
import base64
import json
import textwrap
from time import sleep

#Extra modules
import yaml
import boto3
from botocore.exceptions import ClientError

#Private modules
import convert_friendly_to_system as converter

client = boto3.client('cloudformation')

def lambda_handler(event, context):

    isBase64Encoded = event.get('isBase64Encoded', False)
    raw_data_model = event.get('body', '')

    if isBase64Encoded:
        raw_data_model = base64.b64decode(raw_data_model).decode()

    jsonified_payload = json.loads(raw_data_model)
    data_model = yaml.safe_load(jsonified_payload["data_model"])

    project_varname = converter.convert_to_system_name(data_model.get('__STARK_project_name__'))
    CF_stack_name   = converter.convert_to_system_name(data_model.get('__STARK_project_name__'), "cf-stack")

    CF_url = f'https://waynestark-stark-prototype-codegenbucket.s3-ap-southeast-1.amazonaws.com/STARK_SAM_{project_varname}.yaml'

    print (f'Trying to execute CF for template: STARK_SAM_{project_varname}.yaml')

    payload = ""
    try:
        response = client.create_stack(
            StackName=CF_stack_name,
            TemplateURL=CF_url,
            TimeoutInMinutes=10,
            Capabilities=[
                'CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM', 'CAPABILITY_AUTO_EXPAND',
            ],
            RoleARN='arn:aws:iam::201649379729:role/STARK_POC_Deploy_CloudFormationServiceRole',
            OnFailure='DELETE',
            EnableTerminationProtection=False
        )

    except ClientError as error:

        if error.response['Error']['Code'] == 'AlreadyExistsException':
            response = client.update_stack(
                StackName=CF_stack_name,
                TemplateURL=CF_url,
                Capabilities=[
                    'CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM', 'CAPABILITY_AUTO_EXPAND',
                ],
                RoleARN='arn:aws:iam::201649379729:role/STARK_POC_Deploy_CloudFormationServiceRole',
            )            
        else:
            payload = {
                'status': 'CloudFormation Execution Failed',
                'message': "Sorry, STARK failed to deploy due to an internal error. It's not you, it's us! {" + error.response['Error']['Code'] + " for template " + project_varname + ".yaml}",
                'retry': False
            }        


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