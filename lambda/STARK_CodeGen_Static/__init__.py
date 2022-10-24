#STARK Code Generator component.
#Produces the customized static content for a STARK system.

#Python Standard Library
import base64
import json
import pickle
import os
import textwrap

#Extra modules
import yaml
import boto3
from crhelper import CfnResource

#Private modules
import importlib

prepend_dir = ""
if 'libstark' in os.listdir():
    prepend_dir = "libstark.STARK_CodeGen_Static."

cg_js_app    = importlib.import_module(f"{prepend_dir}cgstatic_js_app")  
cg_js_view   = importlib.import_module(f"{prepend_dir}cgstatic_js_view")  
cg_js_login  = importlib.import_module(f"{prepend_dir}cgstatic_js_login")  
cg_js_home   = importlib.import_module(f"{prepend_dir}cgstatic_js_homepage")  
cg_js_stark  = importlib.import_module(f"{prepend_dir}cgstatic_js_stark")  
cg_css_login = importlib.import_module(f"{prepend_dir}cgstatic_css_login")  
cg_git       = importlib.import_module(f"{prepend_dir}cgstatic_gitignore")  
cg_add       = importlib.import_module(f"{prepend_dir}cgstatic_html_add")   
cg_edit      = importlib.import_module(f"{prepend_dir}cgstatic_html_edit")  
cg_view      = importlib.import_module(f"{prepend_dir}cgstatic_html_view")  
cg_login     = importlib.import_module(f"{prepend_dir}cgstatic_html_login")  
cg_delete    = importlib.import_module(f"{prepend_dir}cgstatic_html_delete")  
cg_listview  = importlib.import_module(f"{prepend_dir}cgstatic_html_listview")  
cg_homepage  = importlib.import_module(f"{prepend_dir}cgstatic_html_homepage")  
cg_report    = importlib.import_module(f"{prepend_dir}cgstatic_html_report")   

import convert_friendly_to_system as converter
import get_relationship as get_rel

s3   = boto3.client('s3')
api  = boto3.client('apigatewayv2')
git  = boto3.client('codecommit')
cdpl = boto3.client('codepipeline')

helper = CfnResource() #We're using the AWS-provided helper library to minimize the tedious boilerplate just to signal back to CloudFormation

