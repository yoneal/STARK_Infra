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
        escaped_destination = stark_func.replace(" ", "_")
        
        #Check if there is a dependency specified
        if "Dependencies" in func_def:
            print (f"Depends on: {{func_def['Dependencies']}}")

            for dependency in func_def['Dependencies']:
                #Copy entire Lambda module code (folder)    
                escaped_dependency =  dependency.replace(" ", "_")
                print(escaped_destination)
                print(escaped_dependency)
                os.system(f"cp -R lambda_src/{{escaped_dependency}} lambda/{{escaped_destination}}")
    """
    return textwrap.dedent(source_code)


