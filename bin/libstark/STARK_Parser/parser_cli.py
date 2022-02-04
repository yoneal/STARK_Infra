#Version of main.py for CLI usage

#Python Standard Library
import json
import os

#Extra modules
import yaml

#Private modules
import parse_stark_settings as stark_settings_parser
import convert_friendly_to_system as converter
import parse_api_gateway as api_gateway_parser
import parse_cloudfront as cloudfront_parser
import parse_dynamodb as dynamodb_parser
import parse_datamodel as model_parser
import parse_lambda as lambda_parser
import parse_layers as layer_parser
import parse_sqs as sqs_parser
import parse_s3 as s3_parser

#Get environment variable - this will allow us to take different branches depending on whether we are LOCAL or PROD (or any other future valid value)
ENV_TYPE = os.environ['STARK_ENVIRONMENT_TYPE']
if ENV_TYPE == "PROD":
    #We may need environment detection in the future (e.g., SaaS offerings), but for now just a stub
    pass
else:
    pass

def parse(construct_file):

    with open(construct_file) as f:
        data_model = yaml.safe_load(f.read())

    entities = []

    #Some essential project metadata
    #   These won't be in the construct file provided by the user (that would be redundant and tiresome)
    #   so we have to get this from the project's existing cloud_resources document
    with open("../cloud_resources.yml", "r") as f:
        current_cloud_resources = yaml.safe_load(f.read())
        project_name            = current_cloud_resources["Project Name"]
        project_varname         = converter.convert_to_system_name(project_name)
        ddb_table_name          = current_cloud_resources["DynamoDB"]["Table Name"]

    for key in data_model:
        if key == "__STARK_project_name__":
            project_name = data_model[key]
            project_varname = converter.convert_to_system_name(project_name)

        elif key == "__STARK_advanced__":
            pass

        else:
            entities.append(key)

    #####################################################
    ###START OF INFRA LIST CREATION #####################

    cloud_resources = {"Project Name": project_name} 

    data = {
        'entities': entities,
        'data_model': data_model,
        'project_name': project_name,
        'project_varname': project_varname
    }

    ###################################################################
    #S3 and API G removed for now - not needed by New Module construct.
    #S3 Bucket ###
    #cloud_resources["S3 webserve"] = s3_parser.parse(data)
    #API Gateway ###
    #cloud_resources["API Gateway"] = api_gateway_parser.parse(data)

    #Data Model ###
    cloud_resources["Data Model"] = model_parser.parse(data)

    #DynamoDB ###
    cloud_resources["DynamoDB"] = dynamodb_parser.parse(data)

    #Lambdas ###
    cloud_resources["Lambda"] = lambda_parser.parse(data)

    #SQS #######################
    #Disable for now, not yet implemented, just contains stub
    #cloud_resources["SQS"] = sqs_parser.parse(data)

    #CloudFront ##################
    #Disable for now, not yet implemented, just contains stub
    #cloud_resources["CloudFront"] = cloudfront_parser.parse(data)

    #For debugging: pretty-print the resulting JSON
    #json_formatted_str = json.dumps(cloud_resources, indent=2)
    #print(json_formatted_str)

    #############################################################
    #FUTURE: STARK-specific settings parsing will be done here 
    #cloud_resources["STARK_settings"] = stark_settings_parser.parse(data)
    #Above is just a stub; in the future, settings parser may be the first call,
    #and its results passed to all other sub-parsers above, as these STARK
    #settings may be used to modify the default behavior of the sub-parsers

    return (cloud_resources, current_cloud_resources)
