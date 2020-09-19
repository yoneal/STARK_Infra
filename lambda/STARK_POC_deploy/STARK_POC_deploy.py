#Handles the POST action of the STARK DEPLOY POC, but using YAML

#Python Standard Library
import base64
import json
import textwrap
from time import sleep

#Extra modules
import yaml
import boto3

client = boto3.client('cloudformation')

def lambda_handler(event, context):

    isBase64Encoded = event.get('isBase64Encoded', False)
    raw_data_model = event.get('body', '')

    if isBase64Encoded:
        raw_data_model = base64.b64decode(raw_data_model).decode()

    jsonified_payload = json.loads(raw_data_model)
    data_model = yaml.safe_load(jsonified_payload["data_model"])

    project_name = (data_model.get('__STARK_project_name__')).replace(" ", "")

    
    #FIXME: Hard-coded for now. Should be based on project name and API key
    CF_url = 'https://waynestark-common-archive.s3-ap-southeast-1.amazonaws.com/CFWriter_test.yaml'


    response = client.create_stack(
        StackName=project_name,
        TemplateURL=CF_url,
        TimeoutInMinutes=10,
        Capabilities=[
            'CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM', 'CAPABILITY_AUTO_EXPAND',
        ],
        RoleARN='arn:aws:iam::201649379729:role/STARK_POC_Deploy_CloudFormationServiceRole',
        OnFailure='DELETE',
        EnableTerminationProtection=False
    )

    payload = {
        'status': 'CloudFormation Execution Started',
        'message': "Look at you, testing out next-gen serverless tech! Don't worry, it's coming!",
        'retry': True #FIXME: hard-coded for now, but for prod check response first. This will be false if create_stack() errors out.
    }


    return {
        "isBase64Encoded": False,
        "statusCode": 200,
        "body": json.dumps(payload),
        "headers": {
            "Content-Type": "application/json",
        }
    }