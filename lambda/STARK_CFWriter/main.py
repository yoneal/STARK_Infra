#This receives parsed data from the STARK Parser, then turns that into the
#appropriate CloudFormation template to actually create the STARK-powered system

#Python Standard Library
import base64
import json
import textwrap
from uuid import uuid4

#Extra modules
import yaml
import boto3

s3  = boto3.client('s3')
ssm = boto3.client('ssm')

preloader_service_token  = ssm.get_parameter(Name="STARK_CustomResource_BucketPreloaderLambda_ARN").get('Parameter', {}).get('Value')
cg_static_service_token  = ssm.get_parameter(Name="STARK_CustomResource_CodeGenStaticLambda_ARN").get('Parameter', {}).get('Value')
cg_dynamic_service_token = ssm.get_parameter(Name="STARK_CustomResource_CodeGenDynamicLambda_ARN").get('Parameter', {}).get('Value')
codegen_bucket_name      = ssm.get_parameter(Name="STARK_CodeGenBucketName").get('Parameter', {}).get('Value')

def lambda_handler(event, context):

    #We create "cloud_resources" here like this so that even if the way we call this function changes, our "cloud_resources" assignments later on won't
    #   have to change - only this line needs to be updated (e.g., change from direct lambda invoke to web api call)
    #   If we use "event" directly, we'd end up making multiple line changes - literally every assignment we do below
    cloud_resources = event
    print(cloud_resources)

    #Get Project Name
    #FIXME: Project Name is used here as unique identifier. For now it's a user-supplied string, which is unreliable
    #       as a unique identifier. Make this a GUID for prod use.
    #       We do still need a user-supplied project name for display purposes (header of each HTML page, login screen, etc), though.
    project_name    = cloud_resources["Project Name"]
    project_varname = project_name.replace(" ", "_").lower()

    #So that cloud_resources can be used by our CodeGen components (which are lambda-backed custom resources in this resulting CF/SAM template),
    #   we need to dump cloud_resources into ParamStore as a YAML string
    response = ssm.put_parameter(
        Name="STARK_cloud_resources_" + project_varname,
        Description="Cloud resources for this project, as determined by the STARK Parser",
        Value=yaml.dump(cloud_resources, sort_keys=False),
        Type='String',
        DataType='text',
        Overwrite=True
    )
    #FIXME: Code above will work ok for YAML strings that are under 4KB (ParamStore standard tier limit).
    #       Real long-term solution should be to turn this into an S3 key, and have our YAML dumped in a STARK staging bucket instead.
    #FIXME: Also, this results in the ParamStore entry not being part of Stack, so it pollutes ParamStore because the entry created here
    #       survives the stack. This isn't a problem for S3 (we can just have a huge collection of text files there), but is a problem for
    #       ParamStore (which has a practical limit, so it can't be our "unlimited config storage" infra)


    ###############################################################################################################
    #Load and sanitize data here, for whatever IaC rules that govern them (e.g., S3 Bucket names must be lowercase)

    #Project Metadata
    ApiG_param_name = cloud_resources['CodeGen_Metadata']['STARK_CodeGen_ApiGatewayId_ParameterName']


    #S3-related data
    s3_bucket_name    = cloud_resources["S3 webserve"]["bucket_name"].lower()
    s3_error_document = cloud_resources["S3 webserve"]["error_document"]
    s3_index_document = cloud_resources["S3 webserve"]["index_document"]

    #DynamoDB-related data
    ddb_table_name            = cloud_resources["DynamoDB"]['Table Name']
    ddb_capacity_type         = cloud_resources["DynamoDB"]['Capacity Type'].upper()
    ddb_surge_protection      = cloud_resources["DynamoDB"]['Surge Protection']
    ddb_surge_protection_fifo = cloud_resources["DynamoDB"]['Surge Protection FIFO']
    ddb_models                = cloud_resources["DynamoDB"]['Models']
    ddb_rcu_provisioned       = cloud_resources["DynamoDB"].get("RCU", 0)
    ddb_wcu_provisioned       = cloud_resources["DynamoDB"].get("WCU", 0)
    ddb_auto_scaling          = cloud_resources["DynamoDB"].get("Auto Scaling", '')

    #Lambda-related data
    lambda_entities = cloud_resources['Lambda']['entities']


    #FIXME: Should this transformation be here or in the Parser?
    #Let this remain here now, but probably should be the job of the parser in the future.
    if ddb_capacity_type != "PROVISIONED":
        ddb_capacity_type = "PAY_PER_REQUEST"



    #Some default values not yet from the Parser, but should be added to Parser later
    s3_versioning     = "Enabled"
    s3_access_control = "PublicRead"



    #Update Token - this token forces CloudFormation to update the resources that do dynamic code generation,
    #               as well as forced re-deployment of Lambdas (by using this as a deployment package path/folder)
    update_token = str(uuid4())

    #Initialize our template
    #This is where we can use triple-quoted f-strings + textwrap.dedent(), instead of manually placing tabs and nl, unreadable!
    #The forward slash ( \ ) is so that we don't have an empty blank line at the top of our resulting file.
    cf_template = f"""\
    AWSTemplateFormatVersion: '2010-09-09'
    Transform: AWS::Serverless-2016-10-31
    Description: AWS SAM template for STARK code gen
    Resources:
        STARKSystemBucket:
            Type: AWS::S3::Bucket
            Properties:
                AccessControl: {s3_access_control}
                BucketName: {s3_bucket_name}
                VersioningConfiguration:
                    Status: {s3_versioning}
                WebsiteConfiguration:
                    ErrorDocument: {s3_error_document}
                    IndexDocument: {s3_index_document}
        STARKFilesPreloader:
            Type: AWS::CloudFormation::CustomResource
            Properties:
                ServiceToken: {preloader_service_token}
                Bucket:
                    Ref: STARKSystemBucket
                Remarks: This will preload all STARK HTML/CSS/JS files into the STARKSystemBucket
            DependsOn:
                -   STARKSystemBucket
        STARKApiGateway:
            Type: AWS::Serverless::HttpApi
            Properties:
                CorsConfiguration:
                    AllowOrigins:
                        - "*"
                    AllowHeaders:
                        - "*"
                    AllowMethods:
                        - "*"
                    MaxAge: 200
                    AllowCredentials: False
        STARKCodeGenParamApiId:
            Type: AWS::SSM::Parameter
            Properties:
                Name: {ApiG_param_name}
                Description: API Gateway ID of your project
                Type: String
                DataType: text
                Value: 
                    Ref: STARKApiGateway
        STARKCGStatic:
            Type: AWS::CloudFormation::CustomResource
            Properties:
                ServiceToken: {cg_static_service_token}
                UpdateToken: {update_token}
                Bucket:
                    Ref: STARKSystemBucket
                Project: {project_name}
                Remarks: This will create the customized STARK HTML/CSS/JS files into the STARKSystemBucket, based on the supplied entities
            DependsOn:
                -   STARKSystemBucket
        STARKCGDynamic:
            Type: AWS::CloudFormation::CustomResource
            Properties:
                ServiceToken: {cg_dynamic_service_token}
                UpdateToken: {update_token}
                Project: {project_name}
                DDBTable: {ddb_table_name}
                Remarks: This will create the customized STARK lambda functions, based on the supplied entities
        STARKDynamoDB:
            Type: AWS::DynamoDB::Table
            Properties:
                TableName: {ddb_table_name}
                BillingMode: {ddb_capacity_type}
                AttributeDefinitions:
                    -
                        AttributeName: pk
                        AttributeType: S
                    -
                        AttributeName: sk
                        AttributeType: S
                KeySchema:
                    -
                        AttributeName: pk
                        KeyType: HASH
                    -
                        AttributeName: sk
                        KeyType: RANGE"""

    if ddb_capacity_type == "PROVISIONED":
        cf_template += f"""
                ProvisionedThroughput:
                    ReadCapacityUnits: {ddb_rcu_provisioned}
                    WriteCapacityUnits: {ddb_wcu_provisioned}"""

    for entity in lambda_entities:
        #CF logical names must have no spaces, underscores, etc
        #FIXME: implement other necessary removals or whitelisting here
        entity_logical_name = entity.replace("_", "").replace(" ", "")
        entity_endpoint_name = entity.replace(" ", "_").lower()
        cf_template += f"""
        STARKBackendApiFor{entity_logical_name}:
            Type: AWS::Serverless::Function
            Properties:
                Events:
                    {entity_logical_name}GetEvent:
                        Type: HttpApi
                        Properties:
                            Path: /{entity_endpoint_name}
                            Method: GET
                            ApiId:
                                Ref: STARKApiGateway
                    {entity_logical_name}PostEvent:
                        Type: HttpApi
                        Properties:
                            Path: /{entity_endpoint_name}
                            Method: POST
                            ApiId:
                                Ref: STARKApiGateway
                    {entity_logical_name}PutEvent:
                        Type: HttpApi
                        Properties:
                            Path: /{entity_endpoint_name}
                            Method: PUT
                            ApiId:
                                Ref: STARKApiGateway
                    {entity_logical_name}DeleteEvent:
                        Type: HttpApi
                        Properties:
                            Path: /{entity_endpoint_name}
                            Method: DELETE
                            ApiId:
                                Ref: STARKApiGateway
                Runtime: python3.8
                Handler: lambda_function.lambda_handler
                CodeUri: s3://{codegen_bucket_name}/{project_varname}/{update_token}/{entity_endpoint_name}.zip
                Role: arn:aws:iam::201649379729:role/WayneStark_test_lambda_role_1
            DependsOn:
                -   STARKCGDynamic"""

    cf_template += f"""
        STARKBackendApiForSysModules:
            Type: AWS::Serverless::Function
            Properties:
                Events:
                    SysModulesGetEvent:
                        Type: HttpApi
                        Properties:
                            Path: /sys_modules
                            Method: GET
                            ApiId:
                                Ref: STARKApiGateway
                Runtime: python3.8
                Handler: lambda_function.lambda_handler
                CodeUri: s3://{codegen_bucket_name}/{project_varname}/{update_token}/sys_modules.zip
                Role: arn:aws:iam::201649379729:role/WayneStark_test_lambda_role_1
            DependsOn:
                -   STARKCGDynamic"""


    response = s3.put_object(
        Body=textwrap.dedent(cf_template).encode(),
        Bucket='waynestark-stark-prototype-codegenbucket',
        Key=f'STARK_SAM_{project_varname}.yaml',
        Metadata={
            'STARK_Description': 'Writer output for CloudFormation'
        }
    )



    return {
        "isBase64Encoded": False,
        "statusCode": 200,
        "body": json.dumps("Success"),
        "headers": {
            "Content-Type": "application/json",
        }
    }
