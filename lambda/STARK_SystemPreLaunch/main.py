#This will handle all pre-launch tasks - final things to do after the entirety of the new system's infra and code have been deployed,
#   such as necessary system entries into the applicaiton's database (default user, permissions, list of modules, etc.)

#Python Standard Library
import datetime
import time
import os


#Extra modules
import boto3
from crhelper import CfnResource
import yaml

#Private modules
import convert_friendly_to_system as converter
import stark_scrypt as scrypt

ddb = boto3.client('dynamodb')
s3  = boto3.client('s3')

helper = CfnResource() #We're using the AWS-provided helper library to minimize the tedious boilerplate just to signal back to CloudFormation

@helper.create
@helper.update
def create_handler(event, context):
    project_name    = event.get('ResourceProperties', {}).get('Project','')    
    project_varname = converter.convert_to_system_name(project_name)
    ddb_table_name = event.get('ResourceProperties', {}).get('DDBTable','')

    #Cloud resources document
    codegen_bucket_name = os.environ['CODEGEN_BUCKET_NAME']
    response = s3.get_object(
        Bucket=codegen_bucket_name,
        Key=f'STARK_cloud_resources/{project_varname}.yaml'
    )
    cloud_resources = yaml.safe_load(response['Body'].read().decode('utf-8')) 


    models   = cloud_resources["Data Model"]
    entities = []
    for entity in models: entities.append(entity)    
    # print(entities)
    # print(entities[0])

    business_permissions = ''
    module_types = ['Add', 'Edit', 'Delete', 'View', 'Report']
    for entity in entities:
        for module_type in module_types:
            business_permissions = business_permissions + entity + '|' + module_type + ', '

    business_permissions = business_permissions[:-2]
    print(business_permissions)


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

    #Module Group
    with open('module_group.yml') as f:
            module_group_raw = f.read()
            module_group_yml = yaml.safe_load(module_group_raw)

    module_group_list = []
    for module_group in module_group_yml:
        module_grp                      = {}
        module_grp['pk']                = {'S' : module_group}
        module_grp['sk']                = {'S' : module_group_yml[module_group]["sk"]}
        module_grp['Description']       = {'S' : module_group_yml[module_group]["Description"]}
        module_grp['Icon']              = {'S' : module_group_yml[module_group]["Icon"]}
        module_grp['Priority']          = {'N' : module_group_yml[module_group]["Priority"]}
        module_grp['STARK-ListView-sk'] = {'S' : module_group}

        response = ddb.put_item(
            TableName=ddb_table_name,
            Item=module_grp,
        )
        print(response)

    # #System Modules
    # with open('system_modules.yml') as f:
    #         system_modules_raw = f.read()
    #         system_modules_yml = yaml.safe_load(system_modules_raw)

    # system_modules_list = []
    # for system_modules in system_modules_yml:
    #     sys_modules                      = {}
    #     sys_modules['pk']                = {'S' : system_modules}
    #     sys_modules['sk']                = {'S' : system_modules_yml[system_modules]["sk"]}
    #     sys_modules['Target']            = {'S' : system_modules_yml[system_modules]["Target"]}
    #     sys_modules['Descriptive_Title'] = {'S' : system_modules_yml[system_modules]["Descriptive_Title"]}
    #     sys_modules['Description']       = {'S' : system_modules_yml[system_modules]["Description"]}
    #     sys_modules['Module_Group']      = {'S' : system_modules_yml[system_modules]["Module_Group"]}
    #     sys_modules['Is_Menu_Item']      = {'S' : system_modules_yml[system_modules]["Is_Menu_Item"]}
    #     sys_modules['Is_Enabled']        = {'S' : system_modules_yml[system_modules]["Is_Enabled"]}
    #     sys_modules['Icon']              = {'S' : system_modules_yml[system_modules]["Icon"]}
    #     sys_modules['Image_Alt']         = {'S' : system_modules_yml[system_modules]["Image_Alt"]}
    #     sys_modules['Priority']          = {'S' : system_modules_yml[system_modules]["Priority"]}
    #     sys_modules['STARK-ListView-sk'] = {'S' : system_modules}

    #     response = ddb.put_item(
    #         TableName=ddb_table_name,
    #         Item=sys_modules,
    #     )
    #     print(response)

@helper.delete
def no_op(_, __):
    pass


def lambda_handler(event, context):
    helper(event, context)
