#STARK Code Generator component.
#Produces the customized dynamic content for a STARK system
#This creates the SAM template.yml file to create the end-user's system infra

#Python Standard Library
import base64
import json
import os
import textwrap
from uuid import uuid4

#Extra modules
import yaml
import boto3

#Private modules
import convert_friendly_to_system as converter


def create(data):

    cloud_resources = data['cloud_resources']

    #Get environment type - this will allow us to take different branches depending on whether we are LOCAL or PROD (or any other future valid value)
    ENV_TYPE = os.environ['STARK_ENVIRONMENT_TYPE']
    if ENV_TYPE == "PROD":
        default_response_headers = { "Content-Type": "application/json" }
        s3  = boto3.client('s3')

        codegen_bucket_name  = os.environ['CODEGEN_BUCKET_NAME']
        response = s3.get_object(
            Bucket=codegen_bucket_name,
            Key=f'STARKConfiguration/STARK_config.yml'
        )
        config = yaml.safe_load(response['Body'].read().decode('utf-8')) 
        cleaner_service_token    = config['Cleaner_ARN']  

    else:
        #We only have to do this because `SAM local start-api` doesn't follow CORS info from template.yml, which is bullshit
        default_response_headers = {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        }
        codegen_bucket_name      = "codegen-fake-local-bucket"
        cleaner_service_token    = "CleanerService-FakeLocalToken"


    #Get Project Name
    #FIXME: Project Name is used here as unique identifier. For now it's a user-supplied string, which is unreliable
    #       as a unique identifier. Make this a GUID for prod use.
    #       We do still need a user-supplied project name for display purposes (header of each HTML page, login screen, etc), though.
    project_name      = cloud_resources["Project Name"]
    project_varname   = converter.convert_to_system_name(project_name)
    project_stackname = converter.convert_to_system_name(project_name, 'cf-stack')

    ###############################################################################################################
    #Load and sanitize data here, for whatever IaC rules that govern them (e.g., S3 Bucket names must be lowercase)

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
    Description: STARK-generated serverless application, Project [{project_name}]
    Parameters:
        UserCICDPipelineBucketNameParameter:
            Type: String
            Description: Name for user bucket that will be used for the default STARK CI/CD pipeline.
        UserWebsiteBucketNameParameter:
            Type: String
            Description: Name for user bucket that will be used as the website bucket for the STARK Parser UI. Not yet used in template, just needed for config.
    Resources:
        STARKSystemBucket:
            Type: AWS::S3::Bucket
            Properties:
                AccessControl: {s3_access_control}
                BucketName: !Ref UserWebsiteBucketNameParameter
                VersioningConfiguration:
                    Status: {s3_versioning}
                WebsiteConfiguration:
                    ErrorDocument: {s3_error_document}
                    IndexDocument: {s3_index_document}
        STARKBucketCleaner:
            Type: AWS::CloudFormation::CustomResource
            Properties:
                ServiceToken: {cleaner_service_token}
                UpdateToken: {update_token}
                Bucket:
                    Ref: STARKSystemBucket
                Remarks: This will empty the STARKSystemBucket for DELETE STACK operations
            DependsOn:
                -   STARKSystemBucket
        STARKProjectDefaultLambdaServiceRole:
            Type: AWS::IAM::Role
            Properties:
                AssumeRolePolicyDocument:
                    Version: '2012-10-17'
                    Statement: 
                        - 
                            Effect: Allow
                            Principal:
                                Service: 
                                    - 'lambda.amazonaws.com'
                            Action: 'sts:AssumeRole'
                ManagedPolicyArns:
                    - 'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'
                Policies:
                    - 
                        PolicyName: PolicyForSTARKProjectDefaultLambdaServiceRole
                        PolicyDocument:
                            Version: '2012-10-17'
                            Statement:
                                - 
                                    Sid: VisualEditor0
                                    Effect: Allow
                                    Action:
                                        - 'iam:GetRole'
                                        - 'dynamodb:BatchGetItem'
                                        - 'dynamodb:BatchWriteItem'
                                        - 'dynamodb:ConditionCheckItem'
                                        - 'dynamodb:PutItem'
                                        - 'dynamodb:DeleteItem'
                                        - 'dynamodb:GetItem'
                                        - 'dynamodb:Scan'
                                        - 'dynamodb:Query'
                                        - 'dynamodb:UpdateItem'
                                    Resource: !Join [ ":", [ "arn:aws:dynamodb", !Ref AWS::Region, !Ref AWS::AccountId, "table/{ddb_table_name}"] ]
        CFCustomResourceHelperLayer:
            Type: AWS::Lambda::LayerVersion
            Properties:
                Content:
                    S3Bucket: !Ref UserCICDPipelineBucketNameParameter
                    S3Key: {project_varname}/STARKLambdaLayers/CF_CustomResourceHelper_py38.zip
                Description: Lambda-backed custom resource library for CloudFormation
                LayerName: {project_varname}_CF_CustomResourceHelper
        PyYamlLayer:
            Type: AWS::Lambda::LayerVersion
            Properties:
                Content:
                    S3Bucket: !Ref UserCICDPipelineBucketNameParameter
                    S3Key: {project_varname}/STARKLambdaLayers/yaml_py38.zip
                Description: YAML module for Python 3.x
                LayerName: {project_varname}_PyYAML
        BcryptLayer:
            Type: AWS::Lambda::LayerVersion
            Properties:
                Content:
                    S3Bucket: !Ref UserCICDPipelineBucketNameParameter
                    S3Key: {project_varname}/STARKLambdaLayers/bcrypt_py39.zip
                Description: bcrypt module for Python 3.9
                LayerName: {project_varname}_bcrypt       
        STARKApiGateway:
            Type: AWS::Serverless::HttpApi
            Properties:
                CorsConfiguration:
                    AllowOrigins:
                        - !Join [ "", [ "http://{s3_bucket_name}.s3-website-", !Ref AWS::Region, ".amazonaws.com"] ]
                        - http://localhost
                    AllowHeaders:
                        - "Content-Type"
                        - "*"
                    AllowMethods:
                        - "*"
                    AllowCredentials: True
                    MaxAge: 200
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
        entity_logical_name = converter.convert_to_system_name(entity, "cf-resource")
        entity_endpoint_name = converter.convert_to_system_name(entity)
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
                Handler: main.lambda_handler
                CodeUri: lambda/{entity_endpoint_name}
                Role: !GetAtt STARKProjectDefaultLambdaServiceRole.Arn"""

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
                Handler: main.lambda_handler
                CodeUri: lambda/sys_modules
                Role: !GetAtt STARKProjectDefaultLambdaServiceRole.Arn
        STARKBackendApiForLogin:
            Type: AWS::Serverless::Function
            Properties:
                Events:
                    LoginPostEvent:
                        Type: HttpApi
                        Properties:
                            Path: /login
                            Method: POST
                            ApiId:
                                Ref: STARKApiGateway
                Runtime: python3.9
                Handler: main.lambda_handler
                CodeUri: lambda/login
                Role: !GetAtt STARKProjectDefaultLambdaServiceRole.Arn
                Layers:
                    - !Ref BcryptLayer
                MemorySize: 1760
                Timeout: 5
        """

    return textwrap.dedent(cf_template)