@helper.create
@helper.update
def create_handler(event, context):
    #Project, bucket name and API Gateway ID from our CF template
    repo_name       = event.get('ResourceProperties', {}).get('RepoName','')
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

    #FIXME: Remove raw for now since we need to update cloud_resources with API gateway URL - hopefully using sort_keys=False will remove the need for the raw version) 
    #raw_cloud_resources = response['Body'].read().decode('utf-8')
    #cloud_resources     = yaml.safe_load(raw_cloud_resources) 
    cloud_resources = yaml.safe_load(response['Body'].read().decode('utf-8')) 

    #Get relevant info from cloud_resources
    models = cloud_resources["Data Model"]

    #Collect list of files to commit to project repository
    files_to_commit = []

    #STARK main JS file
    data = { 'API Endpoint': endpoint, 'Entities': models, "Bucket Name": bucket_name }
    add_to_commit(cg_js_stark.create(data), key=f"js/STARK.js", files_to_commit=files_to_commit, file_path='static')

    #For each entity, we'll create a set of HTML and JS Files and uploaded folder
    for entity in models:
        # print(models)
        pk   = models[entity]["pk"]
        cols = models[entity]["data"]
        relationships = get_rel.get_relationship(models, entity)
        rel_model = {}
        
        for relationship in relationships.get('has_many', []):
            if relationship.get('type') == 'repeater':
                rel_col = models.get(relationship.get('entity'), '')
                rel_model.update({(relationship.get('entity')) : rel_col})
            
        cgstatic_data = { "Entity": entity, "PK": pk, "Columns": cols, "Project Name": project_name, "Relationships": relationships, "Rel Model": rel_model }
        entity_varname = converter.convert_to_system_name(entity)

        for rel in rel_model:
            add_to_commit(source_code='', key=f"js/many_{rel}.js", files_to_commit=files_to_commit, file_path='static')

        add_to_commit(source_code=cg_add.create(cgstatic_data), key=f"{entity_varname}_add.html", files_to_commit=files_to_commit, file_path='static')
        add_to_commit(source_code=cg_edit.create(cgstatic_data), key=f"{entity_varname}_edit.html", files_to_commit=files_to_commit, file_path='static')
        add_to_commit(source_code=cg_delete.create(cgstatic_data), key=f"{entity_varname}_delete.html", files_to_commit=files_to_commit, file_path='static')
        add_to_commit(source_code=cg_view.create(cgstatic_data), key=f"{entity_varname}_view.html", files_to_commit=files_to_commit, file_path='static')
        add_to_commit(source_code=cg_listview.create(cgstatic_data), key=f"{entity_varname}.html", files_to_commit=files_to_commit, file_path='static')
        add_to_commit(source_code=cg_report.create(cgstatic_data), key=f"{entity_varname}_report.html", files_to_commit=files_to_commit, file_path='static')
        add_to_commit(source_code=cg_js_app.create(cgstatic_data), key=f"js/{entity_varname}_app.js", files_to_commit=files_to_commit, file_path='static')
        add_to_commit(source_code=cg_js_view.create(cgstatic_data), key=f"js/{entity_varname}_view.js", files_to_commit=files_to_commit, file_path='static')
        add_to_commit(source_code=f"{entity} Uploaded files", key=f"uploaded_files/{entity_varname}/README.txt", files_to_commit=files_to_commit, file_path='')
        
    #HTML+JS for our homepage
    homepage_data = { "Project Name": project_name }
    add_to_commit(source_code=cg_homepage.create(homepage_data), key=f"home.html", files_to_commit=files_to_commit, file_path='static')
    add_to_commit(source_code=cg_js_home.create(homepage_data), key=f"js/STARK_home.js", files_to_commit=files_to_commit, file_path='static')

    #Login HTML+JS+CSS
    login_data = { "Project Name": project_name }
    add_to_commit(source_code=cg_login.create(homepage_data), key=f"index.html", files_to_commit=files_to_commit, file_path='static')
    add_to_commit(source_code=cg_js_login.create(homepage_data), key=f"js/login.js", files_to_commit=files_to_commit, file_path='static')
    add_to_commit(source_code=cg_css_login.create(homepage_data), key=f"css/login.css", files_to_commit=files_to_commit, file_path='static')
    
    #TMP folder
    add_to_commit(source_code="Temporary files", key=f"tmp/README.txt", files_to_commit=files_to_commit, file_path='')

    ##########################################
    #Add cloud resources document to our files
    #First, update the API Gateway URL (it's empty when first generated by STARK Parser, as the API Gateway does not exist yet by then)
    cloud_resources['API Gateway']['URL'] = endpoint
    add_to_commit(source_code=yaml.dump(cloud_resources, sort_keys=False), key="cloud_resources.yml", files_to_commit=files_to_commit, file_path='')


    ###############################################
    #Get pre-built static files from codegen bucket
    prebuilt_static_files = []
    list_prebuilt_static_files(codegen_bucket_name, prebuilt_static_files)
    for static_file in prebuilt_static_files:
        #We don't want to include the "STARKWebSource/" prefix in our list of keys, hence the string slice in static_file
        add_to_commit(source_code=get_file_from_bucket(codegen_bucket_name, static_file), key=static_file[15:], files_to_commit=files_to_commit, file_path='static')

    ####################################################
    #Create static files from the source_files directory
    #   These are HTML files for built-in STARK modules like user management, permissions, sessions...
    #   Right now they need to be modified by the generator a bit just to replace the Project/System Name in the headers
    dir = "source_files"
    html_files = os.listdir(dir)
    for html_file in html_files:
        with open(dir + os.sep + html_file) as f:
            #replace all occurences of "[[STARK_PROJECT_NAME]]" with project_name
            source_code = f.read().replace("[[STARK_PROJECT_NAME]]", project_name)
            add_to_commit(source_code=source_code, key=html_file, files_to_commit=files_to_commit, file_path='static')

    ##################################################################
    #Get pre-built utilities, layers and helpers for local development
    prebuilt_utilities = []
    list_prebuilt_utilities(codegen_bucket_name, prebuilt_utilities)
    for static_file in prebuilt_utilities:
        #We don't want to include the "STARKUtilities/" prefix in our list of keys, hence the string slice in static_file
        add_to_commit(source_code=get_file_from_bucket(codegen_bucket_name, static_file), key=static_file[15:], files_to_commit=files_to_commit, file_path='bin')

    prebuilt_layers = []
    list_packaged_layers(codegen_bucket_name, prebuilt_layers)
    for static_file in prebuilt_layers:
        #We don't want to include the "STARKLambdaLayers/" prefix in our list of keys, hence the string slice in static_file
        add_to_commit(source_code=get_file_from_bucket(codegen_bucket_name, static_file), key=static_file[18:], files_to_commit=files_to_commit, file_path='lambda/packaged_layers')

    prebuilt_helpers = []
    list_prebuilt_helpers(codegen_bucket_name, prebuilt_helpers)
    for static_file in prebuilt_helpers:
        #We don't want to include the "STARKLambdaHelpers/" prefix in our list of keys, hence the string slice in static_file
        add_to_commit(source_code=get_file_from_bucket(codegen_bucket_name, static_file), key=static_file[19:], files_to_commit=files_to_commit, file_path='lambda/helpers')

    #######################################################################
    #Get our STARK_Config.yml from the CodeGen bucket - needed by STARK CLI
    response = s3.get_object(
        Bucket=codegen_bucket_name,
        Key=f'STARKConfiguration/STARK_config.yml'
    )
    source_code = response['Body'].read()
    add_to_commit(source_code=source_code, key=f"STARK_config.yml", files_to_commit=files_to_commit, file_path='bin/libstark')

    ####################################################################################################
    #Create the .gitignore file for the project repo - so that cruft doesn't get into commits by default
    add_to_commit(source_code=cg_git.create(), key=f".gitignore", files_to_commit=files_to_commit, file_path='')

    ##############################################
    #Commit our prebuilt files to the project repo
    #   There's a codecommit limit of 100 files - this will fail if more than 100 static files are needed,
    #   such as if a dozen or so entities are requested for code generation. Implement commit chunking here for safety.
    ctr                 = 0
    key                 = 0
    chunked_commit_list = {}
    for item in files_to_commit:
        if ctr == 100:
            key = key + 1
            ctr = 0
        ctr = ctr + 1
        if chunked_commit_list.get(key, '') == '':
            chunked_commit_list[key] = []
        chunked_commit_list[key].append(item)

    ctr         = 0
    batch_count = key + 1
    for commit_batch in chunked_commit_list:
        ctr = ctr + 1

        response = git.get_branch(
            repositoryName=repo_name,
            branchName='master'        
        )
        commit_id = response['branch']['commitId']

        response = git.create_commit(
            repositoryName=repo_name,
            branchName='master',
            parentCommitId=commit_id,
            authorName='STARK::CGStatic',
            email='STARK@fakedomainstark.com',
            commitMessage=f"Initial commit of static and prebuilt files (commit {ctr} of {batch_count})",
            putFiles=chunked_commit_list[commit_batch]
        )

    ##################################################
    # Optimization Attempt
    #   After we commit code to the repo, re-enable the Pipeline's source stage change detection 
    #   We need to get current working settings

    response = s3.get_object(
        Bucket=codegen_bucket_name,
        Key=f'STARK_cloud_resources/{project_varname}_pipeline.pickle'
    )
    pipeline_definition = pickle.loads(response['Body'].read()) 
    print(pipeline_definition)
    response = cdpl.update_pipeline(pipeline=pipeline_definition['pipeline'])
    cdpl.start_pipeline_execution(name=f"STARK_{project_varname}_pipeline")


