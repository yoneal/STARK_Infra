#This will handle all pre-launch tasks - final things to do after the entirety of the new system's infra and code have been deployed,
#   such as necessary system entries into the applicaiton's database (default user, permissions, list of modules, etc.)

#Python Standard Library
import datetime
import time

#Extra modules
import boto3
from crhelper import CfnResource

#Private modules
import convert_friendly_to_system as converter
import stark_scrypt as scrypt

ddb = boto3.client('dynamodb')

helper = CfnResource() #We're using the AWS-provided helper library to minimize the tedious boilerplate just to signal back to CloudFormation

@helper.create
@helper.update
def create_handler(event, context):
    project_name    = event.get('ResourceProperties', {}).get('Project','')    
    project_varname = converter.convert_to_system_name(project_name)
    ddb_table_name = event.get('ResourceProperties', {}).get('DDBTable','')

    #################################
    #Create default user and password
    user = "root"    
    
    #FIXME: Default password is static right now, but in prod, this should be random each time and then saved to dev's local machine 
    #           (i.e., where he triggered the Stark CLI for the system generation request)
    password = "welcome-2-STARK!"
    hashed   = scrypt.create_hash(password)

    item                  = {}
    item['pk']            = {'S' : user}
    item['sk']            = {'S' : "STARK|user|info"}
    item['Role']          = {'S' : "Super Admin"}
    item['Full_Name']     = {'S' : "The Amazing Mr. Root"}
    item['Nickname']      = {'S' : "Root"}
    item['Password_Hash'] = {'S' : hashed}
    item['Last_Access']   = {'S' : str(datetime.datetime.now())}
    item['Permissions']   = {'S' : ""}
   
    #This special attribute is to make this record show up in the GSI "STARK-ListView-Index",
    #   which is what the User List View module will need to query, and also serves as the main sort field for the List View
    item['STARK-ListView-sk'] = {'S' : user}

    response = ddb.put_item(
        TableName=ddb_table_name,
        Item=item,
    )
    print(response)


@helper.delete
def no_op(_, __):
    pass


def lambda_handler(event, context):
    helper(event, context)
