#STARK Code Generator component.
#Produces the customized static content for a STARK system

#Python Standard Library
import textwrap

#Private modules
import convert_friendly_to_system as converter

def create(data):

    api_endpoint = data['API Endpoint']
    entities     = data['Entities']

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
                    credentials: 'include'
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
            }},

            logout: function () {{
                console.log("Log out command!")
                /*
                fetchUrl = STARK.login_url
                payload=''
                return STARK.request('POST', fetchUrl, payload)
                
                //Redirect back to login screen
                */
            }}

        }};
    """

    return textwrap.dedent(source_code)
