#STARK Code Generator component.
#Produces the customized dynamic content for a STARK system (Lambda / serverless resources)

#Python Standard Library
import json
import os
import textwrap
import importlib
from random import randint

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
                
            icon = 'images/' + suggest_graphic(entity)

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


#FIXME: suggest_graphic should become a layer, as it is now in 2 places (prelaunch and here)
def suggest_graphic(entity_name):
    #FIXME: When STARK data modeling syntax is finalized, it should include a way for
    #   devs to include a type hint for the entity (e.g., "people") to guide the parser
    #   towards choosing a more appropriate default graphic.
    #   Should also include a way to directly specify the desired image name (e.g. "user.png")

    extension = "svg"

    default_icon_map = {
        "award": [f"award.{extension}"],
        "archive": [f"archive.{extension}"],
        "book": [f"book.{extension}"],
        "commerce": [f"bag.{extension}", f"bag-heart.{extension}", f"cart.{extension}", f"cart-check.{extension}"],
        "config": [f"gear.{extension}", f"sliders.{extension}", f"sliders2.{extension}", f"sliders2-vertical.{extension}"],
        "data": [f"pie-chart.{extension}"],
        "document": [f"file-earmark-text.{extension}", f"folder.{extension}", f"folder-fill.{extension}", f"folder2.{extension}"],
        "event": [f"calendar.{extension}",f"calendar-day.{extension}",f"calendar-date.{extension}",f"calendar-event.{extension}",f"calendar2.{extension}",f"calendar2-day.{extension}",f"calendar2-date.{extension}",f"calendar2-event.{extension}" ],
        "item": [f"box.{extension}",f"box-seam.{extension}",f"box2.{extension}"],
        "location": [f"map.{extension}", f"geo-alt-fill.{extension}", f"geo-alt.{extension}"],
        "logistics": [f"truck.{extension}"],
        "person": [f"person.{extension}", f"people.{extension}"],
        "sales": [f"currency-dollar.{extension}", f"credit-card.{extension}", f"credit-card-2-front.{extension}"],
        "tasks": [f"clipboard.{extension}"],
        "travel": [f"briefcase.{extension}"],
        "type": [f"tag.{extension}", f"tags.{extension}"],
    }

    abstract_icons = [ f"square.{extension}", f"triangle.{extension}", f"circle.{extension}", f"hexagon.{extension}", f"star.{extension}"]

    #The order of these types matter. Types that come first take precedence.
    entity_type_map = {
        "type": ["type", "category", "categories", "tag", "price"],
        "tasks": ["task", "to do", "todo", "to-do", "list"],
        "data": ["data", "report"],
        "award": ["award", "prize"],
        "archive": ["archive", "storage", "warehouse"],
        "book": ["book"],
        "commerce": ["order", "shop"],
        "config": ["config", "configuration", "settings", "option"],
        "document": ["document", "file", "form",],
        "event": ["event", "meeting", "date", "call", "conference"],
        "item": ["item", "package", "inventory"],
        "location": ["address", "place", "location", "country", "countries", "city", "cities", "branch", "office"],
        "logistics": ["delivery", "deliveries", "vehicle", "fleet", "shipment"],
        "person": ["customer", "agent", "employee", "student", "teacher", "person", "people", "human"],
        "sales": ["sale", "sale", "purchase", "money", "finance"],
        "travel": ["travel"],
    }

    suggested_type = ''
    entity_name = entity_name.lower()
    for type in entity_type_map:
        #First, try a naive match
        if entity_name in entity_type_map[type]:
            suggested_type = type

        #If no match, see if we can match by attempting to turn name to singular
        if suggested_type == '':
            if entity_name[-1] == "s":
                singular_name = entity_name[0:-1]
                if singular_name in entity_type_map[type]:
                    suggested_type = type

        #If no match, see if we can substr the type map entries into entity name
        if suggested_type == '':
            for keyword in entity_type_map[type]:
                if keyword in entity_name:
                    suggested_type = type


    #If still no match, abstract icons will be assigned to this entity
    if suggested_type == '':
        suggested_type = 'abstract'

    print(suggested_type)
    if suggested_type == 'abstract':
        limit = len(abstract_icons) - 1
        suggested_icon = abstract_icons[randint(0, limit)]
    else:
        limit = len(default_icon_map[suggested_type]) - 1
        suggested_icon = default_icon_map[suggested_type][randint(0, limit)]

    return suggested_icon
