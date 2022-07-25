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

    source_code = f"""\
    #Python Standard Library
    import base64
    import json
    import sys
    import importlib
    from urllib.parse import unquote

    #Extra modules
    import boto3
    import csv
    import uuid
    from io import StringIO
    import os

    ddb = boto3.client('dynamodb')
    s3 = boto3.client("s3")

    #######
    #CONFIG
    ddb_table     = "{ddb_table_name}"
    pk_field      = "{pk_varname}"
    default_sk    = "{default_sk}"
    sort_fields   = ["{pk_varname}", ]
    bucket_name   = "{bucket_name}"
    relationships = {relationships}
    region_name   = os.environ['AWS_REGION']
    page_limit    = 10

    def lambda_handler(event, context):

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
                        temp_report_fields.append(index['field'])
                    for index, attributes in data.items():
                        if attributes['value'] != "":
                            if attributes['operator'] == "":
                                isInvalidPayload = True
                    data['STARK_report_fields'] = temp_report_fields
                    data['STARK_isReport'] = payload.get('STARK_isReport', False)

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
                response = delete(data)

            elif method == "PUT":

                #We can't update DDB PK, so if PK is different, we need to do ADD + DELETE
                if data['orig_pk'] == data['pk']:
                    response = edit(data)
                else:
                    response   = add(data, method)
                    data['pk'] = data['orig_pk']
                    response   = delete(data)

            elif method == "POST":
                if 'STARK_isReport' in data:
                    response = report(data, default_sk)
                else:
                    response = add(data)

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
            "statusCode": 200,
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
        for key, index in data.items():
            if key not in ["STARK_isReport", "STARK_report_fields"]:
                if index['value'] != "":
                    processed_operator_dict = (compose_operators(key, index)) 
                    temp_string_filter += processed_operator_dict['filter_string']
                    object_expression_value.update(processed_operator_dict['expression_values'])
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

        csv_filename = generate_csv(items, data['STARK_report_fields'])
        #Get the "next" token, pass to calling function. This enables a "next page" request later.
        next_token = response.get('LastEvaluatedKey')

        return items, next_token, csv_filename

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
        items = []
        for record in raw:
            items.append(map_results(record))

        return items

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
        {dict_to_var_code}

        UpdateExpressionString = "SET {update_expression}" 
        ExpressionAttributeNamesDict = {{"""

    for col in columns:
        col_varname = converter.convert_to_system_name(col)
        source_code +=f"""
            '#{col_varname}' : '{col_varname}',"""  
 
    source_code += f"""
            '#STARKListViewsk' : 'STARK-ListView-sk'
        }}
        ExpressionAttributeValuesDict = {{"""

    for col, col_type in columns.items():
        col_varname = converter.convert_to_system_name(col)
        col_type_id = set_type(col_type)

        source_code +=f"""
            ':{col_varname}' : {{'{col_type_id}' : {col_varname} }},"""  

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
        {dict_to_var_code}

        item={{}}
        item['pk'] = {{'S' : pk}}
        item['sk'] = {{'S' : sk}}"""

    for col, col_type in columns.items():
        col_varname = converter.convert_to_system_name(col)
        col_type_id = set_type(col_type)

        source_code +=f"""
        item['{col_varname}'] = {{'{col_type_id}' : {col_varname}}}"""

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
    
    def compose_operators(key, data):
        composed_filter_dict = {{"filter_string":"","expression_values": {{}}}}
        if data['operator'] == "IN":
            string_split = data['value'].split(',')
            composed_filter_dict['filter_string'] += f" {{key}} IN "
            temp_in_string = ""
            in_string = ""
            in_counter = 1
            for in_index in string_split:
                in_string += f" :inParam{{in_counter}}, "
                composed_filter_dict['expression_values'][f":inParam{{in_counter}}"] = {{data['type'] : in_index.strip()}}
                in_counter += 1
            temp_in_string = in_string[1:-2]
            composed_filter_dict['filter_string'] += f"({{temp_in_string}}) AND"
        elif data['operator'] in [ "contains", "begins_with" ]:
            composed_filter_dict['filter_string'] += f" {{data['operator']}}({{key}}, :{{key}}) AND"
            composed_filter_dict['expression_values'][f":{{key}}"] = {{data['type'] : data['value'].strip()}}
        elif data['operator'] == "between":
            from_to_split = data['value'].split(',')
            composed_filter_dict['filter_string'] += f" ({{key}} BETWEEN :from{{key}} AND :to{{key}}) AND"
            composed_filter_dict['expression_values'][f":from{{key}}"] = {{data['type'] : from_to_split[0].strip()}}
            composed_filter_dict['expression_values'][f":to{{key}}"] = {{data['type'] : from_to_split[1].strip()}}
        else:
            composed_filter_dict['filter_string'] += f" {{key}} {{data['operator']}} :{{key}} AND"
            composed_filter_dict['expression_values'][f":{{key}}"] = {{data['type'] : data['value'].strip()}}

        return composed_filter_dict

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

    source_code += f"""
        return item

    def generate_csv(mapped_results = [], display_fields=[]): 
        diff_list = []
        master_fields = ['{pk_varname}', """
    for col in columns:
        col_varname = converter.convert_to_system_name(col)
        source_code += f"'{col_varname}', "    
    source_code += f"""]
        if len(display_fields) > 0:
            csv_header = display_fields
            diff_list = list(set(master_fields) - set(display_fields))
        else:
            csv_header = master_fields

        file_buff = StringIO()
        writer = csv.DictWriter(file_buff, fieldnames=csv_header)
        writer.writeheader()
        for rows in mapped_results:
            rows.pop("sk")
            for index in diff_list:
                rows.pop(index)
            writer.writerow(rows)
        filename = f"{{str(uuid.uuid4())}}.csv"
        test = s3.put_object(
            ACL='public-read',
            Body= file_buff.getvalue(),
            Bucket=bucket_name,
            Key='tmp/'+filename
        )
        
        return bucket_name+".s3."+ region_name + ".amazonaws.com/tmp/" +filename

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