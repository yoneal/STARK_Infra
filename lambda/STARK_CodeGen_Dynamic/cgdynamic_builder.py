#STARK Code Generator component.
#Produces the customized dynamic content for a STARK system

#Python Standard Library
import base64
import textwrap

def create():
    source_code = f"""\
    import os

    import yaml
    print("Hello World! Starting YAML read...")

    with open('cloud_resources.yml') as f:
        resources_raw = f.read()
        resources_yml = yaml.safe_load(resources_raw)


    for stark_func in resources_yml['Lambda']:
        func_def = resources_yml['Lambda'][stark_func]
        print (stark_func)
        print (func_def)
        
        #Check if there is a dependency specified
        if "Dependencies" in func_def:
            print (f"Depends on: {{func_def['Dependencies']}}")

            for dependency in func_def['Dependencies']:
                #Copy entire Lambda module code (folder)
                os.system(f"cp -R lambda/{{dependency}} lambda/{{stark_func}}")
    """
return textwrap.dedent(source_code)


