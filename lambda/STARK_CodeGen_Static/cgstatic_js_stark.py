#STARK Code Generator component.
#Produces the customized static content for a STARK system

#Python Standard Library
import textwrap

#Private modules
import convert_friendly_to_system as converter

def create(data):

    api_endpoint  = data['API Endpoint']
    entities        = data['Entities']

    #FIXME: BUG! region is hardcoded here. Use endpoint property to get entire endpoint url programmatically, instead of stitching API ID with rest of URL compenents
    #           This has been done already in STARK_ConfigWriter, follow pattern there. 
    #           Might have to fix in main.py, and pass full endpoint here instead of just the id.
    source_code = f"""\
        const STARK={{
            'login_url':'{api_endpoint}/login',
            'sys_modules_url':'{api_endpoint}/sys_modules',"""

    #Each entity is a big module, has own endpoint
    for entity in entities:
        entity_endpoint_name = converter.convert_to_system_name(entity)
        source_code += f"""
            '{entity_endpoint_name}_url':'{api_endpoint}/{entity_endpoint_name}',"""

    #STARK-provided common methods go here
    source_code += f"""
            'methods_with_body': ["POST", "DELETE", "PUT"],

            request: function(method, fetchURL, payload='') {{

                let fetchData = {{
                    mode: 'cors',
                    headers: {{ "Content-Type": "application/json" }},
                    method: method,
                }}

                if(this.methods_with_body.includes(method)) {{
                    console.log("stringifying payload")
                    console.log(payload)
                    fetchData['body'] = JSON.stringify(payload)
                }}

                return fetch(fetchUrl, fetchData).then( function(response) {{
                    if (!response.ok) {{
                        console.log(response)
                        throw Error(response.statusText);
                    }}
                    return response
                }}).then((response) => response.json())
            }}
        }};
    """

    return textwrap.dedent(source_code)
