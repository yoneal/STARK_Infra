#STARK Code Generator component.
#Produces the customized dynamic content for a STARK system
#This creates the SAM template.yml file to create the end-user's system infra

#Python Standard Library
import base64
from html import entities
import json
import os
import textwrap
from uuid import uuid4

#Extra modules
import yaml
import boto3

#Private modules
import convert_friendly_to_system as converter


def create(data, cli_mode=False):

    cloud_resources = data['cloud_resources']

    #Get environment type - this will allow us to take different branches depending on whether we are LOCAL or PROD (or any other future valid value)
    ENV_TYPE = os.environ['STARK_ENVIRONMENT_TYPE']
    if ENV_TYPE == "PROD" or cli_mode == True:
        default_response_headers = { "Content-Type": "application/json" }
        s3  = boto3.client('s3')

        if cli_mode == True:
            cleaner_service_token   = data['Cleaner_ARN']
            prelaunch_service_token = data['Prelaunch_ARN']
            cicd_bucket_name        = data['CICD_Bucket_Name']
            codegen_bucket_name     = data['CodeGen_Bucket_Name']
        else:
            codegen_bucket_name = os.environ['CODEGEN_BUCKET_NAME']

            response = s3.get_object(
                Bucket=codegen_bucket_name,
                Key=f'STARKConfiguration/STARK_config.yml'
            )
            config = yaml.safe_load(response['Body'].read().decode('utf-8'))
            cleaner_service_token   = config['Cleaner_ARN']
            prelaunch_service_token = config['Prelaunch_ARN']
            cicd_bucket_name        = config['CICD_Bucket_Name']

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
    s3_bucket_name    = cloud_resources["S3 webserve"]["Bucket Name"].lower()
    s3_error_document = cloud_resources["S3 webserve"]["Error Document"]
    s3_index_document = cloud_resources["S3 webserve"]["Index Document"]

    #DynamoDB-related data
    ddb_table_name            = cloud_resources["DynamoDB"]['Table Name']
    ddb_capacity_type         = cloud_resources["DynamoDB"]['Capacity Type'].upper()
    ddb_surge_protection      = cloud_resources["DynamoDB"]['Surge Protection']
    ddb_surge_protection_fifo = cloud_resources["DynamoDB"]['Surge Protection FIFO']
    ddb_rcu_provisioned       = cloud_resources["DynamoDB"].get("RCU", 0)
    ddb_wcu_provisioned       = cloud_resources["DynamoDB"].get("WCU", 0)
    ddb_auto_scaling          = cloud_resources["DynamoDB"].get("Auto Scaling", '')

    #Lambda-related data
    entities = cloud_resources['Data Model']

    #FIXME: Should this transformation be here or in the Parser?
    #Let this remain here now, but probably should be the job of the parser in the future.
    if ddb_capacity_type != "PROVISIONED":
        ddb_capacity_type = "PAY_PER_REQUEST"

    #Some default values not yet from the Parser, but should be added to Parser later
    s3_versioning     = "Enabled"
    s3_access_control = "PublicRead"

    #Update Token - this token forces CloudFormation to update the resources that do dynamic code generation,
    update_token = str(uuid4())

    #Initialize our template
    #This is where we can use triple-quoted f-strings + textwrap.dedent(), instead of manually placing tabs and nl, unreadable!
    #The forward slash ( \ ) is so that we don't have an empty blank line at the top of our resulting file.
    #FIXME: instead of a RegionMap Mappings section here, can we just use pure python to handle the inconsistency in S3 website endpoints?
    #       Perhaps the prepackaged boto3 in Lambda already has region info baked in, we can then simplify this CF template and handle the
    #       inconsistency in S3 endpoints like we did in STARK_Deploy_Check 
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
    Mappings:
        RegionMap:
            us-east-2:
                s3endpoint: "s3-website.us-east-2.amazonaws.com"
            us-east-1:
                s3endpoint: "s3-website-us-east-1.amazonaws.com"
            us-west-1:
                s3endpoint: "s3-website-us-west-1.amazonaws.com"
            us-west-2:
                s3endpoint: "s3-website-us-west-2.amazonaws.com"
            af-south-1:
                s3endpoint: "s3-website.af-south-1.amazonaws.com"
            ap-east-1:
                s3endpoint: "s3-website.ap-east-1.amazonaws.com"
            ap-south-1:
                s3endpoint: "s3-website.ap-south-1.amazonaws.com"
            ap-northeast-3:
                s3endpoint: "s3-website.ap-northeast-3.amazonaws.com"
            ap-northeast-2:
                s3endpoint: "s3-website.ap-northeast-2.amazonaws.com"
            ap-southeast-1:
                s3endpoint: "s3-website-ap-southeast-1.amazonaws.com"
            ap-southeast-2:
                s3endpoint: "s3-website-ap-southeast-2.amazonaws.com"
            ap-northeast-1:
                s3endpoint: "s3-website-ap-northeast-1.amazonaws.com"
            ca-central-1:
                s3endpoint: "s3-website.ca-central-1.amazonaws.com"
            cn-northwest-1:
                s3endpoint: "s3-website.cn-northwest-1.amazonaws.com.cn"
            eu-central-1:
                s3endpoint: "s3-website.eu-central-1.amazonaws.com"
            eu-west-1:
                s3endpoint: "s3-website-eu-west-1.amazonaws.com"
            eu-west-2:
                s3endpoint: "s3-website.eu-west-2.amazonaws.com"
            eu-south-1:
                s3endpoint: "s3-website.eu-south-1.amazonaws.com"
            eu-west-3:
                s3endpoint: "s3-website.eu-west-3.amazonaws.com"
            eu-north-1:
                s3endpoint: "s3-website.eu-north-1.amazonaws.com"
            ap-southeast-3:
                s3endpoint: "s3-website.ap-southeast-3.amazonaws.com"
            me-south-1:
                s3endpoint: "s3-website.me-south-1.amazonaws.com"
            sa-east-1:
                s3endpoint: "s3-website-sa-east-1.amazonaws.com"
            us-gov-east-1:
                s3endpoint: "s3-website.us-gov-east-1.amazonaws.com"
            us-gov-west-1:
                s3endpoint: "s3-website-us-gov-west-1.amazonaws.com"

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
                                    Resource: 
                                        - !Join [ ":", [ "arn:aws:dynamodb", !Ref AWS::Region, !Ref AWS::AccountId, "table/{ddb_table_name}"] ]
                                        - !Join [ ":", [ "arn:aws:dynamodb", !Ref AWS::Region, !Ref AWS::AccountId, "table/{ddb_table_name}/index/STARK-ListView-Index", ] ]
        STARKProjectDefaultAuthorizerInvokeRole:
            Type: AWS::IAM::Role
            Properties:
                AssumeRolePolicyDocument:
                    Version: '2012-10-17'
                    Statement: 
                        - 
                            Effect: Allow
                            Principal:
                                Service: 
                                    - 'apigateway.amazonaws.com'
                            Action: 'sts:AssumeRole'
                Policies:
                    - 
                        PolicyName: PolicyForSTARKProjectDefaultAuthorizerInvokeRole
                        PolicyDocument:
                            Version: '2012-10-17'
                            Statement:
                                - 
                                    Sid: VisualEditor0
                                    Effect: Allow
                                    Action:
                                        - 'lambda:InvokeFunction'
                                    Resource: !GetAtt STARKDefaultAuthorizerFunc.Arn
        CFCustomResourceHelperLayer:
            Type: AWS::Lambda::LayerVersion
            Properties:
                Content:
                    S3Bucket: !Ref UserCICDPipelineBucketNameParameter
                    S3Key: {project_varname}/STARKLambdaLayers/CF_CustomResourceHelper_py39.zip
                Description: Lambda-backed custom resource library for CloudFormation
                LayerName: {project_varname}_CF_CustomResourceHelper
                CompatibleArchitectures:
                    - x86_64
                    - arm64
                CompatibleRuntimes:
                    - python3.6
                    - python3.7
                    - python3.8
                    - python3.9
        PyYamlLayer:
            Type: AWS::Lambda::LayerVersion
            Properties:
                Content:
                    S3Bucket: !Ref UserCICDPipelineBucketNameParameter
                    S3Key: {project_varname}/STARKLambdaLayers/yaml_py39.zip
                Description: YAML module for Python 3.x
                LayerName: {project_varname}_PyYAML
                CompatibleArchitectures:
                    - x86_64
                    - arm64
                CompatibleRuntimes:
                    - python3.6
                    - python3.7
                    - python3.8
                    - python3.9
        RequestsLayer:
            Type: AWS::Lambda::LayerVersion
            Properties:
                Content:
                    S3Bucket: !Ref UserCICDPipelineBucketNameParameter
                    S3Key: {project_varname}/STARKLambdaLayers/requests_py39.zip
                Description: Requests module for Python 3.x
                LayerName: {project_varname}_Requests
                CompatibleArchitectures:
                    - x86_64
                    - arm64
                CompatibleRuntimes:
                    - python3.6
                    - python3.7
                    - python3.8
                    - python3.9
        STARKFriendlyToSystemNamesLayer:
            Type: AWS::Lambda::LayerVersion
            Properties:
                Content:
                    S3Bucket: !Ref UserCICDPipelineBucketNameParameter
                    S3Key: {project_varname}/STARKLambdaLayers/STARK_friendly_to_system_name_py39.zip
                Description: STARK module for converting user-supplied, human-friendly identifiers into system-friendly entity or variable names
                LayerName: {project_varname}_friendly_to_system_name
                CompatibleArchitectures:
                    - x86_64
                    - arm64
                CompatibleRuntimes:
                    - python3.6
                    - python3.7
                    - python3.8
                    - python3.9
        STARKScryptLayer:
            Type: AWS::Lambda::LayerVersion
            Properties:
                Content:
                    S3Bucket: !Ref UserCICDPipelineBucketNameParameter
                    S3Key:  {project_varname}/STARKLambdaLayers/STARK_scrypt_py39.zip
                Description: STARK module for working with scrypt from the Python stdlib
                LayerName: {project_varname}_scrypt
                CompatibleArchitectures:
                    - x86_64
                    - arm64
                CompatibleRuntimes:
                    - python3.6
                    - python3.7
                    - python3.8
                    - python3.9
        STARKLayerMakerFunc:
            Type: AWS::Serverless::Function
            Properties:
                Runtime: python3.9
                Handler: main.lambda_handler
                CodeUri: 
                    Bucket: {codegen_bucket_name}
                    Key: STARKLambdaFunctions/STARK_LayerMaker.zip
                Environment:
                    Variables:
                        STARK_ENVIRONMENT_TYPE: PROD
                        Project_Name: {project_name}
                        CICD_Bucket_Name: {cicd_bucket_name}
                Policies:
                    - AmazonS3FullAccess
                Layers:
                    - !Ref PyYamlLayer
                    - !Ref STARKFriendlyToSystemNamesLayer
                Architectures:
                    - arm64
                MemorySize: 128
                Timeout: 60
        STARKDefaultAuthorizerFunc:
            Type: AWS::Serverless::Function
            Properties:
                Runtime: python3.9
                Handler: main.lambda_handler
                CodeUri: lambda/authorizer_default
                Role: !GetAtt STARKProjectDefaultLambdaServiceRole.Arn
                Architectures:
                    - arm64
                MemorySize: 128
                Timeout: 5
        STARKApiGateway:
            Type: AWS::Serverless::HttpApi
            Properties:
                Auth:
                    Authorizers:
                        STARKDefaultAuthorizer:
                            AuthorizerPayloadFormatVersion: 2.0
                            EnableSimpleResponses: True
                            FunctionArn: !GetAtt STARKDefaultAuthorizerFunc.Arn
                            FunctionInvokeRole: !GetAtt STARKProjectDefaultAuthorizerInvokeRole.Arn
                            Identity:
                                Headers: 
                                    - cookie
                                ReauthorizeEvery: 300
                    DefaultAuthorizer: STARKDefaultAuthorizer
                CorsConfiguration:
                    AllowOrigins:
                        - !Join [ "", [ "http://{s3_bucket_name}.", !FindInMap [ RegionMap, !Ref AWS::Region, s3endpoint] ] ]
                        - http://localhost
                    AllowHeaders:
                        - "Content-Type"
                        - "*"
                    AllowMethods:
                        - GET
                        - POST
                        - PUT
                        - DELETE
                    AllowCredentials: True
                    MaxAge: 200
        STARKDynamoDB:
            Type: AWS::DynamoDB::Table
            Properties:
                TableName: {ddb_table_name}
                BillingMode: {ddb_capacity_type}
                TimeToLiveSpecification:
                    AttributeName: TTL
                    Enabled: True
                AttributeDefinitions:
                    -
                        AttributeName: pk
                        AttributeType: S
                    -
                        AttributeName: sk
                        AttributeType: S
                    -
                        AttributeName: STARK-ListView-sk
                        AttributeType: S
                GlobalSecondaryIndexes:
                    -
                        IndexName: STARK-ListView-Index
                        KeySchema:
                            -
                                AttributeName: sk
                                KeyType: HASH
                            -
                                AttributeName: STARK-ListView-sk
                                KeyType: RANGE
                        Projection: 
                            ProjectionType: ALL"""

    if ddb_capacity_type == "PROVISIONED":
        cf_template += f"""
                        ProvisionedThroughput:
                            ReadCapacityUnits: {ddb_rcu_provisioned}
                            WriteCapacityUnits: {ddb_wcu_provisioned}"""

    cf_template += f"""
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

    for entity in entities:
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
                Runtime: python3.9
                Handler: main.lambda_handler
                CodeUri: lambda/{entity_endpoint_name}
                Role: !GetAtt STARKProjectDefaultLambdaServiceRole.Arn
                Architectures:
                    - arm64
                MemorySize: 128
                Timeout: 5"""
    
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
                Runtime: python3.9
                Handler: main.lambda_handler
                CodeUri: lambda/sys_modules
                Role: !GetAtt STARKProjectDefaultLambdaServiceRole.Arn
                Architectures:
                    - arm64
                MemorySize: 128
                Timeout: 5
                Layers:
                    - !Ref PyYamlLayer
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
                            Auth:
                                Authorizer: NONE
                Runtime: python3.9
                Handler: main.lambda_handler
                CodeUri: lambda/login
                Role: !GetAtt STARKProjectDefaultLambdaServiceRole.Arn
                Layers:
                    - !Ref STARKScryptLayer
                Architectures:
                    - arm64
                MemorySize: 1792
                Timeout: 5
        STARKBackendApiForLogout:
            Type: AWS::Serverless::Function
            Properties:
                Events:
                    LoginPostEvent:
                        Type: HttpApi
                        Properties:
                            Path: /logout
                            Method: POST
                            ApiId:
                                Ref: STARKApiGateway
                Runtime: python3.9
                Handler: main.lambda_handler
                CodeUri: lambda/logout
                Role: !GetAtt STARKProjectDefaultLambdaServiceRole.Arn
                Architectures:
                    - arm64
                MemorySize: 128
                Timeout: 5
        STARKPreLaunch:
            Type: AWS::CloudFormation::CustomResource
            Properties:
                ServiceToken: {prelaunch_service_token}
                UpdateToken: REPLACE-ME-ONLY-FOR-RELAUNCHES
                Project: {project_name}
                DDBTable: {ddb_table_name}
                Remarks: Final system pre-launch tasks - things to do after the entirety of the new system's infra and code have been deployed
            DependsOn:
                - STARKApiGateway
                - STARKBackendApiForLogin
                - STARKBackendApiForSysModules
                - STARKBucketCleaner
                - STARKDynamoDB
                - STARKProjectDefaultLambdaServiceRole
        """

    return textwrap.dedent(cf_template)