#STARK Code Generator component.
#Produces the customized static content for a STARK system

#Python Standard Library
import textwrap

#Private modules
import cgstatic_controls_coltype as cg_coltype
import convert_friendly_to_system as converter

def create(data):

    entity = data["Entity"]
    cols   = data["Columns"]
    pk     = data['PK']

    entity_varname = converter.convert_to_system_name(entity)
    entity_app     = entity_varname + '_app'
    pk_varname     = converter.convert_to_system_name(pk)

    source_code = f"""\
        var root = new Vue({{
            el: "#vue-root",
            data: {{
                listview_table: '',
                {entity_varname}: {{
                    '{pk_varname}': '',
                    'sk': '',"""

    for col in cols:
        col_varname = converter.convert_to_system_name(col)
        source_code += f"""
                    '{col_varname}': '',""" 

    source_code += f"""
                }},
                lists: {{"""

    for col, col_type in cols.items():
        col_varname = converter.convert_to_system_name(col)
        js_list_code = cg_coltype.create_list({
            "col": col,
            "col_type": col_type,
            "col_varname": col_varname
        })

        if js_list_code != None:
            source_code += f"""
                    {js_list_code}"""

    source_code += f"""
                }},
                visibility: 'hidden',
            }},
            methods:{{

                show: function () {{
                    this.visibility = 'visible';
                }},

                hide: function () {{
                    this.visibility = 'hidden';
                }},

                add: function () {{
                    loading_modal.show()
                    console.log("VIEW: Inserting!")

                    let data = {{ {entity_varname}: this.{entity_varname} }}

                    {entity_app}.add(data).then( function(data) {{
                        console.log("VIEW: INSERTING DONE!");
                        loading_modal.hide()
                        window.location.href = "{entity_varname}.html";
                    }}).catch(function(error) {{
                        console.log("Encountered an error! [" + error + "]")
                        loading_modal.hide()
                    }});
                }},

                delete: function () {{
                    loading_modal.show()
                    console.log("VIEW: Deleting!")

                    let data = {{ {entity_varname}: this.{entity_varname} }}

                    {entity_app}.delete(data).then( function(data) {{
                        console.log("VIEW: DELETE DONE!");
                        console.log(data);
                        loading_modal.hide()
                        window.location.href = "{entity_varname}.html";
                    }})
                    .catch(function(error) {{
                        console.log("Encountered an error! [" + error + "]")
                        loading_modal.hide()
                    }});
                }},

                update: function () {{
                    loading_modal.show()
                    console.log("VIEW: Updating!")

                    let data = {{ {entity_varname}: this.{entity_varname} }}

                    {entity_app}.update(data).then( function(data) {{
                        console.log("VIEW: UPDATING DONE!");
                        console.log(data);
                        loading_modal.hide()
                        window.location.href = "{entity_varname}.html";
                    }})
                    .catch(function(error) {{
                        console.log("Encountered an error! [" + error + "]")
                        loading_modal.hide()
                    }});
                }},

                get: function () {{
                    const queryString = window.location.search;
                    const urlParams = new URLSearchParams(queryString);
                    //Get whatever params are needed here (pk, sk, filters...)
                    data = {{}}
                    data['{pk_varname}'] = urlParams.get('{pk_varname}');

                    if(data['{pk_varname}'] == null) {{
                        root.show();
                    }}
                    else {{
                        loading_modal.show();
                        console.log("VIEW: Getting!")

                        {entity_app}.get(data).then( function(data) {{
                            root.{entity_varname} = data[0]; //We need 0, because API backed func always returns a list for now
                            root.{entity_varname}.orig_{pk_varname} = root.{entity_varname}.{pk_varname};
                            console.log("VIEW: Retreived module data.")
                            root.show()
                            loading_modal.hide()
                        }})
                        .catch(function(error) {{
                            console.log("Encountered an error! [" + error + "]")
                            loading_modal.hide()
                        }});
                    }}
                }},

                list: function () {{
                    spinner.show()
                    customer_app.list().then( function(data) {{
                        root.listview_table = data;
                        console.log("DONE! Retreived list.");
                        spinner.hide()
                    }})
                    .catch(function(error) {{
                        console.log("Encountered an error! [" + error + "]")
                        spinner.hide()
                    }});
                }},
            }}
        }})

    """

    return textwrap.dedent(source_code)