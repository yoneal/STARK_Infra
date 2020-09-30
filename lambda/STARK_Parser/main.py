#Handles the POST action of the STARK PARSE POC, but using YAML, HTTP API version.
#Updated to handle POST request from JS FETCH API, using application/json content-type.

#Python Standard Library
import base64
import json
from collections import OrderedDict 

#Extra modules
import yaml
import boto3

#Private modules
import parse_stark_settings as stark_settings_parser
import parse_api_gateway as api_gateway_parser
import parse_cloudfront as cloudfront_parser
import parse_dynamodb as dynamodb_parser
import parse_lambda as lambda_parser
import parse_sqs as sqs_parser
import parse_s3 as s3_parser

#We need SSM to access the Parameter Store, where the function name of the CF Writer lambda will be stored
#We don't want to hard-code that name here, that's yucky
ssm_client              = boto3.client('ssm')
CFWriter_FuncName       = ssm_client.get_parameter(Name='STARK_CFWriter_FunctionName').get('Parameter', {}).get('Value', '')

#And of course a Lambda client, so we can invoke the function whose name we retrieved above
lambda_client = boto3.client('lambda')

def lambda_handler(event, context):

    if CFWriter_FuncName == '':
        #We should totally bail now, because this means there's an
        #internal error with the STARK infra
        return {
          "isBase64Encoded": False,
          "statusCode": 500,
          "body": json.dumps("STARK Internal Error - no CFWriter function name found!"),
          "headers": {
            "Content-Type": "application/json",
          }
        }

    isBase64Encoded = event.get('isBase64Encoded', False)
    raw_data_model = event.get('body', '')

    if isBase64Encoded:
        raw_data_model = base64.b64decode(raw_data_model).decode()

    jsonified_payload = json.loads(raw_data_model)
    data_model = yaml.safe_load(jsonified_payload["data_model"])

    #Debugging only
    #print("****************************")
    #print(data_model.get('__STARK_project_name__'))

    entities = []
    project_name = ""
    project_varname = ""

    for key in data_model:
        if key == "__STARK_project_name__":
            project_name = data_model[key]
            if not project_name:                
                return {
                    "isBase64Encoded": False,
                    "statusCode": 200,
                    "body": json.dumps("Code:NoProjectName"),
                    "headers": {
                        "Content-Type": "application/json",
                }
            }
            #FIXME: This needs a better sanitizer
            project_varname = project_name.replace(" ", "_").lower()

        elif key == "__STARK_advanced__":
            pass

        else:
            entities.append(key)

    #####################################################
    ###START OF INFRA LIST CREATION #####################

    cloud_resources = {}
    cloud_resources = {"Project Name": project_name, "CodeGen_Metadata" : {}} 
  
    cloud_resources['CodeGen_Metadata']['STARK_CodeGen_ApiGatewayId_ParameterName'] = "STARK_CodeGen_ApiGatewayId_" + project_varname
    cloud_resources['CodeGen_Metadata']['Entities'] = entities

    data = {
        'entities': entities
        'data_model': data_model,
        'project_name': project_name,
        'project_varname': project_varname
    }

    #S3 Bucket ###
    cloud_resources["S3 webserve"] = s3_parser.parse(data)

    #API Gateway ###
    cloud_resources["API Gateway"] = api_gateway_parser.parse(data)

    #Lambdas ###
    cloud_resources["Lambda"] = lambda_parser.parse(data)

    #DynamoDB #######################
    cloud_resources["DynamoDB"] = dynamodb_parser.parse(data)

    #SQS #######################
    cloud_resources["SQS"] = sqs_parser.parse(data)

    #CloudFront
    cloud_resources["CloudFront"] = cloudfront_parser.parse(data)

    #For debugging: pretty-print the resulting JSON
    #json_formatted_str = json.dumps(cloud_resources, indent=2)
    #print(json_formatted_str)


    #####################################################################################
    #FIXME: In PROD version, all calls below should be a Web API call, not Lambda invokes
    #####################################################################################
 
    #PAYLOAD FORMAT NOTE:
    #   If parser needs to specifically pass a YAML document, use:
    #       Payload=json.dumps(yaml.dump(cloud_resources))

    response = lambda_client.invoke(
        FunctionName = CFWriter_FuncName,
        InvocationType = 'RequestResponse',
        LogType= 'Tail',
        Payload=json.dumps(cloud_resources)
    )
    
    return {
        "isBase64Encoded": False,
        "statusCode": 200,
        "body": json.dumps("Success"),
        "headers": {
            "Content-Type": "application/json",
        }
    }