@helper.delete
def no_op(_, __):
    pass


def lambda_handler(event, context):
    helper(event, context)


def add_to_commit(source_code, key, files_to_commit, file_path=''):

    if type(source_code) is str:
        source_code = source_code.encode()

    if file_path == '':
        full_path = key
    else:
        full_path = f"{file_path}/{key}"

    files_to_commit.append({
        'filePath': full_path,
        'fileContent': source_code
    })

def list_prebuilt_static_files(bucket_name, prebuilt_static_files):
    response = s3.list_objects_v2(
        Bucket = bucket_name,
        Prefix = "STARKWebSource/",
    )

    for static_file in response['Contents']:
        prebuilt_static_files.append(static_file['Key'])

def list_prebuilt_helpers(bucket_name, prebuilt_static_files):
    response = s3.list_objects_v2(
        Bucket = bucket_name,
        Prefix = "STARKLambdaHelpers/",
    )

    for static_file in response['Contents']:
        prebuilt_static_files.append(static_file['Key'])

def list_prebuilt_utilities(bucket_name, prebuilt_static_files):
    response = s3.list_objects_v2(
        Bucket = bucket_name,
        Prefix = "STARKUtilities/",
    )

    for static_file in response['Contents']:
        prebuilt_static_files.append(static_file['Key'])

def list_packaged_layers(bucket_name, prebuilt_static_files):
    response = s3.list_objects_v2(
        Bucket = bucket_name,
        Prefix = "STARKLambdaLayers/",
    )

    for static_file in response['Contents']:
        prebuilt_static_files.append(static_file['Key'])

def get_file_from_bucket(bucket_name, static_file):
    response = s3.get_object(
        Bucket = bucket_name,
        Key = static_file
    )

    source_code = response['Body'].read()
    return source_code
