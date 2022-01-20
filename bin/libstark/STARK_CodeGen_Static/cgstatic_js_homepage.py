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
                    fetchUrl = STARK.sys_modules_url
                    STARK.request('GET', fetchUrl)
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