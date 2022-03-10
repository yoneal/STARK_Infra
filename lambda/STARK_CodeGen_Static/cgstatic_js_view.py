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
                list_status: {{"""

    #FIXME: These kinds of logic (determining col types, lists, retreiving settings, etc) are repetitive, should be refactored shipped to a central lib
    for col, col_type in cols.items():
        if isinstance(col_type, dict) and col_type["type"] == "relationship":
            has_one = col_type.get('has_one', '')
            if  has_one != '':
                #simple 1-1 relationship
                col_varname = converter.convert_to_system_name(col)

                source_code += f"""
                    '{col_varname}': 'empty',"""



    source_code += f"""
                }},
                visibility: 'hidden',
                next_token: '',
                next_disabled: true,
                prev_token: '',
                prev_disabled: true,
                page_token_map: {{1: ''}},
                curr_page: 1

            }},
            methods: {{

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

               list: function (lv_token='', btn='') {{
                    spinner.show()
                    payload = []
                    if (btn == 'next') {{
                        root.curr_page++;
                        console.log(root.curr_page);
                        payload['Next_Token'] = lv_token;

                        //When Next button is clicked, we should:
                        // - save Next Token to new page in page_token_map
                        // - hide Next button - it will be visible again if API call returns a new Next Token
                        // - if new_page is > 2, assign {{new_page - 1}} token to prev_token
                        root.prev_disabled = false;    
                        root.next_disabled = true;

                        root.page_token_map[root.curr_page] = lv_token;

                        if (root.curr_page > 1) {{
                            root.prev_token = root.page_token_map[root.curr_page - 1];
                        }}
                        console.log(root.page_token_map)
                        console.log(root.prev_token)
                    }}
                    else if (btn == "prev") {{
                        root.curr_page--;

                        if (root.prev_token != "") {{
                            payload['Next_Token'] = root.page_token_map[root.curr_page];
                        }}

                        if (root.curr_page > 1) {{
                            root.prev_disabled = false
                            root.prev_token = root.page_token_map[root.curr_page - 1]
                        }}
                        else {{
                            root.prev_disabled = true
                            root.prev_token = ""
                        }}
                    }}

                    {entity_app}.list(payload).then( function(data) {{
                        token = data['Next_Token'];
                        root.listview_table = data['Items'];
                        console.log("DONE! Retrieved list.");
                        spinner.hide()

                        if (token != "null") {{
                            root.next_disabled = false;
                            root.next_token = token;
                        }}
                        else {{
                            root.next_disabled = true;
                        }}

                    }})
                    .catch(function(error) {{
                        console.log("Encountered an error! [" + error + "]")
                        spinner.hide()
                    }});
                }},"""

    for col, col_type in cols.items():
        if isinstance(col_type, dict) and col_type["type"] == "relationship":
            has_one = col_type.get('has_one', '')
            if  has_one != '':
                #simple 1-1 relationship
                foreign_entity  = converter.convert_to_system_name(has_one)
                foreign_field   = converter.convert_to_system_name(col_type.get('value', foreign_entity))
                foreign_display = converter.convert_to_system_name(col_type.get('display', foreign_field))

                source_code += f"""
                list_{foreign_entity}: function () {{
                    if (this.list_status.{foreign_field} == 'empty') {{
                        loading_modal.show();

                        //FIXME: for now, generic list() is used. Can be optimized to use a list function that only retrieves specific columns
                        {foreign_entity}_app.list().then( function(data) {{
                            data.forEach(function(arrayItem) {{
                                value = arrayItem['{foreign_field}']
                                text  = arrayItem['{foreign_display}']
                                root.lists.{foreign_field}.push({{ value: value, text: text }})
                            }})
                            root.list_status.{foreign_field} = 'populated'
                            loading_modal.hide();
                        }}).catch(function(error) {{
                            console.log("Encountered an error! [" + error + "]")
                            loading_modal.hide();
                        }});
                    }}
                }},"""


    source_code += f"""
            }}
        }})
    """

    return textwrap.dedent(source_code)