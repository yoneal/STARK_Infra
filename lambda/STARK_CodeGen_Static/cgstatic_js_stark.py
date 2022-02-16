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
        api_endpoint_1 = '{api_endpoint}'

        const STARK={{
            'login_url':`${{api_endpoint_1}}/login`,
            'logout_url':`${{api_endpoint_1}}/logout`,
            'sys_modules_url':`${{api_endpoint_1}}/sys_modules`,"""

    #Each entity is a big module, has own endpoint
    for entity in entities:
        entity_endpoint_name = converter.convert_to_system_name(entity)
        source_code += f"""
            '{entity_endpoint_name}_url':`${{api_endpoint_1}}/{entity_endpoint_name}`,"""

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

                    //Specific indicators to watch for:
                    //401 (Unauthorized)= AWS API Gateway Authorizer error, missing Identity Source in request. Redirect to login screen
                    //403 (Forbidden) = Identity Source (cookie) was submitted, but Authorizer determined it was invalid. Redirect to home page
                    if (response.status == 401) {{
                        console.log("Unauthenticated request, redirecting to Login Screen")
                        window.location.href="index.html"
                    }}
                    if (response.status == 403) {{
                        console.log("Forbidden request, redirecting to Home Page")
                        window.location.href="home.html"
                        //FIXME: Redirecting to home for 403 errors could cause problems during cookie expiration (default: 12hrs.
                        //  Might be best to just immediately call logout to clear problematic session id and redirect to login?
                        //      See if this is a real problem first, though. Currently our Authorizer really only cares about being logged in,
                        //      and does not really do granular permissions checking (and having cached response could complicate having granular,
                        //      per-module permissions checking there, unless these granular items also get added to Identity Sources so they are all cached
                        //      independently.)
                        //  If browser clears local cookies earlier than DDB TTL execution, then this won't be a problem at all, as 401 will be triggered instead of
                        //  403. Browser clearing local cookie faster than DDB TTL execution is practically guaranteed, as TTL execution is not guaranteed real time.
                    }}

                        throw Error(response.statusText);
                    }}
                    return response
                }}).then((response) => response.json())
            }},

            logout: function () {{
                var sys_exit = confirm("Log out?");
                
                if(sys_exit) {{
                    console.log("Log out command!")
                    loading_modal.show()
                    fetchUrl = STARK.logout_url
                    payload={{}}
                    STARK.request('POST', fetchUrl, payload).then( function(data) {{
                            loading_modal.hide()
                            console.log("Server-side log out successful!");
                            window.location.href = "index.html";
                    }})
                    .catch(function(error) {{
                        console.log("Encountered an error! [" + error + "]")
                        loading_modal.hide()
                    }});
                }}
            }}
        }};
    """

    return textwrap.dedent(source_code)
