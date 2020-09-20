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

    CF_stack_name = (data_model.get('__STARK_project_name__')).replace(" ", "").lower()

    
    print("Sleep for 10!")
    sleep(10)

    response = client.describe_stacks(
        StackName=CF_stack_name
    )

    stack_status = response['Stacks'][0]['StackStatus']


    url    = ''
    result = ''
    if stack_status == 'CREATE_COMPLETE':

        response = client.describe_stack_resource(
            StackName=CF_stack_name,
            LogicalResourceId='STARKSystemBucket'
        )

        result = 'SUCCESS'
        retry  = False
        url    = response['StackResourceDetail']['PhysicalResourceId']
        url    = "http://" + url + ".s3-website-ap-southeast-1.amazonaws.com/"

    elif stack_status == 'CREATE_FAILED':
        result = 'FAILED'
        retry = False

    elif stack_status == 'ROLLBACK_IN_PROGRESS':
        result = 'FAILED'
        retry = False

    elif stack_status == 'ROLLBACK_COMPLETE':
        result = 'FAILED'
        retry = False

    elif stack_status == 'DELETE_IN_PROGRESS':
        result = 'FAILED'
        retry = False

    elif stack_status == 'DELETE_COMPLETE':
        result = 'FAILED'
        retry = False
        
    else:
        result = 'FAILED'
        retry = True


    payload = {
        'status': stack_status,
        'retry': retry,
        'result': result,
        'url': url
    }

    return {
        "isBase64Encoded": False,
        "statusCode": 200,
        "body": json.dumps(payload),
        "headers": {
            "Content-Type": "application/json",
        }
    }