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
        if col == 'Attachments':
            print(col_type)
        if col_type == 'file-upload':
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
    import sys
    import importlib
    from urllib.parse import unquote
    import math

    #Extra modules
    import boto3
    import csv
    import uuid
    from io import StringIO
    import os
    from fpdf import FPDF

    #STARK
    import stark_core 
    from stark_core import utilities

    ddb    = boto3.client('dynamodb')
    s3     = boto3.client("s3")
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
                    temp = payload.get('STARK_report_fields',[])
                    temp_report_fields = []
                    for index in temp:
                        temp_report_fields.append(index['label'])
                    for index, attributes in data.items():
                        if attributes['value'] != "":
                            if attributes['operator'] == "":
                                isInvalidPayload = True
                    data['STARK_report_fields'] = temp_report_fields
                    data['STARK_isReport'] = payload.get('STARK_isReport', False)

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
                response = get_fields(fields, default_sk)

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
            if key not in ["STARK_isReport", "STARK_report_fields", "STARK_uploaded_s3_keys"]:
                if index['value'] != "":
                    processed_operator_and_parameter_dict = utilities.compose_report_operators_and_parameters(key, index) 
                    temp_string_filter += processed_operator_and_parameter_dict['filter_string']
                    object_expression_value.update(processed_operator_and_parameter_dict['expression_values'])
                    report_param_dict.update(processed_operator_and_parameter_dict['report_params'])
        string_filter = temp_string_filter[1:-3]
        
        if temp_string_filter == "":
            response = ddb.query(
                TableName=ddb_table,
                IndexName="STARK-ListView-Index",
                Select='ALL_ATTRIBUTES',
                ReturnConsumedCapacity='TOTAL',
                KeyConditionExpression='sk = :sk',
                ExpressionAttributeValues=object_expression_value
            )
        else:
            response = ddb.query(
                TableName=ddb_table,
                IndexName="STARK-ListView-Index",
                Select='ALL_ATTRIBUTES',
                ReturnConsumedCapacity='TOTAL',
                FilterExpression=string_filter,
                KeyConditionExpression='sk = :sk',
                ExpressionAttributeValues=object_expression_value
            )
        raw = response.get('Items')

        #Map to expected structure
        #FIXME: this is duplicated code, make this DRY by outsourcing the mapping to a different function.
        items = []
        for record in raw:
            items.append(map_results(record))

        report_filenames = generate_reports(items, data['STARK_report_fields'], report_param_dict)
        #Get the "next" token, pass to calling function. This enables a "next page" request later.
        next_token = response.get('LastEvaluatedKey')

        return items, next_token, report_filenames

    def get_all(sk=default_sk, lv_token=None):

        if lv_token == None:
            response = ddb.query(
                TableName=ddb_table,
                IndexName="STARK-ListView-Index",
                Select='ALL_ATTRIBUTES',
                Limit=page_limit,
                ReturnConsumedCapacity='TOTAL',
                KeyConditionExpression='sk = :sk',
                ExpressionAttributeValues={{
                    ':sk' : {{'S' : sk}}
                }}
            )
        else:
            response = ddb.query(
                TableName=ddb_table,
                IndexName="STARK-ListView-Index",
                Select='ALL_ATTRIBUTES',
                Limit=page_limit,
                ExclusiveStartKey=lv_token,
                ReturnConsumedCapacity='TOTAL',
                KeyConditionExpression='sk = :sk',
                ExpressionAttributeValues={{
                    ':sk' : {{'S' : sk}}
                }}
            )

        raw = response.get('Items')

        #Map to expected structure
        #FIXME: this is duplicated code, make this DRY by outsourcing the mapping to a different function.
        items = []
        for record in raw:
            items.append(map_results(record))

        #Get the "next" token, pass to calling function. This enables a "next page" request later.
        next_token = response.get('LastEvaluatedKey')

        return items, next_token

    def get_by_pk(pk, sk=default_sk):
        response = ddb.query(
            TableName=ddb_table,
            Select='ALL_ATTRIBUTES',
            KeyConditionExpression="#pk = :pk and #sk = :sk",
            ExpressionAttributeNames={{
                '#pk' : 'pk',
                '#sk' : 'sk'
            }},
            ExpressionAttributeValues={{
                ':pk' : {{'S' : pk }},
                ':sk' : {{'S' : sk }}
            }}
        )

        raw = response.get('Items')

        #Map to expected structure
        response = {{}}
        response['item'] = map_results(raw[0])"""
    if with_upload : 
        source_code +=f"""
        response['object_url_prefix'] = bucket_url + entity_upload_dir"""
    source_code+= f"""

        return response

    def delete(data):
        pk = data.get('pk','')
        sk = data.get('sk','')
        if sk == '': sk = default_sk

        response = ddb.delete_item(
            TableName=ddb_table,
            Key={{
                'pk' : {{'S' : pk}},
                'sk' : {{'S' : sk}}
            }}
        )

        return "OK"

    def edit(data):                
        {dict_to_var_code}"""

    if with_upload:
        source_code += f"""
        temp_s3_keys = data.get('STARK_uploaded_s3_keys', {{}}) 
        STARK_uploaded_s3_keys = {{}}
        for key, items in temp_s3_keys.items():
            STARK_uploaded_s3_keys[key] = {{ 'S' : items }}
            copy_source = {{
                'Bucket': bucket_name,
                'Key': 'tmp/' + items
            }}
            
            extra_args = {{
                'ACL': 'public-read'
            }}
            s3_res.meta.client.copy(copy_source, bucket_name, entity_upload_dir + items, extra_args)
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

        response = ddb.update_item(
            TableName=ddb_table,
            Key={{
                'pk' : {{'S' : pk}},
                'sk' : {{'S' : sk}}
            }},
            UpdateExpression=UpdateExpressionString,
            ExpressionAttributeNames=ExpressionAttributeNamesDict,
            ExpressionAttributeValues=ExpressionAttributeValuesDict
        )
        """
    if len(relationships) > 0:
        source_code += f"""
        for relation in relationships:
            cascade_pk_change_to_child(data, relation['parent'], relation['child'], relation['attribute'])
        """
    source_code += f"""

        return "OK"

    def add(data, method='POST'):
        {dict_to_var_code}"""

    if with_upload:
        source_code += f"""
        temp_s3_keys = data.get('STARK_uploaded_s3_keys', {{}}) 
        STARK_uploaded_s3_keys = {{}}
        for key, items in temp_s3_keys.items():
            STARK_uploaded_s3_keys[key] = {{ 'S' : items }}
            copy_source = {{
                'Bucket': bucket_name,
                'Key': 'tmp/' + items,
            }}
            
            extra_args = {{
                'ACL': 'public-read'
            }}
            s3_res.meta.client.copy(copy_source, bucket_name, entity_upload_dir + items, extra_args)
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


        response = ddb.put_item(
            TableName=ddb_table,
            Item=item,
        )
        """
    if len(relationships) > 0:
        source_code += f"""
        if method == 'POST':
            data['orig_pk'] = pk

        for relation in relationships:
            cascade_pk_change_to_child(data, relation['parent'], relation['child'], relation['attribute'])
        """
    source_code += f"""
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

    def generate_reports(mapped_results = [], display_fields=[], report_params = {{}}): 
        diff_list = []
        master_fields = ['{pk}', """
    for col in columns:
        source_code += f"'{col}', "    
    source_code += f"""]
        if len(display_fields) > 0:
            csv_header = display_fields
            diff_list = list(set(master_fields) - set(display_fields))
        else:
            csv_header = master_fields

        report_list = []
        for key in mapped_results:
            temp_dict = {{}}
            #remove primary identifiers and STARK attributes
            key.pop("sk")"""

    if with_upload:
        source_code += f"""
            key.pop("STARK_uploaded_s3_keys")"""
    source_code += f"""
            for index, value in key.items():
                temp_dict[index.replace("_"," ")] = value
            report_list.append(temp_dict)

        file_buff = StringIO()
        writer = csv.DictWriter(file_buff, fieldnames=csv_header)
        writer.writeheader()
        for rows in report_list:
            for index in diff_list:
                rows.pop(index)
            writer.writerow(rows)
        filename = f"{{str(uuid.uuid4())}}"
        csv_file = f"{{filename}}.csv"
        pdf_file = f"{{filename}}.pdf"
        s3_action = s3.put_object(
            ACL='public-read',
            Body= file_buff.getvalue(),
            Bucket=bucket_name,
            Key='tmp/'+csv_file
        )

        prepare_pdf_data(report_list, csv_header, pdf_file, report_params)

        csv_bucket_key = bucket_tmp + csv_file
        pdf_bucket_key = bucket_tmp + pdf_file

        return csv_bucket_key, pdf_bucket_key

    def get_all_by_old_parent_value(old_pk_val, attribute, sk = default_sk):
    
        string_filter = " #Attribute = :old_parent_value"
        object_expression_value = {{':sk' : {{'S' : sk}},
                                    ':old_parent_value': {{'S' : old_pk_val}}}}
        ExpressionAttributeNamesDict = {{
            '#Attribute' : attribute,
        }}
        response = ddb.query(
            TableName=ddb_table,
            IndexName="STARK-ListView-Index",
            Select='ALL_ATTRIBUTES',
            ReturnConsumedCapacity='TOTAL',
            FilterExpression=string_filter,
            KeyConditionExpression='sk = :sk',
            ExpressionAttributeValues=object_expression_value,
            ExpressionAttributeNames=ExpressionAttributeNamesDict
        )
        raw = response.get('Items')
        items = []
        for record in raw:
            item = map_results(record)
            #add pk as literal 'pk' value
            #and STARK-ListView-Sk
            item['pk'] = record.get('pk', {{}}).get('S','')
            item['STARK-ListView-sk'] = record.get('STARK-ListView-sk',{{}}).get('S','')
            items.append(item)
        return items

    def prepare_pdf_data(data_to_tuple, master_fields, pdf_filename, report_params):
        #FIXME: PDF GENERATOR: can be outsourced to a layer, for refining 
        row_list = []
        for key in data_to_tuple:
            column_list = []
            for index in master_fields:
                column_list.append(key[index])
            row_list.append(tuple(column_list))

        header_tuple = tuple(master_fields) 
        data_tuple = tuple(row_list)
        
        pdf = utilities.create_pdf(header_tuple, data_tuple, report_params, pk_field)
        s3_action = s3.put_object(
            ACL='public-read',
            Body= pdf.output(),
            Bucket=bucket_name,
            Key='tmp/'+pdf_filename
        )


    def get_fields(fields, sk = default_sk):
            
        dd_arguments = {{}}
        next_token = 'initial'
        items = []
        while next_token != None:
            next_token = '' if next_token == 'initial' else next_token
            dd_arguments['TableName']=ddb_table
            dd_arguments['IndexName']="STARK-ListView-Index"
            dd_arguments['Limit']=5
            dd_arguments['ReturnConsumedCapacity']='TOTAL'
            dd_arguments['KeyConditionExpression']='sk = :sk'
            dd_arguments['ExpressionAttributeValues']={{
                ':sk' : {{'S' : sk}}
            }}

            if next_token != '':
                dd_arguments['ExclusiveStartKey']=next_token

            response = ddb.query(**dd_arguments)
            raw = response.get('Items')

            for record in raw:
                
                item = {{}}
                for field in fields:
                    if field == pk_field:
                        get_record = record.get('pk',{{}}).get('S','')
                    else:
                        get_record = record.get(field,{{}}).get('S','')
                        
                    item[field] = get_record
                items.append(item)
            #Get the "next" token, pass to calling function. This enables a "next page" request later.
            next_token = response.get('LastEvaluatedKey')

        return items
    """
    
    if len(relationships) > 0:
        source_code += f"""    
    def cascade_pk_change_to_child(params, parent_entity_name, child_entity_name, attribute):
        from os import getcwd 
        STARK_folder = getcwd() + f"/{{child_entity_name}}"
        sys.path = [STARK_folder] + sys.path

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