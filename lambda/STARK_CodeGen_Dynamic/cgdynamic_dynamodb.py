#STARK Code Generator component.
#Produces the customized dynamic content for a STARK system

#Python Standard Library
import base64
import textwrap

def create(data):
  
    pk             = data["PK"]
    entity         = data["Entity"]
    columns        = data["Columns"]
    ddb_table_name = data["DynamoDB Name"]

    #Convert human-friendly names to variable-friendly names
    entity_varname = entity.replace(" ", "_").lower()
    pk_varname     = entity.replace(" ", "_").lower()

    default_sk     = entity + "|info"
 
    #Create the column dict we'll use in the code as a declaration
    col_dict = '{ "pk": pk, "sk": sk, '
    for col in columns:
        col_varname = col.replace(" ", "_").lower()
        col_dict += f'"{col_varname}": {col_varname}, '
    col_dict = col_dict[:-2]
    col_dict += ' }'

    #Create the dict value retrieval code for the add/edit function body
    dict_to_var_code = f"""pk = data.get('pk', '')
        sk = data.get('sk', '')"""
    for col in columns:
        col_varname = col.replace(" ", "_").lower()
        dict_to_var_code += f"""
        {col_varname} = str(data.get('{col_varname}', ''))"""

    #This is for our DDB update call
    update_expression = ""
    for col in columns:
        col_varname = col.replace(" ", "_").lower()
        update_expression += f"""#{col_varname} = :{col_varname}, """
    update_expression = update_expression[:-2]

    source_code = f"""\
    #Python Standard Library
    import base64
    import json

    #Extra modules
    import boto3

    ddb = boto3.client('dynamodb')

    #######
    #CONFIG
    ddb_table  = "{ddb_table_name}"
    default_sk = "{default_sk}"

    def lambda_handler(event, context):

        #Get request type
        request_type = event.get('queryStringParameters',{{}}).get('rt','')

        if request_type == '':
            ########################
            #Handle non-GET requests
    
            #Get specific request method
            method  = event.get('requestContext').get('http').get('method')
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
        col_varname = col.replace(" ", "_").lower()
        source_code +=f"""
                data['{col_varname}'] = payload.get('{col_varname}','')"""

    source_code +=f"""

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
                response = get_all(default_sk)

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

    def get_all(sk):
        response = ddb.scan(
            TableName=ddb_table,
            Select='ALL_ATTRIBUTES',
            ReturnConsumedCapacity='TOTAL',
            FilterExpression='#sk = :sk',
            ExpressionAttributeNames={{
                '#sk' : 'sk'
            }},
            ExpressionAttributeValues={{
                ':sk' : {{'S' : sk}}
            }}
        )

        raw = response.get('Items')

        #Map to expected structure
        #FIXME: this is duplicated code, make this DRY by outsourcing the mapping to a different function.
        items = []
        for record in raw:
            item = {{'{pk_varname}': record['pk']['S'],
                    'sk': record['sk']['S'],"""

    for col, col_type in columns.items():
        col_varname = col.replace(" ", "_").lower()
        col_type_id = set_type(col_type)

        source_code +=f"""
                    '{col_varname}': record['{col_varname}']['{col_type_id}'],"""


    source_code +=f"""}}
            items.append(item)

        #Sort: this can be transformed to an actual sorting function instead of lambda (Python lambda, not AWS lambda)
        #   to allow for sorting features like choosing which column to sort on, or applying complex sort logic that involves two or more cols.
        items = sorted(items, key=lambda item: item['{pk_varname}'])

        return items

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
            item = {{'{pk_varname}': record['pk']['S'],
                    'sk': record['sk']['S'],"""

    for col, col_type in columns.items():
        col_varname = col.replace(" ", "_").lower()
        col_type_id = set_type(col_type)

        source_code +=f"""
                    '{col_varname}': record['{col_varname}']['{col_type_id}'],"""


    source_code += f"""}}
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

        response = ddb.update_item(
            TableName=ddb_table,
            Key={{
                'pk' : {{'S' : pk}},
                'sk' : {{'S' : sk}}
            }},
            UpdateExpression="SET {update_expression}",
            ExpressionAttributeNames={{"""

    for col in columns:
        col_varname = col.replace(" ", "_").lower()
        source_code +=f"""
                '#{col_varname}' : '{col_varname}',"""  

    source_code += f"""
            }},
            ExpressionAttributeValues={{"""

    for col, col_type in columns.items():
        col_varname = col.replace(" ", "_").lower()
        col_type_id = set_type(col_type)

        source_code +=f"""
                ':{col_varname}' : {{'{col_type_id}' : {col_varname} }},"""  

    source_code += f"""
            }}
        )

        return "OK"

    def add(data):
        {dict_to_var_code}

        item={{}}
        item['pk'] = {{'S' : pk}}
        item['sk'] = {{'S' : sk}}"""

    for col, col_type in columns.items():
        col_varname = col.replace(" ", "_").lower()
        col_type_id = set_type(col_type)

        source_code +=f"""
        item['{col_varname}'] = {{'{col_type_id}' : {col_varname}}}"""

    source_code += f"""
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
        if col_type["type"] == "int-spinner" or col_type["type"] == "decimal-spinner":
            col_type_id = 'N'
    
    elif col_type == "int" or col_type == "number":
        col_type_id = 'N'

    return col_type_id