#STARK Code Generator component.
#Produces the customized static content for a STARK system.

#Python Standard Library
import json
import os
import textwrap

#Extra modules
import yaml

#Private modules
import cgstatic_js_app as cg_js_app
import cgstatic_js_view as cg_js_view
import cgstatic_js_login as cg_js_login
import cgstatic_js_homepage as cg_js_home
import cgstatic_js_stark as cg_js_stark
import cgstatic_css_login as cg_css_login
import cgstatic_html_add  as cg_add
import cgstatic_html_edit as cg_edit
import cgstatic_html_view as cg_view
import cgstatic_html_login as cg_login
import cgstatic_html_delete as cg_delete
import cgstatic_html_listview as cg_listview
import cgstatic_html_homepage as cg_homepage
import convert_friendly_to_system as converter

def create(cloud_resources, current_cloud_resources, project_basedir):
    models = cloud_resources["Data Model"]
    entities = []
    for entity in models:
        entities.append(entity)

    project_name    = cloud_resources["Project Name"]
    project_varname = converter.convert_to_system_name(project_name)

    #FIXME: API G is now in our `cloud_resources`` file, update this code
    #The endpoint of our API Gateway is not saved anywhere
    #   except in the main STARK.js file, so the only thing we can do is
    #   edit that file directly and get the endpoint URL from there
    endpoint = ''
    with open("../static/js/STARK.js", "r") as f:
        for line in f:
            code = line.strip()
            if code[0:14] == "api_endpoint_1":
                data     = code.partition("=")
                endpoint = data[2].strip()[1:-1] #slicing is to remove the quotes around the endpoint string

    #Collect list of files to commit to project repository
    files_to_commit = []

    #For each entity, we'll create a set of HTML and JS Files
    for entity in models:
        pk   = models[entity]["pk"]
        cols = models[entity]["data"]
        cgstatic_data = { "Entity": entity, "PK": pk, "Columns": cols, "Project Name": project_name }
        entity_varname = converter.convert_to_system_name(entity)

        add_to_commit(source_code=cg_add.create(cgstatic_data), key=f"{entity_varname}_add.html", files_to_commit=files_to_commit, file_path='static')
        add_to_commit(source_code=cg_edit.create(cgstatic_data), key=f"{entity_varname}_edit.html", files_to_commit=files_to_commit, file_path='static')
        add_to_commit(source_code=cg_delete.create(cgstatic_data), key=f"{entity_varname}_delete.html", files_to_commit=files_to_commit, file_path='static')
        add_to_commit(source_code=cg_view.create(cgstatic_data), key=f"{entity_varname}_view.html", files_to_commit=files_to_commit, file_path='static')
        add_to_commit(source_code=cg_listview.create(cgstatic_data), key=f"{entity_varname}.html", files_to_commit=files_to_commit, file_path='static')
        add_to_commit(source_code=cg_js_app.create(cgstatic_data), key=f"js/{entity_varname}_app.js", files_to_commit=files_to_commit, file_path='static')
        add_to_commit(source_code=cg_js_view.create(cgstatic_data), key=f"js/{entity_varname}_view.js", files_to_commit=files_to_commit, file_path='static')


    #STARK main JS file - modify to add new models.
    #   Requires a list of the old models from existing cloud_resources
    combined_models = current_cloud_resources["Data Model"].copy()
    combined_models.update(models)

    data = { 'API Endpoint': endpoint, 'Entities': combined_models }
    add_to_commit(cg_js_stark.create(data), key=f"js/STARK.js", files_to_commit=files_to_commit, file_path='static')

    ##################################################
    #Write files
    for code in files_to_commit:
        filename = project_basedir + code['filePath']
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "wb") as f:
            f.write(code['fileContent'])


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
