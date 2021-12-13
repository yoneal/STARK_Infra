#Tracks status of CF Deploy after it is successfully triggered by STARK_Deploy

#Python Standard Library
import base64
import json
import textwrap
from time import sleep

#Extra modules
import yaml
import boto3
import botocore

#Private modules
import convert_friendly_to_system as converter

cfn = boto3.client('cloudformation')
s3  = boto3.client('s3')

stack_map = {
    0: 'CI/CD Pipeline',
    1: 'System Bootstrapper',
    2: 'Main Application' 
} 

def lambda_handler(event, context):


    isBase64Encoded = event.get('isBase64Encoded', False)
    raw_data_model  = event.get('body', '')

    if isBase64Encoded:
        raw_data_model = base64.b64decode(raw_data_model).decode()

    jsonified_payload = json.loads(raw_data_model)
    current_stack     = jsonified_payload['current_stack']
    data_model        = yaml.safe_load(jsonified_payload['data_model'])
    project_name      = data_model.get('__STARK_project_name__')
    project_stackname = converter.convert_to_system_name(project_name, 'cf-stack')

    #Stack to track is either the CI/CD Pipeline stack, the bootstrapper, or the main application
    #   The bootstrapper and the main application operate on the same stack (same name)
    if current_stack == 0:
        CF_stack_name = f"CICD-pipeline-{project_stackname}"
    else:
        CF_stack_name = f"STARK-project-{project_stackname}"

    print('Sleeping for 10!')
    sleep(10)

    try:
        response          = cfn.describe_stacks( StackName=CF_stack_name )
        print(response)
        stack_status      = response['Stacks'][0]['StackStatus']
    except botocore.exceptions.ClientError as error:
        if error.response['Error']['Code'] == 'ValidationError':
            if CF_stack_name == f"STARK-project-{project_stackname}":
                #We should just wait again, the application sometimes takes a while.
                #   We'll let the client decide how long to retry when it comes to ValidationErrors here
                #   Implementing client-side retries makes more sense, since our lambda function is stateless.
                payload = {
                    'current_stack': current_stack,
                    'status': 'STACK_NOT_FOUND',
                    'retry': True,
                    'result': 'STACK_NOT_FOUND',
                    'url': ''
                }

                return {
                    "isBase64Encoded": False,
                    "statusCode": 200,
                    "body": json.dumps(payload),
                    "headers": {
                        "Content-Type": "application/json",
                    }
                }

    print("Current stack: " + str(current_stack))
    print("Stack status: " + stack_status)

    url           = ''
    result        = ''
    if stack_status in [ 'CREATE_COMPLETE', 'UPDATE_COMPLETE' ]:

        stack_description = response['Stacks'][0]['Description']
        print("Stack description: " + stack_description)

        if current_stack < 2:
            result = 'SUCCESS'
            retry = True
            #Tell client to ask for tracking of the next stack
            current_stack = current_stack + 1

        elif current_stack == 2 and stack_description != "Bootstrapper":
            response = cfn.describe_stack_resource(
                StackName=CF_stack_name,
                LogicalResourceId='STARKSystemBucket'
            )

            result          = 'SUCCESS'
            retry           = False
            bucket_name     = response['StackResourceDetail']['PhysicalResourceId']
            response        = s3.get_bucket_location(Bucket=bucket_name)
            bucket_location = response['LocationConstraint']
            url             = f"http://{bucket_name}.s3-website-{bucket_location}.amazonaws.com/"
        else:
            #Tell client to keep tracking stack 2. We're still waiting for the
            #   CI/CD pipeline to update the stack from bootstrapper to main application
            retry         = True
            result        = ''
            current_stack = 2


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
        result = ''
        retry = True


    payload = {
        'current_stack': current_stack,
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