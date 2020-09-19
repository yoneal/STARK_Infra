#STARK Code Generator component.
#Produces the customized static content for a STARK system

#Python Standard Library
import textwrap

def create(data):

    source_code = f"""\
        var root = new Vue({{
            el: "#vue-root",
            data: {{
                modules: ''
            }},
            methods:{{
                get_module_list: function () {{

                    // This function and relevant parameters should be decoupled from Vue!
                    let fetchData = {{
                        mode: 'cors',
                        headers: {{ "Content-Type": "application/json" }},
                        method: "GET",
                    }}

                    fetch(STARK.sys_modules_url, fetchData)
                    .then( function(response) {{
                        //FIXME:
                        //Error handling here should just be for network-related failiures
                        //Actual server errors should be handled properly by the API, giving back useful error messages and status codes.
                        if (!response.ok) {{
                            console.log(response)
                            throw Error(response.statusText);
                        }}
                        return response;
                    }})
                    .then((response) => response.json())
                    .then( function(data) {{
                        root.modules = data;
                        console.log("DONE! Retreived list of modules.")
                        spinner.hide();
                    }})
                    .catch(function(error) {{
                        root.form.provisioned_resources = "Encountered an error! [" + error + "]"
                    }});
                }}
            }}
        }})

        root.get_module_list();




    """
    return textwrap.dedent(source_code)