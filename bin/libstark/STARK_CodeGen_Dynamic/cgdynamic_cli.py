#STARK Code Generator component.
#Produces the customized dynamic content for a STARK system (Lambda / serverless resources)

#Python Standard Library
import json
import os
import textwrap

#Extra modules
import yaml

#Private modules
import cgdynamic_login as cg_login
import cgdynamic_logout as cg_logout
import cgdynamic_modules as cg_mod
import cgdynamic_dynamodb as cg_ddb
import cgdynamic_buildspec as cg_build
import cgdynamic_sam_template as cg_sam
import cgdynamic_template_conf as cg_conf
import convert_friendly_to_system as converter

def create(cloud_resources, project_basedir):

    models = cloud_resources["Data Model"]
    entities = []
    for entity in models:
        entities.append(entity)

    project_name    = cloud_resources["Project Name"]
    project_varname = converter.convert_to_system_name(project_name)
    ddb_table_name  = cloud_resources["DynamoDB"]["Table Name"]

    ##########################################
    #Create code for our entity Lambdas (API endpoint backing)
    files_to_commit = []
    for entity in entities:
        entity_varname = converter.convert_to_system_name(entity)
        #Step 1: generate source code.
        data = {
            "Entity": entity_varname,
            "Columns": models[entity]["data"],
            "PK": models[entity]["pk"],
            "DynamoDB Name": ddb_table_name
        }
        source_code = cg_ddb.create(data)

        #Step 2: Add source code to our commit list to the project repo
        files_to_commit.append({
            'filePath': f"lambda/{entity_varname}/main.py",
            'fileContent': source_code.encode()
        })


    ####################################################
    #Update the /sys_modules modules.yml file
    #   This is essentially the directory of system modules
    #First, get existing yml file, turn to dict
    with open("../lambda/sys_modules/modules.yml", "r") as f:
        modules_yml = yaml.safe_load(f.read())
    #Now, just update with our new modules, conveniently overwriting
    #   any that already exist (they could have been re-defined)
    for entity in entities:
        entity_varname = converter.convert_to_system_name(entity)
        graphic = cg_mod.suggest_graphic(entity)
        modules_yml[entity] = {
            "image": f"images/{graphic}",
            "image_alt": f"{entity} graphic",
            "href": f"{entity_varname}.html",
        }

    files_to_commit.append({
        'filePath': f"lambda/sys_modules/modules.yml",
        'fileContent': yaml.dump(modules_yml, encoding='utf-8', sort_keys=False)
    })

    ##################################################
    #Write files
    for code in files_to_commit:
        filename = project_basedir + code['filePath']
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "wb") as f:
            f.write(code['fileContent'])

def create_template_from_cloud_resources(data):
    cf_template = cg_sam.create(data, cli_mode=True)
    return cf_template
