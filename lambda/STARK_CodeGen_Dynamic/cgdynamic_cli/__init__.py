#STARK Code Generator component.
#Produces the customized dynamic content for a STARK system (Lambda / serverless resources)

#Python Standard Library
import json
import os
import textwrap
import importlib

#Extra modules
import yaml

#Private modules
prepend_dir = ""
if 'libstark' in os.listdir():
    prepend_dir = "libstark.STARK_CodeGen_Dynamic."

cg_ddb     = importlib.import_module(f"{prepend_dir}cgdynamic_dynamodb")
cg_sam     = importlib.import_module(f"{prepend_dir}cgdynamic_sam_template")

import convert_friendly_to_system as converter
import get_relationship as get_rel
import suggest_graphic as set_graphic

def create(cloud_resources, project_basedir):

    models = cloud_resources["Data Model"]
    entities = []
    for entity in models:
        entities.append(entity)

    project_name    = cloud_resources["Project Name"]
    project_varname = converter.convert_to_system_name(project_name)
    ddb_table_name  = cloud_resources["DynamoDB"]["Table Name"]
    web_bucket_name = cloud_resources["S3 webserve"]["Bucket Name"]

    ##########################################
    #Create code for our entity Lambdas (API endpoint backing)
    files_to_commit = []
    for entity in entities:
        entity_varname = converter.convert_to_system_name(entity)
        #Step 1: generate source code.
        #Step 1.1: extract relationship
        relationships = get_rel.get_relationship(models, entity)
        data = {
            "Entity": entity_varname,
            "Columns": models[entity]["data"],
            "PK": models[entity]["pk"],
            "DynamoDB Name": ddb_table_name,
            "Bucket Name": web_bucket_name,
            "Relationships": relationships
        }
        source_code = cg_ddb.create(data)

        #Step 2: Add source code to our commit list to the project repo
        files_to_commit.append({
            'filePath': f"lambda/{entity_varname}/main.py",
            'fileContent': source_code.encode()
        })


    ##################################################
    #Write files
    for code in files_to_commit:
        filename = project_basedir + code['filePath']
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "wb") as f:
            f.write(code['fileContent'])


    #####################################################
    #Create the STARK_Module entries for the new entities
    new_STARK_Module_entries = []
    module_types = ['Add', 'Edit', 'Delete', 'View', 'Report']
    for entity in entities:
        for module_type in module_types:
            pk = entity + '|' + module_type 
            entity_varname = converter.convert_to_system_name(entity)
            if module_type == 'View':
                target = entity_varname + '.html'
                title = entity
                is_menu_item = True
            else:
                target = entity_varname + '_' + module_type + '.html'
                title = module_type + ' ' + entity
                is_menu_item = False
                
            icon = 'images/' + set_graphic.suggest_graphic(entity)

            item                      = {}
            item['pk']                = {'S' : pk}
            item['sk']                = {'S' : "STARK|module"}
            item['Target']            = {'S' : target}
            item['Descriptive_Title'] = {'S' : title}
            item['Description']       = {'S' : ""}
            item['Module_Group']      = {'S' : "Default"}
            item['Is_Menu_Item']      = {'BOOL' : is_menu_item}
            item['Is_Enabled']        = {'BOOL' : True}
            item['Icon']              = {'S' : icon}
            item['Image_Alt']         = {'S' : ""}
            item['Priority']          = {'N' : "0"}
            item['STARK-ListView-sk'] = {'S' : pk}

            new_STARK_Module_entries.append({"PutRequest": {"Item": item}})

    with open("STARK_modules_data.json","wb") as f:
        f.write(('{"' + ddb_table_name + '": ' + json.dumps(new_STARK_Module_entries) + '}').encode())

    #FIXME:This should be a separate, independently-triggerable command in STARK CLI
    os.system("aws dynamodb batch-write-item --request-items file://STARK_modules_data.json")


def create_template_from_cloud_resources(data):
    cf_template = cg_sam.create(data, cli_mode=True)
    return cf_template


