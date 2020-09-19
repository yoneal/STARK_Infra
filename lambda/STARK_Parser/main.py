#Handles the POST action of the STARK PARSE POC, but using YAML, HTTP API version.
#Updated to handle POST request from JS FETCH API, using application/json content-type.

#Python Standard Library
import base64
import json
import textwrap
from collections import OrderedDict 

#Extra modules
import yaml
import boto3

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


    print("****************************")
    print(data_model.get('__STARK_project_name__'))

    #Get models ("tables" in RDBMS)
    models = []
    project_name = ""
    project_varname = ""
    ddb_table_name = ""
    s3_static_bucket_name = ""
    ddb_auto_scaling = False
    ddb_surge_protection = False
    ddb_surge_protection_fifo = False
    ddb_capacity_type = "provisioned"
    ddb_rcu_provisioned = 3
    ddb_wcu_provisioned = 3
    cf_enable = False
    cf_regions = []
    cf_price_class = 100

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
            project_varname = project_name.replace(" ", "_").lower()
        elif key == "__STARK_advanced__":
            ddb_table_name = data_model[key].get('ddb_table_name', "")
            ddb_surge_protection = data_model[key].get('ddb_surge_protection', False)
            ddb_surge_protection_fifo = data_model[key].get('ddb_surge_protection_fifo', False)
            ddb_auto_scaling = data_model[key].get('ddb_auto_scaling', False)
            ddb_capacity_type = data_model[key].get('ddb_capacity_type', "provisioned")
            ddb_rcu_provisioned = data_model[key].get('ddb_rcu_provisioned', 3)
            ddb_wcu_provisioned = data_model[key].get('ddb_wcu_provisioned', 3)
            cf_enable = data_model[key].get('cf_enable', False)
            cf_regions = data_model[key].get('cf_regions', [])
            cf_price_class = data_model[key].get('cf_price_class', 100)
            s3_static_bucket_name = data_model[key].get('s3_static_bucket_name', "")
            s3_webserve_only = data_model[key].get('s3_webserve_only', True)
        else:
            models.append(key)

    if ddb_table_name == "":
        ddb_table_name = project_varname  + "_ddb"

    if s3_static_bucket_name == "":
        s3_static_bucket_name = project_varname + "-stark-dynamic-site"
    #Sample of removing invalid characters in bucket name, replacing with acceptable ones
    s3_static_bucket_name = s3_static_bucket_name.replace("_", "-")

    if ddb_auto_scaling:
        ddb_auto_scaling = "ENABLED"
    else:
        ddb_auto_scaling = "OFF"

    print(models)
    print(len(models))

    #####################################################
    ###START OF INFRA LIST CREATION #####################

    #This is what will actually be passed to CFWriter (or similar components that ingest usable STARK parser output).
    #Use triple-quoted f-strings, then use textwrap.dedent at the end to strip extra whitespaces c/o code indentation
    cloud_resources = {}
    cloud_resources = {"Project Name": project_name, "CodeGen_Metadata" : {}} 
  
    #FIXME: This probably belongs to the yet-to-exist Orchestrator component, instead of Parser itself? (Still debating if Parser should be Orchestrator)
    #Dynamic resource names or IDs needed fby Code Gen later.
    cloud_resources['CodeGen_Metadata']['STARK_CodeGen_ApiGatewayId_ParameterName'] = "STARK_CodeGen_ApiGatewayId_" + project_varname
    cloud_resources['CodeGen_Metadata']['Entities'] = models

    #S3 Bucket
    cloud_resources["S3 webserve"] = {
        "bucket_name": s3_static_bucket_name,
        "error_document": "error.html",
        "index_document": "index.html"
    }

    #API Gateway #######################
    cloud_resources["API Gateway"] = {
        "entities": [] #Entities will be converted to routes by the writer. Some transformation will be needed for non-URL friendly entity names
    }

    for model in models:
        cloud_resources['API Gateway']['entities'].append(model)

    #Lambdas #######################
    cloud_resources["Lambda"] = {
        "entities": [] #Each entity will be its own lambda function, and will become integrations for API gateway routes
    }

    for model in models:
        cloud_resources['Lambda']['entities'].append(model)

    #DynamoDB #######################
    cloud_resources["DynamoDB"] = {
        "Table Name": ddb_table_name,
        "Capacity Type": ddb_capacity_type,
        "Surge Protection": ddb_surge_protection,
        "Surge Protection FIFO": ddb_surge_protection_fifo,
        "Models": {}
    }

    if ddb_capacity_type == "provisioned":
        cloud_resources["DynamoDB"]["RCU"] = ddb_rcu_provisioned
        cloud_resources["DynamoDB"]["WCU"] = ddb_wcu_provisioned
        cloud_resources["DynamoDB"]["Auto Scaling"] = ddb_auto_scaling

    for model in models:
        cloud_resources["DynamoDB"]["Models"][model] = {}
        cloud_resources["DynamoDB"]["Models"][model]["pk"] = data_model.get(model).get('pk')
        cloud_resources["DynamoDB"]["Models"][model]["data"] = OrderedDict() 


        attributes = ''
        for column_dict in data_model.get(model).get("data"):
            # `column_dict` here is a dictionary with a single key and value: { "Column Name": "Column Type" }
            #  So while we're accessing it now through a for loop, there's really just one value. MAY CHANGE IN FUTURE

            for key, value in column_dict.items():
                column   = key
                col_type = value

            cloud_resources["DynamoDB"]["Models"][model]["data"][column] = col_type

            if isinstance(col_type, list):
                attributes += column + "(Enum: ["
                for item in col_type:
                    attributes += item  + ", "
                attributes = attributes[:-2]  
                attributes += "]),"           
            elif isinstance(col_type, str):
                attributes += column + "(" + col_type + "),"
        attributes = attributes[:-1]

    #SQS #######################
    cloud_resources["SQS"] = {}

    if ddb_surge_protection:
        #SQS Queue

        if ddb_surge_protection_fifo:
            cloud_resources["SQS"]["Queue Type"] = "FIFO"
            cloud_resources["SQS"]["Queue Name"] = project_varname + "_write_queue_fifo"
        else:
            cloud_resources["SQS"]["Queue Type"] = "Standard"
            cloud_resources["SQS"]["Queue Name"] = project_varname + "_write_queue"
            cloud_resources["SQS"]["DLQ Name"]   = project_varname + "_write_queue_dlq"

    #CloudFront
    cloud_resources["CloudFront"] = {
        "Enabled": cf_enable,
        "Price Class": str(cf_price_class)
    }

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