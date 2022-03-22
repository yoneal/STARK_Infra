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
        sk = data.get('sk', '')"""
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
    update_expression = update_expression[:-2]

    source_code = f"""\
    #Python Standard Library
    import base64
    import json
    from urllib.parse import unquote

    #Extra modules
    import boto3

    ddb = boto3.client('dynamodb')

    #######
    #CONFIG
    ddb_table   = "{ddb_table_name}"
    default_sk  = "{default_sk}"
    sort_fields = ["{pk_varname}", ]
    page_limit  = 10

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
                data['pk'] = payload.get('{pk_varname}')
                data['orig_pk'] = payload.get('orig_{pk_varname}','')
                data['sk'] = payload.get('sk', '')
                if data['sk'] == "":
                    data['sk'] = default_sk"""

    for col, col_type in columns.items():
        col_varname = converter.convert_to_system_name(col)
        source_code +=f"""
                data['{col_varname}'] = payload.get('{col_varname}','')"""

    source_code +=f"""
            ListView_index_values = []
            for field in sort_fields:
                ListView_index_values.append(payload.get(field))
            data['STARK-ListView-sk'] = "|".join(ListView_index_values)

            if method == "DELETE":
                response = delete(data)

            elif method == "PUT":

                #We can't update DDB PK, so if PK is different, we need to do ADD + DELETE
                if data['orig_pk'] == data['pk']:
                    response = edit(data)
                else:
                    response   = add(data)
                    data['pk'] = data['orig_pk']
                    response   = delete(data)

            elif method == "POST":
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

            elif request_type == "report":
                response = report(default_sk)

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

    def report(sk):
        #FIXME: THIS IS A STUB, WILL NEED TO BE UPDATED WITH
        #   ENHANCED LISTVIEW LOGIC LATER WHEN WE ACTUALLY IMPLEMENT REPORTING

        response = ddb.query(
            TableName=ddb_table,
            IndexName="STARK-ListView-Index",
            Select='ALL_ATTRIBUTES',
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
            item = {{}}
            item['{pk_varname}'] = record.get('pk', {{}}).get('S','')
            item['sk'] = record.get('sk',{{}}).get('S','')"""
    for col, col_type in columns.items():
        col_varname = converter.convert_to_system_name(col)
        col_type_id = set_type(col_type)

        source_code +=f"""
            item['{col_varname}'] = record.get('{col_varname}',{{}}).get('{col_type_id}','')"""

    source_code += f"""
            items.append(item)

        #Get the "next" token, pass to calling function. This enables a "next page" request later.
        next_token = response.get('LastEvaluatedKey')

        return items, next_token

    def get_all(sk, lv_token=None):

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
            item = {{}}
            item['{pk_varname}'] = record.get('pk', {{}}).get('S','')
            item['sk'] = record.get('sk',{{}}).get('S','')"""
    for col, col_type in columns.items():
        col_varname = converter.convert_to_system_name(col)
        col_type_id = set_type(col_type)

        source_code +=f"""
            item['{col_varname}'] = record.get('{col_varname}',{{}}).get('{col_type_id}','')"""

    source_code += f"""
            items.append(item)

        #Get the "next" token, pass to calling function. This enables a "next page" request later.
        next_token = response.get('LastEvaluatedKey')

        return items, next_token

    def get_by_pk(pk, sk):
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
            item = {{}}
            item['{pk_varname}'] = record.get('pk', {{}}).get('S','')
            item['sk'] = record.get('sk',{{}}).get('S','')"""
    for col, col_type in columns.items():
        col_varname = converter.convert_to_system_name(col)
        col_type_id = set_type(col_type)

        source_code +=f"""
            item['{col_varname}'] = record.get('{col_varname}',{{}}).get('{col_type_id}','')"""

    source_code += f"""
            items.append(item)
        #FIXME: Mapping is duplicated code, make this DRY

        return items

    def delete(data):
        pk = data.get('pk','')
        sk = data.get('sk','')

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
        }}
        ExpressionAttributeValuesDict = {{"""

    for col, col_type in columns.items():
        col_varname = converter.convert_to_system_name(col)
        col_type_id = set_type(col_type)

        source_code +=f"""
            ':{col_varname}' : {{'{col_type_id}' : {col_varname} }},"""  

    source_code += f"""
        }}

        #If STARK-ListView-sk is part of the data payload, it should be added to the update expression
        if data.get('STARK-ListView-sk','') != '':
            UpdateExpressionString += ", #STARKListViewsk = :STARKListViewsk"
            ExpressionAttributeNamesDict['#STARKListViewsk']  = 'STARK-ListView-sk'
            ExpressionAttributeValuesDict[':STARKListViewsk'] = {{'S' : data['STARK-ListView-sk']}}

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

        return "OK"

    def add(data):
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

        if data.get('STARK-ListView-sk','') != '':
            item['STARK-ListView-sk'] = {{'S' : data['STARK-ListView-sk']}}

        response = ddb.put_item(
            TableName=ddb_table,
            Item=item,
        )

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