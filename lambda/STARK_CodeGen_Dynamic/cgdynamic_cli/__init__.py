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

cg_analytics  = importlib.import_module(f"{prepend_dir}cgdynamic_analytics")
cg_etl_script = importlib.import_module(f"{prepend_dir}cgdynamic_etl_script")

cg_conftest = importlib.import_module(f"{prepend_dir}cgdynamic_conftest")
cg_test     = importlib.import_module(f"{prepend_dir}cgdynamic_test_cases")
cg_fixtures = importlib.import_module(f"{prepend_dir}cgdynamic_test_fixtures")

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

    s3_analytics_raw_bucket_name = converter.convert_to_system_name(project_varname + '-stark-analytics-raw', 's3')
    s3_analytics_processed_bucket_name = converter.convert_to_system_name(project_varname + '-stark-analytics-processed', 's3')
    s3_analytics_athena_bucket_name = converter.convert_to_system_name(project_varname + '-stark-analytics-athena', 's3')

    with open("../cloud_resources.yml", "r") as f:
        current_cloud_resources = yaml.safe_load(f.read())
        current_data_model =  current_cloud_resources['Data Model']

    current_entities = []
    for each_entity in current_data_model:
        current_entities.append(each_entity)

    ##########################################
    #Create code for our entity Lambdas (API endpoint backing)
    files_to_commit = []
    for entity in entities:
        entity_varname = converter.convert_to_system_name(entity)
        #Step 1: generate source code.
        #Step 1.1: extract relationship
        relationships = get_rel.get_relationship(models, entity, entity)
        rel_model = {}
        for relationship in relationships.get('has_many', []):
            if relationship.get('type') == 'repeater':
                rel_col = models.get(relationship.get('entity'), '')
                rel_model.update({(relationship.get('entity')) : rel_col})

        for index, items in relationships.items():
            if len(items) > 0:
                for key in items:
                    for value in key:
                        key[value] = converter.convert_to_system_name(key[value])
        data = {
            "Entity": entity_varname,
            "Columns": models[entity]["data"],
            "PK": models[entity]["pk"],
            "DynamoDB Name": ddb_table_name,
            "Bucket Name": web_bucket_name,
            "Relationships": relationships,
            "Rel Model": rel_model,
            "Raw Bucket Name": s3_analytics_raw_bucket_name,
            "Processed Bucket Name": s3_analytics_processed_bucket_name,
            "Project Name": project_varname
        }
        source_code            = cg_ddb.create(data)
        test_source_code       = cg_test.create(data)
        fixtures_source_code   = cg_fixtures.create(data)
        etl_script_source_code = cg_etl_script.create(data)

        #Step 2: Add source code to our commit list to the project repo
        files_to_commit.append({
            'filePath': f"lambda/{entity_varname}/__init__.py",
            'fileContent': source_code.encode()
        })

        # test cases
        files_to_commit.append({
            'filePath': f"lambda/test_cases/business_modules/test_{entity_varname.lower()}.py",
            'fileContent': test_source_code.encode()
        })

        # fixtures
        files_to_commit.append({
            'filePath': f"lambda/test_cases/fixtures/{entity_varname}/__init__.py",
            'fileContent': fixtures_source_code.encode()
        })

        # etl scripts
        files_to_commit.append({
            'filePath': f"lambda/STARK_Analytics/ETL_Scripts/{entity_varname}.py",
            'fileContent': etl_script_source_code.encode()
        })
    ########################################
    #Update conftest of test_cases 
    data = {
        "Entities": [*current_entities, *entities]
    }
    conftest_code = cg_conftest.create(data)

    files_to_commit.append({
        'filePath': f"lambda/test_cases/conftest.py",
        'fileContent': conftest_code.encode()
    })

    #########################################
    #Update entities in STARK_Analytics 
    analytics_source_code = cg_analytics.create(data)
    files_to_commit.append({
        'filePath': f"lambda/STARK_Analytics/__init__.py",
        'fileContent': analytics_source_code.encode()
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


