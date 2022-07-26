#STARK Code Generator component.
#Produces the customized dynamic content for a STARK system

#Python Standard Library
import base64
import textwrap

def create():
    source_code = f"""\
    import os
    import sys

    import yaml
    print("Hello World! Starting YAML read...")
    STARK_folder = os.getcwd() + '/lambda/helpers'
    sys.path = [STARK_folder] + sys.path
    import convert_friendly_to_system as converter

    with open('cloud_resources.yml') as f:
        resources_raw = f.read()
        resources_yml = yaml.safe_load(resources_raw)


    for stark_func in resources_yml['Lambda']:
        func_def = resources_yml['Lambda'][stark_func]
        print (stark_func)
        print (func_def)
        destination_varname = converter.convert_to_system_name(stark_func)
        
        #Check if there is a dependency specified
        if "Dependencies" in func_def:
            print (f"Depends on: {{func_def['Dependencies']}}")

            for dependency in func_def['Dependencies']:
                #Copy entire Lambda module code (folder)    
                dependency_varname =  converter.convert_to_system_name(dependency)
                os.system(f"cp -R lambda_src/{{dependency_varname}} lambda/{{destination_varname}}")
    """
    return textwrap.dedent(source_code)


