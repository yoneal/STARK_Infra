#STARK Code Generator component.
#Produces the customized static content for a STARK system.

#Python Standard Library
import base64
import json
import os
import textwrap

#Extra modules
import yaml
import boto3
from crhelper import CfnResource

#Private modules
import cgstatic_js_app as cg_js_app
import cgstatic_js_view as cg_js_view
import cgstatic_js_homepage as cg_js_home
import cgstatic_js_stark as cg_js_stark
import cgstatic_html_add  as cg_add
import cgstatic_html_edit as cg_edit
import cgstatic_html_view as cg_view
import cgstatic_html_delete as cg_delete
import cgstatic_html_listview as cg_listview
import cgstatic_html_homepage as cg_homepage
import convert_friendly_to_system as converter

s3  = boto3.client('s3')
api = boto3.client('apigatewayv2')
git = boto3.client('codecommit')

helper = CfnResource() #We're using the AWS-provided helper library to minimize the tedious boilerplate just to signal back to CloudFormation

@helper.create
@helper.update
def create_handler(event, context):
    #Project, bucket name and API Gateway ID from our CF template
    bucket_name     = event.get('ResourceProperties', {}).get('Bucket','')
    project_name    = event.get('ResourceProperties', {}).get('Project','')
    project_varname = converter.convert_to_system_name(project_name)
    api_gateway_id  = event.get('ResourceProperties', {}).get('ApiGatewayId','')
    response = api.get_api(ApiId=api_gateway_id)
    endpoint = response['ApiEndpoint']

    #Bucket for our cloud resources document
    codegen_bucket_name = os.environ['CODEGEN_BUCKET_NAME']

    #Cloud resources document
    response = s3.get_object(
        Bucket=codegen_bucket_name,
        Key=f'STARK_cloud_resources/{project_varname}.yaml'
    )
    cloud_resources = yaml.safe_load(response['Body'].read().decode('utf-8')) 

    #Get relevant info from cloud_resources
    models          = cloud_resources["DynamoDB"]["Models"]

    #STARK main JS file
    data = { 'API Endpoint': endpoint, 'Entities': models }
    deploy(cg_js_stark.create(data), bucket_name=bucket_name, key=f"js/STARK.js", files_to_commit=files_to_commit)

    #For each entity, we'll create a set of HTML and JS Files
    files_to_commit = []
    for entity in models:
        pk   = models[entity]["pk"]
        cols = models[entity]["data"]
        cgstatic_data = { "Entity": entity, "PK": pk, "Columns": cols, "Bucket Name": bucket_name, "Project Name": project_name }
        entity_varname = converter.convert_to_system_name(entity)

        deploy(source_code=cg_add.create(cgstatic_data), bucket_name=bucket_name, key=f"{entity_varname}_add.html", files_to_commit=files_to_commit)
        deploy(source_code=cg_edit.create(cgstatic_data), bucket_name=bucket_name, key=f"{entity_varname}_edit.html", files_to_commit=files_to_commit)
        deploy(source_code=cg_delete.create(cgstatic_data), bucket_name=bucket_name, key=f"{entity_varname}_delete.html", files_to_commit=files_to_commit)
        deploy(source_code=cg_view.create(cgstatic_data), bucket_name=bucket_name, key=f"{entity_varname}_view.html", files_to_commit=files_to_commit)
        deploy(source_code=cg_listview.create(cgstatic_data), bucket_name=bucket_name, key=f"{entity_varname}.html", files_to_commit=files_to_commit)
        deploy(source_code=cg_js_app.create(cgstatic_data), bucket_name=bucket_name, key=f"js/{entity_varname}_app.js", files_to_commit=files_to_commit)
        deploy(source_code=cg_js_view.create(cgstatic_data), bucket_name=bucket_name, key=f"js/{entity_varname}_view.js", files_to_commit=files_to_commit)
  
    #HTML+JS for our homepage
    homepage_data = { "Project Name": project_name }
    deploy(source_code=cg_homepage.create(homepage_data), bucket_name=bucket_name, key=f"index.html", files_to_commit=files_to_commit)
    deploy(source_code=cg_js_home.create(homepage_data), bucket_name=bucket_name, key=f"js/STARK_home.js", files_to_commit=files_to_commit)

    ############################################
    #Commit our static files to the project repo
    response = git.create_commit(
        repositoryName=repo_name,
        branchName='master',
        authorName='STARK',
        email='STARK@fakedomainstark.com',
        commitMessage='Initial commit of static files',
        putFiles=files_to_commit
    )



@helper.delete
def no_op(_, __):
    pass


def lambda_handler(event, context):
    helper(event, context)


def deploy(source_code, bucket_name, key, files_to_commit):

    files_to_commit.append({
        'filePath': f"static/{key}",
        'fileContent': source_code.encode()
    })

    response = s3.put_object(
        ACL='public-read',
        Body=source_code.encode(),
        Bucket=bucket_name,
        Key=key,
        ContentType="text/html",
    )


    return response

