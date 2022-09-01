#STARK Code Generator component.
#Produces the customized static content for a STARK system

#Python Standard Library
import textwrap
import os
import importlib

#Private modules
prepend_dir = ""
if 'libstark' in os.listdir():
    prepend_dir = "libstark.STARK_CodeGen_Static."

cg_coltype = importlib.import_module(f"{prepend_dir}cgstatic_controls_coltype")  
import convert_friendly_to_system as converter

def create(data):

    entity = data["Entity"]
    cols   = data["Columns"]
    pk     = data['PK']

    entity_varname = converter.convert_to_system_name(entity)
    entity_app     = entity_varname + '_app'
    pk_varname     = converter.convert_to_system_name(pk)

    #file upload controls
    with_upload         = False
    ext_string          = ""
    allowed_size_string = ""
    upload_elems_string = ""

    source_code = f"""\
        var root = new Vue({{
            el: "#vue-root",
            data: {{
                metadata: {{
                    '{pk_varname}': {{
                        'value': '',
                        'required': true,
                        'max_length': '',
                        'data_type': '',
                        'state': null,
                        'feedback': ''
                    }},"""
    
    for col in cols:
        col_varname = converter.convert_to_system_name(col)
        source_code += f"""
                    '{col_varname}': {{
                        'value': '',
                        'required': true,
                        'max_length': '',
                        'data_type': '',
                        'state': null,
                        'feedback': ''
                    }},""" 
                    
    source_code += f"""
                }},
                
                auth_config: {{ }},

                auth_list: {{
                    'View': {{'permission': '{entity}|View', 'allowed': false}},
                    'Add': {{'permission': '{entity}|Add', 'allowed': false}},
                    'Delete': {{'permission': '{entity}|Delete', 'allowed': false}},
                    'Edit': {{'permission': '{entity}|Edit', 'allowed': false}},
                    'Report': {{'permission': '{entity}|Report', 'allowed': false}}
                }},

                listview_table: '',
                STARK_report_fields: [],
                {entity_varname}: {{
                    '{pk_varname}': '',
                    'sk': '',"""

    for col in cols:
        col_varname = converter.convert_to_system_name(col)
        source_code += f"""
                    '{col_varname}': '',""" 

    source_code += f"""
                    'STARK_uploaded_s3_keys':{{}}
                }},
                custom_report:{{
                    '{pk_varname}': {{"operator": "", "value": "", "type":"S"}},"""
    for col, col_type in cols.items():
        col_varname = converter.convert_to_system_name(col)
        col_type_id = set_type(col_type)
        source_code += f"""
                    '{col_varname}':  {{"operator": "", "value": "", "type":"{col_type_id}"}},""" 

    source_code += f"""
                    'STARK_isReport':true,
                    'STARK_report_fields':[]
                }},
                lists: {{
                    'Report_Operator': [
                        {{ value: '', text: '' }},
                        {{ value: '=', text: 'EQUAL TO (=)' }},
                        {{ value: '<>', text: 'NOT EQUAL TO (!=)' }},
                        {{ value: '<', text: 'LESS THAN (<)' }},
                        {{ value: '<=', text: 'LESS THAN OR EQUAL TO (<=)' }},
                        {{ value: '>', text: 'GREATER THAN (>)' }},
                        {{ value: '>=', text: 'GREATER THAN OR EQUAL TO (>=)' }},
                        {{ value: 'contains', text: 'CONTAINS (%..%)' }},
                        {{ value: 'begins_with', text: 'BEGINS WITH (..%)' }},
                        {{ value: 'IN', text: 'IN (value1, value2, value3, ... valueN)' }},
                        {{ value: 'between', text: 'BETWEEN (value1, value2)' }},
                    ],"""

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
            has_many = col_type.get('has_many', '')
            if  has_one != '' or has_many != '':
                #simple 1-1 relationship
                col_varname = converter.convert_to_system_name(col)

                source_code += f"""
                    '{col_varname}': 'empty',"""



    source_code += f"""
                }},
                multi_select_values: {{"""

    #FIXME: These kinds of logic (determining col types, lists, retreiving settings, etc) are repetitive, should be refactored shipped to a central lib
    for col, col_type in cols.items():
        if isinstance(col_type, dict):
            col_varname = converter.convert_to_system_name(col)
            col_values = col_type.get("values", "")
            if col_type["type"] == "relationship":
                has_many = col_type.get('has_many', '')
                if  has_many != '':
                    source_code += f"""
                        '{col_varname}': [],"""
            elif isinstance(col_values, list):
                    source_code += f"""
                        '{col_varname}': [],"""
                
    source_code += f"""

                }},
                visibility: 'hidden',
                next_token: '',
                next_disabled: true,
                prev_token: '',
                prev_disabled: true,
                page_token_map: {{1: ''}},
                curr_page: 1,
                showReport: false,
                object_url_prefix: "",
                temp_csv_link: "",
                temp_pdf_link: "",
                showError: false,
                no_operator: [],
                error_message: '',
                authFailure: false,
                authTry: false,
                all_selected: true,"""
    field_strings = f"['{pk_varname}',"
    for col in cols:
        col_varname = converter.convert_to_system_name(col)
        field_strings += f"""'{col_varname}',"""
    field_strings += f"""]"""
    source_code += f"""
                temp_checked_fields: {field_strings},
                checked_fields: {field_strings},"""
                
    search_string       = ""
    for col, col_type in cols.items():
        col_varname = converter.convert_to_system_name(col)
        if isinstance(col_type, dict):
            col_values = col_type.get("values", "")
            if col_type["type"] == "relationship" or isinstance(col_values, list):
                has_many = col_type.get('has_many', '')
                search_string += f"""
                    {col_varname}: '',"""
            if col_type["type"] == 'file-upload': 
                with_upload = True 
                ext_string += f"""
                         "{col_varname}": "{str(col_type.get("allowed_ext",""))}","""
                allowed_size = col_type.get("max_upload_size", "1 MB")
                temp_split = allowed_size.split()
                allowed_size_string += f"""
                         "{col_varname}": {int(temp_split[0])},"""
                upload_elems_string += f"""
                        "{col_varname}": {{"file": '', "progress_bar_val": 0}},"""
    if with_upload:
        source_code += f"""
                s3_access: "",
                STARK_upload_elements: {{{upload_elems_string}
                }},
                ext_whitelist: {{{ext_string}
                }},
                allowed_size: {{{allowed_size_string}
                }},
                ext_whitelist_table: "",
                allowed_size_table: 0,"""
    source_code += f"""
                search:{{{search_string}
                }},
            }},
            methods: {{

                show: function () {{
                    this.visibility = 'visible';
                }},

                hide: function () {{
                    this.visibility = 'hidden';
                }},

                add: function () {{
                    console.log("VIEW: Inserting!")"""
    for col, col_type in cols.items():
        col_varname = converter.convert_to_system_name(col)
        if isinstance(col_type, dict) and col_type["type"] == "relationship":
            has_many = col_type.get('has_many', '')
            if has_many != "":
                source_code += f"""
                    this.{entity_varname}.{col_varname} = (root.multi_select_values.{col_varname}.sort()).join(', ')"""
    
    source_code += f"""
                    response = STARK.validate_form(root.metadata, root.{entity_varname}""" 
    if with_upload:
        source_code += f", root.STARK_upload_elements"

    source_code += f""")
                    this.metadata = response['new_metadata']
                    if(response['is_valid_form']) {{
                        loading_modal.show()
                        let data = {{ {entity_varname}: this.{entity_varname} }}

                        {entity_app}.add(data).then( function(data) {{
                            loading_modal.hide()
                            if(data != "OK")
                            {{
                                for (var key in data) {{
                                    if (data.hasOwnProperty(key)) {{
                                        root.metadata[key]['state'] = false
                                        root.metadata[key]['feedback'] = data[key]
                                    }}
                                }}
                                return false
                            }}
                            console.log("VIEW: INSERTING DONE!");
                            STARK.local_storage_delete_key('Listviews', '{entity_varname}');
                            window.location.href = "{entity_varname}.html";
                        }}).catch(function(error) {{
                            console.log("Encountered an error! [" + error + "]")
                            alert("Request Failed: System error or you may not have enough privileges")
                            loading_modal.hide()
                        }});
                    }}
                }},

                delete: function () {{
                    loading_modal.show()
                    console.log("VIEW: Deleting!")

                    let data = {{ {entity_varname}: this.{entity_varname} }}

                    {entity_app}.delete(data).then( function(data) {{
                        console.log("VIEW: DELETE DONE!");
                        STARK.local_storage_delete_key('Listviews', '{entity_varname}');
                        console.log(data);
                        loading_modal.hide()
                        window.location.href = "{entity_varname}.html";
                    }})
                    .catch(function(error) {{
                        console.log("Encountered an error! [" + error + "]")
                        alert("Request Failed: System error or you may not have enough privileges")
                        loading_modal.hide()
                    }});
                }},

                update: function () {{
                    console.log("VIEW: Updating!")"""
    for col, col_type in cols.items():
        col_varname = converter.convert_to_system_name(col)
        if isinstance(col_type, dict) and col_type["type"] == "relationship":
            has_many = col_type.get('has_many', '')
            if has_many != "":
                source_code += f"""
                    this.{entity_varname}.{col_varname} = (root.multi_select_values.{col_varname}.sort()).join(', ')"""
    
    source_code += f"""
                    response = STARK.validate_form(root.metadata, root.{entity_varname}""" 
    if with_upload:
        source_code += f", root.STARK_upload_elements"

    source_code += f""")
                    this.metadata = response['new_metadata']
                    if(response['is_valid_form']) {{
                        loading_modal.show()
                        let data = {{ {entity_varname}: this.{entity_varname} }}

                        {entity_app}.update(data).then( function(data) {{
                            loading_modal.hide()
                            if(data != "OK")
                            {{
                                for (var key in data) {{
                                    if (data.hasOwnProperty(key)) {{
                                        root.metadata[key]['state'] = false
                                        root.metadata[key]['feedback'] = data[key]
                                    }}
                                }}
                                return false
                            }}
                            console.log("VIEW: UPDATING DONE!");
                            STARK.local_storage_delete_key('Listviews', '{entity_varname}');
                            window.location.href = "{entity_varname}.html";
                        }})
                        .catch(function(error) {{
                            console.log("Encountered an error! [" + error + "]")
                            alert("Request Failed: System error or you may not have enough privileges")
                            loading_modal.hide()
                        }});
                    }}
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
                            root.{entity_varname} = data["item"]; 
                            root.{entity_varname}.orig_{pk_varname} = root.{entity_varname}.{pk_varname};"""
    for col, col_type in cols.items():
        col_varname = converter.convert_to_system_name(col)
        if isinstance(col_type, dict) and col_type['type'] == 'file-upload':
            source_code += f"""
                            root.{entity_varname}.STARK_uploaded_s3_keys['{col_varname}'] = root.{entity_varname}.{col_varname} != "" ? root.{entity_varname}.STARK_uploaded_s3_keys.{col_varname}.S : ""
                            root.STARK_upload_elements['{col_varname}'].file              = root.{entity_varname}.{col_varname} != "" ? root.{entity_varname}.{col_varname} : ""
                            root.STARK_upload_elements['{col_varname}'].progress_bar_val  = root.{entity_varname}.{col_varname} != "" ? 100 : 0
                            root.object_url_prefix                                           = data['object_url_prefix']
                            """

    #If there are 1:1 rel fields, we need to assign their initial value to the still-unpopulated drop-down list so that it displays 
    #   a value even before the lazy-loading is triggered.
    for col, col_type in cols.items():
        if isinstance(col_type, dict) and col_type["type"] == "relationship":
            has_one = col_type.get('has_one', '')
            has_many = col_type.get('has_many', '')
            
            foreign_entity  = converter.convert_to_system_name(has_one if has_one != '' else has_many)
            foreign_field   = converter.convert_to_system_name(col_type.get('value', foreign_entity))
            foreign_display = converter.convert_to_system_name(col_type.get('display', foreign_field))

            if  has_one != '':
                #simple 1-1 relationship
                source_code += f"""
                            root.lists.{foreign_field} = [  {{ value: root.{entity_varname}.{foreign_field}, text: root.{entity_varname}.{foreign_field} }},]
                            root.list_{foreign_entity}()"""
            elif has_many != '':
                source_code += f"""
                            root.multi_select_values.{foreign_entity} = root.{entity_varname}.{foreign_entity}.split(', ')
                            root.list_{foreign_entity}()"""
    source_code += f"""
                            console.log("VIEW: Retreived module data.")
                            root.show()
                            loading_modal.hide()
                        }})
                        .catch(function(error) {{
                            console.log("Encountered an error! [" + error + "]")
                            alert("Request Failed: System error or you may not have enough privileges")
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

                    var listview_data = STARK.get_local_storage_item('Listviews', '{entity_varname}')
                    var fetch_from_db = false;
                    console.log(listview_data)
                    if(listview_data) {{
                        root.listview_table = listview_data[root.curr_page]
                        root.next_token = listview_data['next_token'];
                        spinner.hide()
                    }}
                    else {{
                        fetch_from_db = true
                    }}
                    
                    if(fetch_from_db) {{
                        {entity_app}.list(payload).then( function(data) {{"""

    for col, col_type in cols.items():
        col_varname = converter.convert_to_system_name(col)
        if isinstance(col_type, dict) and col_type["type"] == "relationship":
            has_many = col_type.get('has_many', '')
            if has_many != "":
                foreign_entity  = converter.convert_to_system_name(has_many)
                source_code += f"""
                            for (let x = 0; x < (data['Items']).length; x++) {{
                                data['Items'][x]['{foreign_entity}'] = ((data['Items'][x]['{foreign_entity}'].split(', ')).sort()).join(', ')      
                            }}
                """
                        
    source_code += f"""
                            token = data['Next_Token'];
                            root.listview_table = data['Items'];
                            var data_to_store = {{}}
                            data_to_store[root.curr_page] = data['Items']
                            data_to_store['next_token'] = token
                            STARK.set_local_storage_item('Listviews', '{entity_varname}', data_to_store)
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
                            alert("Request Failed: System error or you may not have enough privileges")
                            spinner.hide()
                        }});
                    }}
                }},

                formValidation: function () {{
                    root.error_message = ""
                    let no_operator = []
                    let isValid = true;
                    root.showError = false
                    for (element in root.custom_report) {{
                        if(root.custom_report[element].value != '' && root.custom_report[element].operator == '')
                        {{
                            root.showError = true
                            //fetch all error
                            if(root.custom_report[element].operator == '')
                            {{
                                isValid = false
                                no_operator.push(element)
                            }}
                        }}
                    }}
                    root.no_operator = no_operator;
                    //display error
                    root.error_message = "Put operator/s on: " + no_operator ;
                    return isValid
                }},

                generate: function () {{
                    let temp_show_fields = []
                    root.checked_fields.forEach(element => {{
                        let temp_index = {{'field': element, label: element.replaceAll("_"," ")}}
                        temp_show_fields.push(temp_index)
                    }});
                    root.STARK_report_fields = temp_show_fields;
                    root.custom_report['STARK_report_fields'] = root.STARK_report_fields"""
    for col, col_type in cols.items():
        col_varname = converter.convert_to_system_name(col)
        if isinstance(col_type, dict):
            col_values = col_type.get("values", "")
            if isinstance(col_values, list):
                source_code += f"""
                    root.custom_report['{col_varname}']['value'] = root.custom_report['{col_varname}']['value'] == "" ? root.multi_select_values['{col_varname}'].join(', '): root.custom_report['{col_varname}']['value']"""
    source_code += f"""
                    let report_payload = {{ {entity_varname}: root.custom_report }}
                    if(root.formValidation())
                    {{
                        loading_modal.show()
                        {entity_app}.report(report_payload).then( function(data) {{
                            root.listview_table = data[0];
                            root.temp_csv_link = data[2][0];
                            root.temp_pdf_link = data[2][1];
                            console.log("DONE! Retrieved report.");
                            loading_modal.hide()
                            root.showReport = true
            
                        }})
                        .catch(function(error) {{
                            console.log("Encountered an error! [" + error + "]")
                            alert("Request Failed: System error or you may not have enough privileges")
                            loading_modal.hide()
                        }});
                    }}
                }},
                download_report(file_type = "csv") {{
                    let link = "https://" + (file_type == "csv" ? root.temp_csv_link : root.temp_pdf_link)
                    window.location.href = link
                }},
                toggle_all(checked) {{
                    root.checked_fields = checked ? root.temp_checked_fields.slice() : []
                    root.all_selected = checked
                }},"""
    if with_upload:
        source_code += f"""
                process_upload_file(file_upload_element) {{
                    var upload_processed = {{
                            'message': 'initial'
                        }}
                    var uuid = ""
                    var ext = ""
                    var file = root.STARK_upload_elements[file_upload_element].file;
                    is_valid = true;
                    error_message = ""

                    if(file)
                    {{
                        if(typeof root.{entity_varname}.STARK_uploaded_s3_keys[file_upload_element] == 'undefined')
                        {{
                            uuid = STARK.create_UUID()
                            ext = file.name.split('.').pop()
                        }}
                        else
                        {{
                            var s3_key = root.{entity_varname}.STARK_uploaded_s3_keys[file_upload_element]
                            uuid = s3_key.split('.').shift()
                            ext = file.name.split('.').pop()
                        }}

                        valid_file = STARK.get_file_ext_whitelist(root.ext_whitelist[file_upload_element], root.ext_whitelist_table).split(", ").includes(ext)
                        allowed_file_size = STARK.get_allowed_upload_size(root.allowed_size[file_upload_element], root.allowed_size_table)
                        if(!valid_file)
                        {{
                            //check if file type is valid
                            error_message = `Invalid file type: ${{ext.toUpperCase()}}`
                        }}
                        else if(file.size > allowed_file_size)
                        {{
                            // check if file size is allowed
                            error_message = `Uploaded file exceeded allowed file size of ${{allowed_file_size / 1024 / 1024}}MB`
                        }}

                        if(error_message == "")
                        {{
                            upload_processed = {{
                                'message'   : error_message,
                                'file_body' : file,
                                'filename'  : file.name,
                                's3_key'    : uuid + '.' + ext
                            }}
                        }}
                        else
                        {{
                            upload_processed = {{
                                'message'   : error_message
                            }}
                        }}
                    }}

                    return upload_processed
                }},
                init_s3_access: function(){{

                    if(root.s3_access == "")
                    {{
                        STARK.get_s3_credentials().then( function(data){{
                            access_key_id = data[0]['access_key_id']
                            secret_access_key = data[0]['secret_access_key']

                            root.s3_access = new AWS.S3({{
                                params: {{Bucket: STARK.bucket_name}},
                                region: STARK.region_name,
                                apiVersion: '2006-03-01',
                                accessKeyId: access_key_id,
                                secretAccessKey: secret_access_key,
                            }});

                            console.log("S3 authorized")
                        }}).catch(function(error) {{
                            console.log("Can't retrieve S3 creds! [" + error + "]")
                        }});
                    }}
                    
                }},
                s3upload: function(file_upload_element) {{

                    root.STARK_upload_elements[file_upload_element].progress_bar_val = 0
                    var upload_processed = root.process_upload_file(file_upload_element)
                    if(upload_processed['message'] == "")
                    {{
                        root.{entity_varname}[file_upload_element] = upload_processed['filename']
                        var filePath = 'tmp/' + upload_processed['s3_key'];
                        root.{entity_varname}.STARK_uploaded_s3_keys[file_upload_element] = upload_processed['s3_key']
                        root.s3_access.upload({{
                            Key: filePath,
                            Body: upload_processed['file_body'],
                            ACL: 'public-read'
                            }}, function(err, data) {{
                                console.log(data)
                                if(err) {{
                                    console.log(err)
                                }}
                            }}).on('httpUploadProgress', function (progress) {{
                            root.STARK_upload_elements[file_upload_element].progress_bar_val = parseInt((progress.loaded * 100) / progress.total);
                            root.metadata[file_upload_element].state = true
                            root.metadata[file_upload_element].feedback = "" 
                        }});
                    }}
                    else
                    {{
                        //do not show alert when file upload is opened then closed
                        if(upload_processed['message'] != 'initial')
                        {{
                            root.metadata[file_upload_element].state = false
                            root.metadata[file_upload_element].feedback = upload_processed['message'] 
                        }}
                    }}

                }},"""
    source_code += f"""
                onOptionClick({{ option, addTag }}, reference) {{
                    addTag(option.value)
                    this.search[reference] = ''
                    this.$refs[reference].show(true)
                }},
                refresh_list () {{
                    root.listview_table = ''
                    STARK.local_storage_delete_key('Listviews', '{entity_varname}');
                    root.list()
                }},
                """

    for col, col_type in cols.items():
        if isinstance(col_type, dict) and col_type["type"] == "relationship":
            has_one = col_type.get('has_one', '')
            has_many = col_type.get('has_many', '')
            if  has_one != '' or has_many != '':
                foreign_entity  = converter.convert_to_system_name(has_one if has_one != '' else has_many)
                foreign_field   = converter.convert_to_system_name(col_type.get('value', foreign_entity))
                foreign_display = converter.convert_to_system_name(col_type.get('display', foreign_field))

                source_code += f"""
                list_{foreign_entity}: function () {{
                    if (this.list_status.{foreign_entity} == 'empty') {{
                        loading_modal.show();
                        root.lists.{foreign_entity} = []

                        //FIXME: for now, generic list() is used. Can be optimized to use a list function that only retrieves specific columns
                        fields = ['{foreign_field}', '{foreign_display}']
                        {foreign_entity}_app.get_fields(fields).then( function(data) {{
                            data.forEach(function(arrayItem) {{
                                value = arrayItem['{foreign_field}']
                                text  = arrayItem['{foreign_display}']"""
                if has_one != '': 
                    source_code += f"""            
                                root.lists.{foreign_entity}.push({{ value: value, text: text }})"""
                if has_many != '': 
                    source_code += f"""            
                                root.lists.{foreign_entity}.push({{ value: value, text: text }})"""
                source_code += f""" 
                }})
                            root.list_status.{foreign_entity} = 'populated'
                            loading_modal.hide();
                        }}).catch(function(error) {{
                            console.log("Encountered an error! [" + error + "]")
                            loading_modal.hide();
                        }});
                    }}
                }},
                """
                if has_many != '':
                    source_code += f"""
                    split_string: function(str) {{
                        var arr = str.split(", ")
                        var return_str = ''
                        arr.forEach(element => {{
                            return_str += this.tag_display_text(element).concat(", ")
                        }});
                        return return_str
                    }},

                    tag_display_text: function (tag) {{
                        display_text = ""
                        if(typeof tag =='string')
                        {{
                            display_text = tag
                        }}
                        else
                        {{
                            var index = this.lists.{foreign_entity}.findIndex(opt => tag == opt.value)
                            display_text = this.lists.{foreign_entity}[index].text
                        }}
                        return display_text
                    }},
                    """

    source_code += f"""
            }},
            computed: {{"""
    for col, col_type in cols.items():
        col_varname = converter.convert_to_system_name(col)
        if isinstance(col_type, dict):
            col_values = col_type.get("values","")
            if (col_type["type"] == "relationship") or isinstance(col_values, list):
                source_code += f"""
            {col_varname}_criteria() {{
                return this.search['{col_varname}'].trim().toLowerCase()
            }},
            {col_varname}() {{
                const {col_varname}_criteria = this.{col_varname}_criteria
                // Filter out already selected options
                const options = this.lists.{col_varname}.filter(opt => this.multi_select_values.{col_varname}.indexOf(opt.value) === -1)
                if ({col_varname}_criteria) {{
                // Show only options that match {col_varname}_criteria
                return options.filter(opt => (opt.text).toLowerCase().indexOf({col_varname}_criteria) > -1);
                }}
                // Show all options available
                return options
            }},
            {col_varname}_search_desc() {{
                if (this.{col_varname}_criteria && this.{col_varname}.length === 0) {{
                return 'There are no tags matching your search criteria'
                }}
                return ''
            }},"""
    source_code += f"""
            }}    
        }})
        
        """

    return textwrap.dedent(source_code)


def set_type(col_type):

    #Default is 'S'. Defined here so we don't need duplicate Else statements below
    col_type_id = 'S'

    if isinstance(col_type, dict):
        #special/complex types
        if col_type["type"] in [ "int-spinner", "decimal-spinner" ]:
            col_type_id = 'N'
        
        if col_type["type"] in [ "tags", "multiple choice" ]:
            col_type_id = 'SS'
    
    elif col_type in [ "int", "number" ]:
        col_type_id = 'N'

    return col_type_id