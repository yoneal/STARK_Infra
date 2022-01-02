#This will handle all pre-launch tasks - final things to do after the entirety of the new system's infra and code have been deployed,
#   such as necessary system entries into the applicaiton's database (default user, permissions, list of modules, etc.)

#Python Standard Library
import base64
import json
import os
import textwrap

#Extra modules
import yaml
import boto3
import botocore
from crhelper import CfnResource

#Private modules
import convert_friendly_to_system as converter

s3   = boto3.client('s3')
lmb  = boto3.client('lambda')
git  = boto3.client('codecommit')

helper = CfnResource() #We're using the AWS-provided helper library to minimize the tedious boilerplate just to signal back to CloudFormation

@helper.create
@helper.update
def create_handler(event, context):
    project_name    = event.get('ResourceProperties', {}).get('Project','')    
    project_varname = converter.convert_to_system_name(project_name)

    #DynamoDB table name from our CF template
    ddb_table_name = event.get('ResourceProperties', {}).get('DDBTable','')

    #Stub actions, just to check that this works as expected
    print(f"Stub works: {project_name} - {project_varname} - {ddb_table_name}")

@helper.delete
def no_op(_, __):
    pass


def lambda_handler(event, context):
    helper(event, context)