#STARK Code Generator component.
#Produces the customized static content for a STARK system

#Python Standard Library
import textwrap

#Private modules
import convert_friendly_to_system as converter

def create(data):

    api_gateway_id  = data['API Gateway ID']
    entities        = data['Entities']

    source_code = f"""\
        const STARK={{
            'sys_modules_url':'https://{api_gateway_id}.execute-api.ap-southeast-1.amazonaws.com/sys_modules',"""

    #Each entity is a big module, has own endpoint
    for entity in entities:
        entity_endpoint_name = converter.convert_friendly_to_system(entity)
        source_code += f"""
            '{entity_endpoint_name}_url':'https://{api_gateway_id}.execute-api.ap-southeast-1.amazonaws.com/{entity_endpoint_name}',"""

    #Close the settings data structure
    source_code += f"""
        }};
    """

    return textwrap.dedent(source_code)