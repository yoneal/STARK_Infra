#STARK Code Generator component.
#Produces the customized static content for a STARK system

#Python Standard Library
import textwrap

def create(data):

    source_code = f"""\
        var root = new Vue({{
            el: "#vue-root",
            data: {{
                group_collapse_name: 'group-collapse-1',
                modules: ''
            }},
            methods:{{
                get_module_list: function () {{
                    fetchUrl = STARK.STARK_Module_url + '?rt=usermodules'
                    STARK.request('GET', fetchUrl)
                    .then( function(data) {{

                        console.log(typeof(data))
                        const grouped_modules = []

                        grouping = []
                        grouping_ctr = 0
                        for (const key in data) {{
                            console.log(data[key]['group'])
                            group = data[key]['group']
                            if ( group in grouping ) {{
                                //Skip
                            }}
                            else {{
                                grouping[group] = grouping_ctr
                                grouped_modules[grouping_ctr] = {{
                                    "group_name": group,
                                    "modules": []
                                }}
                                grouping_ctr++
                            }}

                            grouped_modules[grouping[group]]["modules"].push(data[key])
                        }}

                        console.log(grouped_modules)
                        console.log(data)
                        console.log(typeof(data))
                        console.log(typeof(grouped_modules))
                        root.modules = grouped_modules;
                        console.log("DONE! Retrieved list of modules.")
                        spinner.hide();
                    }})
                    .catch(function(error) {{
                        console.log("Encountered an error! [" + error + "]");
                    }});
                }}
            }}
        }})

        root.get_module_list();
    """
    return textwrap.dedent(source_code)