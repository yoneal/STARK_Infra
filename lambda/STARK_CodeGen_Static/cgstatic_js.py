#STARK Code Generator component.
#Produces the customized static content for a STARK system

#Python Standard Library
import textwrap

#Private modules
import cgstatic_controls_coltype as cg_coltype

def create(data):

    entity = data["Entity"]
    cols   = data["Columns"]
    pk     = data['PK']

    entity_varname = entity.replace(" ", "_").lower()
    pk_varname     = pk.replace(" ", "_").lower()

    source_code = f"""\
        var root = new Vue({{
            el: "#vue-root",
            data: {{
                listview_table: '',
                {entity_varname}: {{
                    '{pk_varname}': '',
                    'sk': '',"""


    for col in cols:
        col_varname = col.replace(" ", "_").lower()
        source_code += f"""
                    '{col_varname}': '',""" 
    source_code = source_code[:-1] #remove last comma

    source_code += f"""
                }},
                lists: {{"""

    for col, col_type in cols.items():
        col_varname = col.replace(" ", "_").lower()
        js_list_code = cg_coltype.create_list({
            "col": col,
            "col_type": col_type,
            "col_varname": col_varname
        })

        if js_list_code != None:
            source_code += f"""
                    {js_list_code}"""

    source_code = source_code[:-1] #remove last comma

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
                    console.log("Inserting!")

                    let data = {{
                        {entity_varname}: this.{entity_varname}
                    }}

                    let fetchData = {{
                        mode: 'cors',
                        body: JSON.stringify(data),
                        headers: {{ "Content-Type": "application/json" }},
                        method: "POST",
                    }}

                    fetchUrl = STARK.{entity_varname}_url
                    fetch(fetchUrl, fetchData)
                    .then( function(response) {{
                        //FIX-ME:
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
                        console.log("INSERTING DONE!");
                        console.log(data);
                        window.location.href = "{entity_varname}.html";
                    }})
                    .catch(function(error) {{
                        console.log("Encountered an error! [" + error + "]")
                    }});
                    loading_modal.hide()
                }},

                delete: function () {{
                    loading_modal.show()
                    console.log("Deleting!")

                    let data = {{
                        {entity_varname}: {{ "{pk_varname}": this.{entity_varname}.{pk_varname} }}
                    }}

                    let fetchData = {{
                        mode: 'cors',
                        body: JSON.stringify(data),
                        headers: {{ "Content-Type": "application/json" }},
                        method: "DELETE",
                    }}

                    fetchUrl = STARK.{entity_varname}_url
                    fetch(fetchUrl, fetchData)
                    .then( function(response) {{
                        //FIX-ME:
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
                        console.log("UPDATING DONE!");
                        console.log(data);
                        window.location.href = "{entity_varname}.html";
                    }})
                    .catch(function(error) {{
                        console.log("Encountered an error! [" + error + "]")
                    }});
                    loading_modal.hide()
                }},

                update: function () {{
                    loading_modal.show()
                    console.log("Updating!")

                    let data = {{
                        {entity_varname}: this.{entity_varname}
                    }}

                    let fetchData = {{
                        mode: 'cors',
                        body: JSON.stringify(data),
                        headers: {{ "Content-Type": "application/json" }},
                        method: "PUT",
                    }}

                    fetchUrl = STARK.{entity_varname}_url
                    fetch(fetchUrl, fetchData)
                    .then( function(response) {{
                        //FIX-ME:
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
                        console.log("UPDATING DONE!");
                        console.log(data);
                        window.location.href = "{entity_varname}.html";
                    }})
                    .catch(function(error) {{
                        console.log("Encountered an error! [" + error + "]")
                    }});
                    loading_modal.hide()
                }},

                get: function () {{
                    // This function and relevant parameters should be decoupled from Vue!
                    const queryString = window.location.search;
                    const urlParams = new URLSearchParams(queryString);
                    const {pk_varname} = urlParams.get('{pk_varname}');

                    console.log({pk_varname});

                    if({pk_varname} == null) {{
                        root.show();
                    }}
                    else {{
                        loading_modal.show();
                        fetchUrl = STARK.{entity_varname}_url + '?rt=detail&{pk_varname}=' + {pk_varname}

                        let fetchData = {{
                            mode: 'cors',
                            headers: {{ "Content-Type": "application/json" }},
                            method: "GET",
                        }}

                        fetch(fetchUrl, fetchData)
                        .then( function(response) {{
                            //FIX-ME:
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
                            root.{entity_varname} = data[0]; //We need 0, because the Lambda func always returns a list for now
                            root.{entity_varname}.orig_{pk_varname} = root.{entity_varname}.{pk_varname};
                            console.log("DONE! Retreived module data.")
                            root.show()
                            loading_modal.hide()
                        }})
                        .catch(function(error) {{
                            console.log("Encountered an error! [" + error + "]")
                        }});
                    }}

                    loading_modal.hide();
                }},

                list: function () {{
                    spinner.show()

                    // This function and relevant parameters should be decoupled from Vue!
                    let fetchData = {{
                        mode: 'cors',
                        headers: {{ "Content-Type": "application/json" }},
                        method: "GET",
                    }}

                    fetchUrl = STARK.{entity_varname}_url + '?rt=all'
                    fetch(fetchUrl, fetchData)
                    .then( function(response) {{
                        //FIX-ME:
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
                        root.listview_table = data;
                        console.log("DONE! Retreived list.");
                        spinner.hide()
                    }})
                    .catch(function(error) {{
                        console.log("Encountered an error! [" + error + "]")
                    }});
                }}
            }}
        }})

    """

    return textwrap.dedent(source_code)