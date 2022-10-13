#STARK Code Generator component.
#Produces the customized dynamic content for a STARK system

#Python Standard Library
import base64
import textwrap

#Private modules
import convert_friendly_to_system as converter

def create(data):
  
    pk             = data["PK"]
    entity         = data["Entity"]
    columns        = data["Columns"]
    ddb_table_name = data["DynamoDB Name"]
    bucket_name    = data['Bucket Name']
    relationships  = data["Relationships"]
    
    #Convert human-friendly names to variable-friendly names
    entity_varname = converter.convert_to_system_name(entity)
    pk_varname     = converter.convert_to_system_name(pk)

    default_sk     = entity_varname + "|info"
    with_upload    = False
 
    #Create the column dict we'll use in the code as a declaration
    col_dict = '{ "pk": pk, "sk": sk, '
    for col in columns:
        col_varname = converter.convert_to_system_name(col)
        col_dict += f'"{col_varname}": {col_varname}, '
    col_dict = col_dict[:-2]
    col_dict += ' }'

    #Create the dict value retrieval code for the add/edit function body
    dict_to_var_code = f"""pk = data.get('pk', '')
        sk = data.get('sk', '')    
        if sk == '': sk = default_sk"""
    for col, col_type in columns.items():
        col_varname = converter.convert_to_system_name(col)
        
        #check for file upload
        if isinstance(col_type, dict) and col_type['type'] == 'file-upload':
            with_upload = True
        
        col_type_id = set_type(col_type)

        if col_type_id in ['S', 'N']: 
            dict_to_var_code += f"""
        {col_varname} = str(data.get('{col_varname}', ''))"""

        else:
            dict_to_var_code += f"""
        {col_varname} = data.get('{col_varname}', '')"""


    #This is for our DDB update call
    update_expression = ""
    for col in columns:
        col_varname = converter.convert_to_system_name(col)
        update_expression += f"""#{col_varname} = :{col_varname}, """
    update_expression += " #STARKListViewsk = :STARKListViewsk"
    if with_upload:
        update_expression += ", #STARK_uploaded_s3_keys = :STARK_uploaded_s3_keys"

    source_code = f"""\
    #Python Standard Library
    import base64
    import json
    import importlib
    from urllib.parse import unquote

    #Extra modules
    import boto3
    import uuid

    #STARK
    import stark_core 
    from stark_core import utilities
    from stark_core import validation
    from stark_core import data_abstraction

    ddb    = boto3.client('dynamodb')
    s3_res = boto3.resource('s3')

    #######
    #CONFIG
    ddb_table         = stark_core.ddb_table
    bucket_name       = stark_core.bucket_name
    region_name       = stark_core.region_name
    page_limit        = stark_core.page_limit
    bucket_url        = stark_core.bucket_url
    bucket_tmp        = stark_core.bucket_tmp
    pk_field          = "{pk_varname}"
    default_sk        = "{default_sk}"
    sort_fields       = ["{pk_varname}", ]
    relationships     = {relationships}
    entity_upload_dir = stark_core.upload_dir + "{entity_varname}/"
    metadata          = {{
                "{pk_varname}": {{
                    'value': '',
                    'required': True,
                    'max_length': '',
                    'data_type': '',
                    'state': None,
                    'feedback': ''
                }},"""
        
    
    for col in columns:
        col_varname = converter.convert_to_system_name(col)
        source_code += f"""
                '{col_varname}': {{
                    'value': '',
                    'required': True,
                    'max_length': '',
                    'data_type': '',
                    'state': None,
                    'feedback': ''
                }},""" 
                    
    source_code += f"""
    }}
    resp_obj = None

    ############
    #PERMISSIONS
    stark_permissions = {{
        'view': '{entity}|View',
        'add': '{entity}|Add',
        'delete': '{entity}|Delete',
        'edit': '{entity}|Edit',
        'report': '{entity}|Report'
    }}

    def lambda_handler(event, context):
        responseStatusCode = 200

        #Get request type
        request_type = event.get('queryStringParameters',{{}}).get('rt','')

        if request_type == '':
            ########################
            #Handle non-GET requests
    
            #Get specific request method
            method  = event.get('requestContext').get('http').get('method')

            if event.get('isBase64Encoded') == True :
                payload = json.loads(base64.b64decode(event.get('body'))).get('{entity_varname}',"")
            else:    
                payload = json.loads(event.get('body')).get('{entity_varname}',"")

            data    = {{}}

            if payload == "":
                return {{
                    "isBase64Encoded": False,
                    "statusCode": 400,
                    "body": json.dumps("Client payload missing"),
                    "headers": {{
                        "Content-Type": "application/json",
                    }}
                }}
            else:
                isInvalidPayload = False
                data['pk'] = payload.get('{pk_varname}')"""
    for col, col_type in columns.items():
        col_varname = converter.convert_to_system_name(col)
        source_code +=f"""
                data['{col_varname}'] = payload.get('{col_varname}','')"""

    source_code +=f"""
                if payload.get('STARK_isReport', False) == False:
                    data['orig_pk'] = payload.get('orig_{pk_varname}','')
                    data['sk'] = payload.get('sk', '')
                    if data['sk'] == "":
                        data['sk'] = default_sk
                    #FIXME: THIS IS A STUB, MIGHT BE USED IN REPORTING
                    ListView_index_values = []
                    for field in sort_fields:
                        ListView_index_values.append(payload.get(field))
                    data['STARK-ListView-sk'] = "|".join(ListView_index_values)
                else:
                    #FIXME: Reporting payload processing:
                    # - identifying filter fields
                    # - operators validator
                    for index, attributes in data.items():
                        if attributes['value'] != "":
                            if attributes['operator'] == "":
                                isInvalidPayload = True
                    data['STARK_report_fields'] = payload.get('STARK_report_fields',[])
                    data['STARK_isReport'] = payload.get('STARK_isReport', False)
                    data['STARK_sum_fields'] = payload.get('STARK_sum_fields', [])
                    data['STARK_count_fields'] = payload.get('STARK_count_fields', [])
                    data['STARK_group_by_1'] = payload.get('STARK_group_by_1', '')

                data['STARK_uploaded_s3_keys'] = payload.get('STARK_uploaded_s3_keys',{{}})

                if isInvalidPayload:
                    return {{
                        "isBase64Encoded": False,
                        "statusCode": 400,
                        "body": json.dumps("Missing operators"),
                        "headers": {{
                            "Content-Type": "application/json",
                        }}
                    }}

            if method == "DELETE":
                if(stark_core.sec.is_authorized(stark_permissions['delete'], event, ddb)):
                    response = delete(data)
                else:
                    responseStatusCode, response = stark_core.sec.authFailResponse

            elif method == "PUT":
                if(stark_core.sec.is_authorized(stark_permissions['edit'], event, ddb)):
                    payload = data
                    payload[pk_field] = data['pk']
                    invalid_payload = validation.validate_form(payload, metadata)
                    if len(invalid_payload) > 0:
                        return {{
                            "isBase64Encoded": False,
                            "statusCode": 200,
                            "body": json.dumps(invalid_payload),
                            "headers": {{
                                "Content-Type": "application/json",
                            }}
                        }}
                        
                    else:
                        if data['orig_pk'] == data['pk']:
                            response = edit(data)
                        else:
                            #We can't update DDB PK, so if PK is different, we need to do ADD + DELETE
                            response   = add(data, method)
                            data['pk'] = data['orig_pk']
                            response   = delete(data)
                else:
                    responseStatusCode, response = stark_core.sec.authFailResponse

            elif method == "POST":
                if 'STARK_isReport' in data:
                    if(stark_core.sec.is_authorized(stark_permissions['report'], event, ddb)):
                        response = report(data, default_sk)
                    else:
                        responseStatusCode, response = stark_core.sec.authFailResponse
                else:
                    if(stark_core.sec.is_authorized(stark_permissions['add'], event, ddb)):
                        payload = data
                        payload[pk_field] = data['pk']
                        invalid_payload = validation.validate_form(payload, metadata)
                        if len(invalid_payload) > 0:
                            return {{
                                "isBase64Encoded": False,
                                "statusCode": 200,
                                "body": json.dumps(invalid_payload),
                                "headers": {{
                                    "Content-Type": "application/json",
                                }}
                            }}
                            
                        else:
                            response = add(data)
                    else:
                        responseStatusCode, response = stark_core.sec.authFailResponse

            else:
                return {{
                    "isBase64Encoded": False,
                    "statusCode": 400,
                    "body": json.dumps("Could not handle API request"),
                    "headers": {{
                        "Content-Type": "application/json",
                    }}
                }}

        else:
            ####################
            #Handle GET requests
            if request_type == "all":
                #check for submitted token
                lv_token = event.get('queryStringParameters',{{}}).get('nt', None)
                if lv_token != None:
                    lv_token = unquote(lv_token)
                    lv_token = json.loads(lv_token)
        
                items, next_token = get_all(default_sk, lv_token)

                response = {{
                    'Next_Token': json.dumps(next_token),
                    'Items': items
                }}
            
            elif request_type == "get_fields":
                fields = event.get('queryStringParameters').get('fields','')
                fields = fields.split(",")
                response = data_abstraction.get_fields(fields, pk_field, default_sk)

            elif request_type == "detail":

                pk = event.get('queryStringParameters').get('{pk_varname}','')
                sk = event.get('queryStringParameters').get('sk','')
                if sk == "":
                    sk = default_sk

                response = get_by_pk(pk, sk)
            else:
                return {{
                    "isBase64Encoded": False,
                    "statusCode": 400,
                    "body": json.dumps("Could not handle GET request - unknown request type"),
                    "headers": {{
                        "Content-Type": "application/json",
                    }}
                }}

        return {{
            "isBase64Encoded": False,
            "statusCode": responseStatusCode,
            "body": json.dumps(response),
            "headers": {{
                "Content-Type": "application/json",
            }}
        }}

    def report(data, sk=default_sk):
        #FIXME: THIS IS A STUB, WILL NEED TO BE UPDATED WITH
        #   ENHANCED LISTVIEW LOGIC LATER WHEN WE ACTUALLY IMPLEMENT REPORTING
        
        temp_string_filter = ""
        object_expression_value = {{':sk' : {{'S' : sk}}}}
        report_param_dict = {{}}
        for key, index in data.items():
            if key not in ["STARK_isReport", "STARK_report_fields", "STARK_uploaded_s3_keys", 
                            "STARK_sum_fields", 'STARK_count_fields', 'STARK_group_by_1']:
                if index['value'] != "":
                    processed_operator_and_parameter_dict = utilities.compose_report_operators_and_parameters(key, index) 
                    temp_string_filter += processed_operator_and_parameter_dict['filter_string']
                    object_expression_value.update(processed_operator_and_parameter_dict['expression_values'])
                    report_param_dict.update(processed_operator_and_parameter_dict['report_params'])
        string_filter = temp_string_filter[1:-3]

        next_token = 'initial'
        items = []
        ddb_arguments = {{}}
        aggregated_results = {{}}
        ddb_arguments['TableName'] = ddb_table
        ddb_arguments['IndexName'] = "STARK-ListView-Index"
        ddb_arguments['Select'] = "ALL_ATTRIBUTES"
        ddb_arguments['ReturnConsumedCapacity'] = 'TOTAL'
        ddb_arguments['KeyConditionExpression'] = 'sk = :sk'
        ddb_arguments['ExpressionAttributeValues'] = object_expression_value

        if temp_string_filter != "":
            ddb_arguments['FilterExpression'] = string_filter
            
        while next_token != None:
            next_token = '' if next_token == 'initial' else next_token

            if next_token != '':
                ddb_arguments['ExclusiveStartKey']=next_token

            response = ddb.query(**ddb_arguments)
            raw = response.get('Items')
            next_token = response.get('LastEvaluatedKey')
            aggregate_report = False if data['STARK_group_by_1'] == '' else True
            for record in raw:
                item = map_results(record)
                if aggregate_report:
                    aggregate_key = data['STARK_group_by_1']
                    aggregate_key_value = item.get(aggregate_key)
                    if aggregate_key_value in aggregated_results:
                        for field in data['STARK_count_fields']:
                            count_index_name = f"Count of {{field}}"
                            aggregated_results[aggregate_key_value][count_index_name] += 1

                        for field in data['STARK_sum_fields']:
                            sum_index_name = f"Sum of {{field}}"
                            sum_value = float(item.get(field))
                            aggregated_results[aggregate_key_value][sum_index_name] = round(aggregated_results[aggregate_key_value][sum_index_name], 1) + sum_value

                        for column in data['STARK_report_fields']:
                            if column != aggregate_key:  
                                aggregated_results[aggregate_key_value][column] = item.get(column.replace(" ","_"))

                    else:
                        temp_dict = {{ aggregate_key : aggregate_key_value}}
                        for field in data['STARK_count_fields']:
                            count_index_name = f"Count of {{field}}"
                            temp_dict.update({{
                                count_index_name:  1
                            }})
                            
                        for field in data['STARK_sum_fields']:
                            sum_index_name = f"Sum of {{field}}"
                            sum_value = float(item.get(field))
                            temp_dict.update({{
                                sum_index_name: sum_value
                            }})
                        
                        for column in data['STARK_report_fields']:
                            if column != aggregate_key:  
                                temp_dict.update({{
                                    column: item.get(column.replace(" ","_"))
                                }})

                        aggregated_results[aggregate_key_value] = temp_dict
                else:
                    items.append(item)

        report_list = []
        csv_file = ''
        pdf_file = ''
        report_header = []
        diff_list = []
        if aggregate_report:
            temp_list = []
            for key, val in aggregated_results.items():
                temp_header = []
                for index in val.keys():
                    temp_header.append(index.replace("_"," "))
                temp_list.append(val)
                report_header = temp_header
            items = temp_list
        else:
            display_fields = data['STARK_report_fields']
            master_fields = []
            for key in metadata.keys():
                master_fields.append(key.replace("_"," "))
            if len(display_fields) > 0:
                report_header = display_fields
                diff_list = list(set(master_fields) - set(display_fields))
            else:
                report_header = master_fields

        if len(items) > 0:
            for key in items:
                temp_dict = {{}}
                #remove primary identifiers and STARK attributes
                if not aggregate_report:
                    key.pop("sk")"""
    if with_upload:
        source_code += f"""
                    key.pop("STARK uploaded s3 keys")"""
    source_code += f"""
                for index, value in key.items():
                    temp_dict[index.replace("_"," ")] = value
                report_list.append(temp_dict)

            report_list = utilities.filter_report_list(report_list, diff_list)
            csv_file = utilities.create_csv(report_list, report_header)
            pdf_file = utilities.prepare_pdf_data(report_list, report_header, report_param_dict, metadata, pk_field)

        csv_bucket_key = bucket_tmp + csv_file
        pdf_bucket_key = bucket_tmp + pdf_file

        if not aggregate_report:
            report_list = items
            new_report_list = []
            for row in report_list:
                temp_dict = {{}}
                for index, value in row.items():
                    temp_dict[index.replace("_"," ")] = value
                new_report_list.append(temp_dict)
            report_list = new_report_list

        return report_list, csv_bucket_key, pdf_bucket_key

    def get_all(sk=default_sk, lv_token=None, db_handler = None):
        if db_handler == None:
            db_handler = ddb

        
        items = []
        ddb_arguments = {{}}
        ddb_arguments['TableName'] = ddb_table
        ddb_arguments['IndexName'] = "STARK-ListView-Index"
        ddb_arguments['Select'] = "ALL_ATTRIBUTES"
        ddb_arguments['Limit'] = page_limit
        ddb_arguments['ReturnConsumedCapacity'] = 'TOTAL'
        ddb_arguments['KeyConditionExpression'] = 'sk = :sk'
        ddb_arguments['ExpressionAttributeValues'] = {{ ':sk' : {{'S' : sk }} }}

        if lv_token != None:
            ddb_arguments['ExclusiveStartKey'] = lv_token

        next_token = ''
        while len(items) < page_limit and next_token is not None:
            if next_token != '':
                ddb_arguments['ExclusiveStartKey']=next_token

            response = db_handler.query(**ddb_arguments)
            raw = response.get('Items')
            next_token = response.get('LastEvaluatedKey')

            for record in raw:
                items.append(map_results(record))

        #Get the "next" token, pass to calling function. This enables a "next page" request later.
        next_token = response.get('LastEvaluatedKey')

        return items, next_token

    def get_by_pk(pk, sk=default_sk, db_handler = None):
        if db_handler == None:
            db_handler = ddb

        ddb_arguments = {{}}
        ddb_arguments['TableName'] = ddb_table
        ddb_arguments['Select'] = "ALL_ATTRIBUTES"
        ddb_arguments['KeyConditionExpression'] = "#pk = :pk and #sk = :sk"
        ddb_arguments['ExpressionAttributeNames'] = {{
                                                    '#pk' : 'pk',
                                                    '#sk' : 'sk'
                                                }}
        ddb_arguments['ExpressionAttributeValues'] = {{
                                                    ':pk' : {{'S' : pk }},
                                                    ':sk' : {{'S' : sk }}
                                                }}
        response = db_handler.query(**ddb_arguments)
        raw = response.get('Items')

        #Map to expected structure
        response = {{}}
        response['item'] = map_results(raw[0])"""
    if with_upload : 
        source_code +=f"""
        response['object_url_prefix'] = bucket_url + entity_upload_dir"""
    source_code+= f"""

        return response

    def delete(data, db_handler = None):
        if db_handler == None:
            db_handler = ddb

        pk = data.get('pk','')
        sk = data.get('sk','')
        if sk == '': sk = default_sk

        ddb_arguments = {{}}
        ddb_arguments['TableName'] = ddb_table
        ddb_arguments['Key'] = {{
                'pk' : {{'S' : pk}},
                'sk' : {{'S' : sk}}
            }}

        response = db_handler.delete_item(**ddb_arguments)
        global resp_obj
        resp_obj = response

        return "OK"

    def edit(data, db_handler = None):
        if db_handler == None:
            db_handler = ddb           
        {dict_to_var_code}"""

    if with_upload:
        source_code += f"""
        temp_s3_keys = data.get('STARK_uploaded_s3_keys', {{}}) 
        STARK_uploaded_s3_keys = {{}}
        for key, items in temp_s3_keys.items():
            STARK_uploaded_s3_keys[key] = {{ 'S' : items }}
            utilities.copy_object_to_bucket(items, entity_upload_dir)
        """
    source_code += f"""
        UpdateExpressionString = "SET {update_expression}" 
        ExpressionAttributeNamesDict = {{"""

    for col in columns:
        col_varname = converter.convert_to_system_name(col)
        source_code +=f"""
            '#{col_varname}' : '{col_varname}',"""  
    
    if with_upload:
        source_code += f"""
            '#STARK_uploaded_s3_keys': 'STARK_uploaded_s3_keys',"""
    source_code += f"""
            '#STARKListViewsk' : 'STARK-ListView-sk'
        }}
        ExpressionAttributeValuesDict = {{"""

    for col, col_type in columns.items():
        col_varname = converter.convert_to_system_name(col)
        col_type_id = set_type(col_type)

        source_code +=f"""
            ':{col_varname}' : {{'{col_type_id}' : {col_varname} }},"""  

    if with_upload:
        source_code += f"""
            ':STARK_uploaded_s3_keys': {{'M': STARK_uploaded_s3_keys }},"""
    source_code += f"""
            ':STARKListViewsk' : {{'S' : data['STARK-ListView-sk']}}
        }}

        ddb_arguments = {{}}
        ddb_arguments['TableName'] = ddb_table
        ddb_arguments['Key'] = {{
                'pk' : {{'S' : pk}},
                'sk' : {{'S' : sk}}
            }}
        ddb_arguments['ReturnValues'] = 'UPDATED_NEW'
        ddb_arguments['UpdateExpression'] = UpdateExpressionString
        ddb_arguments['ExpressionAttributeNames'] = ExpressionAttributeNamesDict
        ddb_arguments['ExpressionAttributeValues'] = ExpressionAttributeValuesDict

        response = db_handler.update_item(**ddb_arguments)
        """
    if len(relationships) > 0:
        source_code += f"""
        for relation in relationships['has_one']:
            cascade_pk_change_to_child(data, relation['child'], relation['attribute'])
        """
    source_code += f"""

        global resp_obj
        resp_obj = response
        return "OK"

    def add(data, method='POST', db_handler=None):
        if db_handler == None:
            db_handler = ddb
        {dict_to_var_code}"""

    if with_upload:
        source_code += f"""
        temp_s3_keys = data.get('STARK_uploaded_s3_keys', {{}}) 
        STARK_uploaded_s3_keys = {{}}
        for key, items in temp_s3_keys.items():
            STARK_uploaded_s3_keys[key] = {{ 'S' : items }}
            utilities.copy_object_to_bucket(items, entity_upload_dir)
        """
    source_code += f"""
        item={{}}
        item['pk'] = {{'S' : pk}}
        item['sk'] = {{'S' : sk}}"""

    for col, col_type in columns.items():
        col_varname = converter.convert_to_system_name(col)
        col_type_id = set_type(col_type)

        source_code +=f"""
        item['{col_varname}'] = {{'{col_type_id}' : {col_varname}}}"""

    if with_upload:
        source_code += f"""
        item['STARK_uploaded_s3_keys'] = {{'M' : STARK_uploaded_s3_keys}}"""

    source_code += f"""

        if data.get('STARK-ListView-sk','') == '':
            item['STARK-ListView-sk'] = {{'S' : create_listview_index_value(data)}}
        else:
            item['STARK-ListView-sk'] = {{'S' : data['STARK-ListView-sk']}}

        ddb_arguments = {{}}
        ddb_arguments['TableName'] = ddb_table
        ddb_arguments['Item'] = item
        response = db_handler.put_item(**ddb_arguments)
        """
    if len(relationships) > 0:
        source_code += f"""
        if method == 'POST':
            data['orig_pk'] = pk

        for relation in relationships['has_one']:
            cascade_pk_change_to_child(data, relation['child'], relation['attribute'])
        """
    source_code += f"""
        global resp_obj
        resp_obj = response
        return "OK"
    
    def create_listview_index_value(data):
        ListView_index_values = []
        for field in sort_fields:
            if field == pk_field:
                ListView_index_values.append(data['pk'])
            else:
                ListView_index_values.append(data.get(field))
        STARK_ListView_sk = "|".join(ListView_index_values)
        return STARK_ListView_sk
    
    def map_results(record):
        item = {{}}
        item['{pk_varname}'] = record.get('pk', {{}}).get('S','')
        item['sk'] = record.get('sk',{{}}).get('S','')"""
    for col, col_type in columns.items():
        col_varname = converter.convert_to_system_name(col)
        col_type_id = set_type(col_type)

        source_code +=f"""
        item['{col_varname}'] = record.get('{col_varname}',{{}}).get('{col_type_id}','')"""

    if with_upload:
        source_code += f"""
        item['STARK_uploaded_s3_keys'] = record.get('STARK_uploaded_s3_keys',{{}}).get('M',{{}})"""
    source_code += f"""
        return item

    def get_all_by_old_parent_value(old_pk_val, attribute, sk = default_sk):
    
        string_filter = " #Attribute = :old_parent_value"
        object_expression_value = {{':sk' : {{'S' : sk}},
                                    ':old_parent_value': {{'S' : old_pk_val}}}}
        ExpressionAttributeNamesDict = {{
            '#Attribute' : attribute,
        }}

        ddb_arguments = {{}}
        ddb_arguments['TableName'] = ddb_table
        ddb_arguments['IndexName'] = "STARK-ListView-Index"
        ddb_arguments['Select'] = "ALL_ATTRIBUTES"
        ddb_arguments['ReturnConsumedCapacity'] = 'TOTAL'
        ddb_arguments['FilterExpression'] = string_filter
        ddb_arguments['KeyConditionExpression'] = 'sk = :sk'
        ddb_arguments['ExpressionAttributeValues'] = object_expression_value
        ddb_arguments['ExpressionAttributeNames'] = ExpressionAttributeNamesDict

        next_token = 'initial'
        items = []
        while next_token != None:
            next_token = '' if next_token == 'initial' else next_token

            if next_token != '':
                ddb_arguments['ExclusiveStartKey']=next_token

            response = ddb.query(**ddb_arguments)
            raw = response.get('Items')
            next_token = response.get('LastEvaluatedKey')
            for record in raw:
                item = map_results(record)
                #add pk as literal 'pk' value
                #and STARK-ListView-Sk
                item['pk'] = record.get('pk', {{}}).get('S','')
                item['STARK-ListView-sk'] = record.get('STARK-ListView-sk',{{}}).get('S','')
                items.append(item)
                
        return items
    """
    
    if len(relationships) > 0:
        source_code += f"""    
    def cascade_pk_change_to_child(params, child_entity_name, attribute):
        temp_import = importlib.import_module(child_entity_name)

        #fetch all records from child using old pk value
        response = temp_import.get_all_by_old_parent_value(params['orig_pk'], attribute)

        #loop through response and update each record
        for record in response:
            record[attribute] = params['pk']
            temp_import.edit(record)

        return "OK"
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