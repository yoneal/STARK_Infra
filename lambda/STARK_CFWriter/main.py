#This receives parsed data from the STARK Parser, then turns that into the
#appropriate CloudFormation template to actually create the STARK-powered system

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


#Get environment type - this will allow us to take different branches depending on whether we are LOCAL or PROD (or any other future valid value)
ENV_TYPE = os.environ['STARK_ENVIRONMENT_TYPE']
if ENV_TYPE == "PROD":
    default_response_headers = { "Content-Type": "application/json" }
    s3  = boto3.client('s3')

    #Get resource ids from STARK configuration document
    codegen_bucket_name  = os.environ['CODEGEN_BUCKET_NAME']
    response = s3.get_object(
        Bucket=codegen_bucket_name,
        Key=f'STARKConfiguration/STARK_config.yml'
    )
    config = yaml.safe_load(response['Body'].read().decode('utf-8')) 
    preloader_service_token  = config['BucketPreloaderLambda_ARN']
    cg_static_service_token  = config['CGStatic_ARN']
    cg_dynamic_service_token = config['CGDynamic_ARN']
    cicd_bucket_name         = config['CICD_Bucket_Name']

else:
    #We only have to do this because `SAM local start-api` doesn't follow CORS info from template.yml, which is bullshit
    default_response_headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*"
    }

    preloader_service_token  = "PreloaderService-FakeLocalToken"
    cg_static_service_token  = "CGStaticService-FakeLocalToken"
    cg_dynamic_service_token = "CGDynamicService-FakeLocalToken"
    codegen_bucket_name      = "codegen-fake-local-bucket"



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
    project_name      = cloud_resources["Project Name"]
    project_varname   = converter.convert_to_system_name(project_name)
    project_stackname = converter.convert_to_system_name(project_name, 'cf-stack')

    if ENV_TYPE == "PROD":
        #So that cloud_resources can be used by our CodeGen components (which are lambda-backed custom resources in this resulting CF/SAM template),
        #   we need to dump cloud_resources into the shared repository for STARK components.
        response = s3.put_object(
            Body=yaml.dump(cloud_resources, sort_keys=False, encoding='utf-8'),
            Bucket=codegen_bucket_name,
            Key=f'STARK_cloud_resources/{project_varname}.yaml',
            Metadata={
                'STARK_Description': 'Cloud resources for this project, as determined by the STARK Parser'
            }
        )

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
                        PolicyName: PolicyForSTARKCodePipelineDeployServiceRole
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
                                    Resource: '*'
        STARKProjectCodeBuildServiceRole:
            Type: AWS::IAM::Role
            Properties:
                AssumeRolePolicyDocument:
                    Version: '2012-10-17'
                    Statement: 
                        - 
                            Effect: Allow
                            Principal:
                                Service: 
                                    - 'codebuild.amazonaws.com'
                            Action: 'sts:AssumeRole'
                ManagedPolicyArns:
                    - 'arn:aws:iam::aws:policy/AmazonS3FullAccess'
                Policies:
                    - 
                        PolicyName: PolicyForSTARKProjectCodeBuildServiceRole
                        PolicyDocument:
                            Version: "2012-10-17"
                            Statement:
                                - 
                                    Effect: Allow
                                    Action:
                                        - 'logs:CreateLogGroup'
                                        - 'logs:CreateLogStream'  
                                        - 'logs:PutLogEvents'
                                        - 's3:PutObject'
                                        - 's3:GetObject'
                                        - 's3:GetObjectVersion'
                                        - 's3:GetBucketAcl'
                                        - 's3:GetBucketLocation'
                                        - 'codebuild:CreateReportGroup'
                                        - 'codebuild:CreateReport'
                                        - 'codebuild:UpdateReport'
                                        - 'codebuild:BatchPutTestCases'
                                    Resource: '*'
        STARKProjectCodePipelineServiceRole:
            Type: AWS::IAM::Role
            Properties:
                AssumeRolePolicyDocument:
                    Version: '2012-10-17'
                    Statement:
                        - 
                            Effect: Allow
                            Principal:
                                Service: 
                                    - 'codepipeline.amazonaws.com'
                            Action: 'sts:AssumeRole'
                Policies:
                    - 
                        PolicyName: PolicyForSTARKProjectCodePipelineServiceRole
                        PolicyDocument:
                            Version: '2012-10-17'
                            Statement:
                                - 
                                    Sid: VisualEditor0
                                    Effect: Allow
                                    Action:
                                        - 'opsworks:DescribeStacks'
                                        - 'rds:*'
                                        - 'devicefarm:GetRun'
                                        - 'cloudformation:CreateChangeSet'
                                        - 'autoscaling:*'
                                        - 'codebuild:BatchGetBuilds'
                                        - 'devicefarm:ScheduleRun'
                                        - 'servicecatalog:ListProvisioningArtifacts'
                                        - 'devicefarm:ListDevicePools'
                                        - 'cloudformation:UpdateStack'
                                        - 'servicecatalog:DescribeProvisioningArtifact'
                                        - 'cloudformation:DescribeChangeSet'
                                        - 'cloudformation:ExecuteChangeSet'
                                        - 'devicefarm:ListProjects'
                                        - 'sns:*'
                                        - 'lambda:ListFunctions'
                                        - 'lambda:InvokeFunction'
                                        - 'codedeploy:RegisterApplicationRevision'
                                        - 'opsworks:DescribeDeployments'
                                        - 'devicefarm:CreateUpload'
                                        - 'cloudformation:*'
                                        - 'cloudformation:DescribeStacks'
                                        - 'codecommit:GetUploadArchiveStatus'
                                        - 'cloudwatch:*'
                                        - 'cloudformation:DeleteStack'
                                        - 'opsworks:DescribeInstances'
                                        - 'ecs:*'
                                        - 'ecr:DescribeImages'
                                        - 'ec2:*'
                                        - 'codebuild:StartBuild'
                                        - 'cloudformation:ValidateTemplate'
                                        - 'opsworks:DescribeApps'
                                        - 'opsworks:UpdateStack'
                                        - 'codedeploy:CreateDeployment'
                                        - 'codedeploy:GetApplicationRevision'
                                        - 'codedeploy:GetDeploymentConfig'
                                        - 'sqs:*'
                                        - 'servicecatalog:CreateProvisioningArtifact'
                                        - 'cloudformation:DeleteChangeSet'
                                        - 'codecommit:GetCommit'
                                        - 'servicecatalog:DeleteProvisioningArtifact'
                                        - 'codedeploy:GetApplication'
                                        - 'cloudformation:SetStackPolicy'
                                        - 'codecommit:UploadArchive'
                                        - 's3:*'
                                        - 'elasticloadbalancing:*'
                                        - 'codecommit:CancelUploadArchive'
                                        - 'devicefarm:GetUpload'
                                        - 'elasticbeanstalk:*'
                                        - 'opsworks:UpdateApp'
                                        - 'opsworks:CreateDeployment'
                                        - 'cloudformation:CreateStack'
                                        - 'ssm:*'
                                        - 'codecommit:GetBranch'
                                        - 'servicecatalog:UpdateProduct'
                                        - 'codedeploy:GetDeployment'
                                        - 'opsworks:DescribeCommands'
                                    Resource: '*'
                                - 
                                    Sid: VisualEditor1
                                    Effect: Allow
                                    Action: 'iam:PassRole'
                                    Resource: '*'
                                    Condition:
                                    StringEqualsIfExists:
                                        iam:PassedToService:
                                        - 'cloudformation.amazonaws.com'
                                        - 'elasticbeanstalk.amazonaws.com'
                                        - 'ec2.amazonaws.com'
                                        - 'ecs-tasks.amazonaws.com'
                                -
                                    Sid: VisualEditor2
                                    Effect: Allow
                                    Action: 'codestar-connections:UseConnection'
                                    Resource: '*'
        STARKProjectCodePipelineDeployServiceRole:
            Type: AWS::IAM::Role
            Properties:
                AssumeRolePolicyDocument:
                    Version: '2012-10-17'
                    Statement: 
                        - 
                            Effect: Allow
                            Principal:
                                Service: 
                                    - 'cloudformation.amazonaws.com'
                            Action: 'sts:AssumeRole'
                ManagedPolicyArns:
                    - 'arn:aws:iam::aws:policy/AWSLambdaExecute'
                Policies:
                    - 
                        PolicyName: PolicyForSTARKProjectCodePipelineDeployServiceRole
                        PolicyDocument:
                            Version: '2012-10-17'
                            Statement:
                                - 
                                    Sid: VisualEditor0
                                    Effect: Allow
                                    Action:
                                        - 'iam:GetRole'
                                        - 'apigateway:*'
                                        - 'iam:CreateRole'
                                        - 'iam:DeleteRole'
                                        - 'iam:AttachRolePolicy'
                                        - 'cloudformation:CreateChangeSet'
                                        - 's3:GetBucketVersioning'
                                        - 'iam:PutRolePolicy'
                                        - 's3:GetObject'
                                        - 'iam:PassRole'
                                        - 'iam:DetachRolePolicy'
                                        - 'iam:DeleteRolePolicy'
                                        - 'ssm:*'
                                        - 'codedeploy:*'
                                        - 'lambda:*'
                                        - 's3:GetObjectVersion'
                                    Resource: '*'
        STARKProjectRepo:
            Type: AWS::CodeCommit::Repository
            Properties:
                RepositoryName: STARK_{project_varname}
                RepositoryDescription: Default Git repo for the STARK project "{project_name}"
        STARKProjectBuildProject:
            Type: AWS::CodeBuild::Project
            Properties:
                Name: STARK_{project_varname}_build
                Artifacts:
                    Type: CODEPIPELINE  
                Description: Default Build Project for the STARK project "{project_name}" CI/CD Pipeline
                Environment:
                    ComputeType: BUILD_GENERAL1_SMALL
                    Image: "aws/codebuild/standard:4.0"
                    Type: LINUX_CONTAINER
                ServiceRole: !GetAtt STARKProjectCodeBuildServiceRole.Arn
                Source:
                    Type: CODEPIPELINE
        STARKProjectCICDPipeline:
            Type: AWS::CodePipeline::Pipeline
            Properties:
                Name: STARK_{project_varname}_pipeline
                ArtifactStore: 
                    Type: S3
                    Location: {cicd_bucket_name}
                RoleArn: !GetAtt STARKProjectCodePipelineServiceRole.Arn
                Stages:
                    -
                        Name: Source
                        Actions:
                            -
                                Name: SourceAction
                                RunOrder: 1
                                ActionTypeId:
                                    Category: Source
                                    Owner: AWS
                                    Provider: CodeCommit
                                    Version: '1'
                                Configuration:
                                    RepositoryName: !GetAtt STARKProjectRepo.Name
                                    PollForSourceChanges: 'true'
                                    BranchName: master
                                InputArtifacts: []
                                OutputArtifacts:
                                    - Name: SourceArtifact
                    -
                        Name: Build
                        Actions:
                            -
                                Name: BuildAction
                                RunOrder: 2
                                ActionTypeId:
                                    Category: Build
                                    Owner: AWS
                                    Provider: CodeBuild
                                    Version: '1'
                                Configuration:
                                    ProjectName: !Ref STARKProjectBuildProject
                                InputArtifacts:
                                    - Name: SourceArtifact
                                OutputArtifacts:
                                    - Name: BuildArtifact
                    -
                        Name: Deploy
                        Actions:
                            -
                                Name: ChangeSetReplace
                                RunOrder: 3
                                ActionTypeId:
                                    Category: Deploy
                                    Owner: AWS
                                    Provider: CloudFormation
                                    Version: '1'
                                Configuration:
                                    ActionMode: CHANGE_SET_REPLACE
                                    StackName: STARK-project-{project_stackname}
                                    Capabilities: CAPABILITY_IAM,CAPABILITY_NAMED_IAM,CAPABILITY_AUTO_EXPAND
                                    ChangeSetName: STARK-project-{project_stackname}-changeset
                                    TemplatePath: "BuildArtifact::outputtemplate.yml"
                                    TemplateConfiguration: "BuildArtifact::template_configuration.json"
                                    RoleArn: !GetAtt STARKProjectCodePipelineDeployServiceRole.Arn
                                InputArtifacts:
                                    - Name: BuildArtifact
                                OutputArtifacts: []
                            -
                                Name: ExecuteChangeSet
                                RunOrder: 4
                                ActionTypeId:
                                    Category: Deploy
                                    Owner: AWS
                                    Provider: CloudFormation
                                    Version: '1'
                                Configuration:
                                    ActionMode: CHANGE_SET_EXECUTE
                                    StackName: STARK-project-{project_stackname}
                                    Capabilities: CAPABILITY_IAM,CAPABILITY_NAMED_IAM,CAPABILITY_AUTO_EXPAND
                                    ChangeSetName: STARK-project-{project_stackname}-changeset
                                InputArtifacts:
                                    - Name: BuildArtifact
                                OutputArtifacts: []

        STARKFilesPreloader:
            Type: AWS::CloudFormation::CustomResource
            Properties:
                ServiceToken: {preloader_service_token}
                UpdateToken: {update_token}
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
        STARKCGStatic:
            Type: AWS::CloudFormation::CustomResource
            Properties:
                ServiceToken: {cg_static_service_token}
                UpdateToken: {update_token}
                Project: {project_name}
                Bucket: !Ref STARKSystemBucket
                ApiGatewayId: !Ref STARKApiGateway
                Remarks: This will create the customized STARK HTML/CSS/JS files into the STARKSystemBucket, based on the supplied entities
            DependsOn:
                -   STARKSystemBucket
                -   STARKApiGateway
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
                Handler: lambda_function.lambda_handler
                CodeUri: s3://{codegen_bucket_name}/codegen_dynamic/{project_varname}/{update_token}/{entity_endpoint_name}.zip
                Role: !GetAtt STARKProjectDefaultLambdaServiceRole.Arn
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
                CodeUri: s3://{codegen_bucket_name}/codegen_dynamic/{project_varname}/{update_token}/sys_modules.zip
                Role: !GetAtt STARKProjectDefaultLambdaServiceRole.Arn
            DependsOn:
                -   STARKCGDynamic"""

    if ENV_TYPE == "PROD":
        response = s3.put_object(
            Body=textwrap.dedent(cf_template).encode(),
            Bucket=codegen_bucket_name,
            Key=f'codegen_dynamic/{project_varname}/STARK_SAM_{project_varname}.yaml',
            Metadata={
                'STARK_Description': 'Writer output for CloudFormation'
            }
        )
    else:
        print(textwrap.dedent(cf_template))


    return {
        "isBase64Encoded": False,
        "statusCode": 200,
        "body": json.dumps("Success"),
        "headers": default_response_headers
    }
