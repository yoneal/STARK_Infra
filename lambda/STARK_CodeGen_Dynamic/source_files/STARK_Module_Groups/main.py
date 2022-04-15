#Python Standard Library
import base64
import json
from urllib.parse import unquote

#Extra modules
import boto3

ddb = boto3.client('dynamodb')

#######
#CONFIG
ddb_table   = "[[STARK_DDB_TABLE_NAME]]"
default_sk  = "STARK|module_group"
sort_fields = ["Group_Name", ]
page_limit  = 10

def lambda_handler(event, context):

    #Get request type
    request_type = event.get('queryStringParameters',{}).get('rt','')

    if request_type == '':
        ########################
        #Handle non-GET requests

        #Get specific request method
        method  = event.get('requestContext').get('http').get('method')

        if event.get('isBase64Encoded') == True :
            payload = json.loads(base64.b64decode(event.get('body'))).get('STARK_Module_Groups',"")
        else:    
            payload = json.loads(event.get('body')).get('STARK_Module_Groups',"")

        data    = {}

        if payload == "":
            return {
                "isBase64Encoded": False,
                "statusCode": 400,
                "body": json.dumps("Client payload missing"),
                "headers": {
                    "Content-Type": "application/json",
                }
            }
        else:
            data['pk'] = payload.get('Group_Name')
            data['orig_pk'] = payload.get('orig_Group_Name','')
            data['sk'] = payload.get('sk', '')
            if data['sk'] == "":
                data['sk'] = default_sk
            data['Description'] = payload.get('Description','')
            data['Icon'] = payload.get('Icon','')
            data['Priority'] = payload.get('Priority','')
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
            return {
                "isBase64Encoded": False,
                "statusCode": 400,
                "body": json.dumps("Could not handle API request"),
                "headers": {
                    "Content-Type": "application/json",
                }
            }

    else:
        ####################
        #Handle GET requests
        if request_type == "all":
            #check for submitted token
            lv_token = event.get('queryStringParameters',{}).get('nt', None)
            if lv_token != None:
                lv_token = unquote(lv_token)
                lv_token = json.loads(lv_token)

            items, next_token = get_all(default_sk, lv_token)

            response = {
                'Next_Token': json.dumps(next_token),
                'Items': items
            }

        elif request_type == "report":
            response = report(default_sk)

        elif request_type == "detail":

            pk = event.get('queryStringParameters').get('Group_Name','')
            sk = event.get('queryStringParameters').get('sk','')
            if sk == "":
                sk = default_sk

            response = get_by_pk(pk, sk)
        else:
            return {
                "isBase64Encoded": False,
                "statusCode": 400,
                "body": json.dumps("Could not handle GET request - unknown request type"),
                "headers": {
                    "Content-Type": "application/json",
                }
            }

    return {
        "isBase64Encoded": False,
        "statusCode": 200,
        "body": json.dumps(response),
        "headers": {
            "Content-Type": "application/json",
        }
    }

def report(sk):
    #FIXME: THIS IS A STUB, WILL NEED TO BE UPDATED WITH
    #   ENHANCED LISTVIEW LOGIC LATER WHEN WE ACTUALLY IMPLEMENT REPORTING

    response = ddb.query(
        TableName=ddb_table,
        IndexName="STARK-ListView-Index",
        Select='ALL_ATTRIBUTES',
        ReturnConsumedCapacity='TOTAL',
        KeyConditionExpression='sk = :sk',
        ExpressionAttributeValues={
            ':sk' : {'S' : sk}
        }
    )

    raw = response.get('Items')

    #Map to expected structure
    #FIXME: this is duplicated code, make this DRY by outsourcing the mapping to a different function.
    items = []
    for record in raw:
        item = {}
        item['Group_Name'] = record.get('pk', {}).get('S','')
        item['sk'] = record.get('sk',{}).get('S','')
        item['Description'] = record.get('Description',{}).get('S','')
        item['Icon'] = record.get('Icon',{}).get('S','')
        item['Priority'] = record.get('Priority',{}).get('N','')
        items.append(item)

    return items

def get_all(sk, lv_token=None):

    if lv_token == None:
        response = ddb.query(
            TableName=ddb_table,
            IndexName="STARK-ListView-Index",
            Select='ALL_ATTRIBUTES',
            Limit=page_limit,
            ReturnConsumedCapacity='TOTAL',
            KeyConditionExpression='sk = :sk',
            ExpressionAttributeValues={
                ':sk' : {'S' : sk}
            }
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
            ExpressionAttributeValues={
                ':sk' : {'S' : sk}
            }
        )

    raw = response.get('Items')

    #Map to expected structure
    #FIXME: this is duplicated code, make this DRY by outsourcing the mapping to a different function.
    items = []
    for record in raw:
        item = {}
        item['Group_Name'] = record.get('pk', {}).get('S','')
        item['sk'] = record.get('sk',{}).get('S','')
        item['Description'] = record.get('Description',{}).get('S','')
        item['Icon'] = record.get('Icon',{}).get('S','')
        item['Priority'] = record.get('Priority',{}).get('N','')
        items.append(item)

    #Get the "next" token, pass to calling function. This enables a "next page" request later.
    next_token = response.get('LastEvaluatedKey')

    return items, next_token

def get_by_pk(pk, sk):
    response = ddb.query(
        TableName=ddb_table,
        Select='ALL_ATTRIBUTES',
        KeyConditionExpression="#pk = :pk and #sk = :sk",
        ExpressionAttributeNames={
            '#pk' : 'pk',
            '#sk' : 'sk'
        },
        ExpressionAttributeValues={
            ':pk' : {'S' : pk },
            ':sk' : {'S' : sk }
        }
    )

    raw = response.get('Items')

    #Map to expected structure
    items = []
    for record in raw:
        item = {}
        item['Group_Name'] = record.get('pk', {}).get('S','')
        item['sk'] = record.get('sk',{}).get('S','')
        item['Description'] = record.get('Description',{}).get('S','')
        item['Icon'] = record.get('Icon',{}).get('S','')
        item['Priority'] = record.get('Priority',{}).get('N','')
        items.append(item)
    #FIXME: Mapping is duplicated code, make this DRY

    return items

def delete(data):
    pk = data.get('pk','')
    sk = data.get('sk','')

    response = ddb.delete_item(
        TableName=ddb_table,
        Key={
            'pk' : {'S' : pk},
            'sk' : {'S' : sk}
        }
    )

    return "OK"

def edit(data):                
    pk = data.get('pk', '')
    sk = data.get('sk', '')
    Description = str(data.get('Description', ''))
    Icon = str(data.get('Icon', ''))
    Priority = str(data.get('Priority', ''))

    UpdateExpressionString = "SET #Description = :Description, #Icon = :Icon, #Priority = :Priority" 
    ExpressionAttributeNamesDict = {
        '#Description' : 'Description',
        '#Icon' : 'Icon',
        '#Priority' : 'Priority',
    }
    ExpressionAttributeValuesDict = {
        ':Description' : {'S' : Description },
        ':Icon' : {'S' : Icon },
        ':Priority' : {'N' : Priority },
    }

    #If STARK-ListView-sk is part of the data payload, it should be added to the update expression
    if data.get('STARK-ListView-sk','') != '':
        UpdateExpressionString += ", #STARKListViewsk = :STARKListViewsk"
        ExpressionAttributeNamesDict['#STARKListViewsk']  = 'STARK-ListView-sk'
        ExpressionAttributeValuesDict[':STARKListViewsk'] = {'S' : data['STARK-ListView-sk']}

    response = ddb.update_item(
        TableName=ddb_table,
        Key={
            'pk' : {'S' : pk},
            'sk' : {'S' : sk}
        },
        UpdateExpression=UpdateExpressionString,
        ExpressionAttributeNames=ExpressionAttributeNamesDict,
        ExpressionAttributeValues=ExpressionAttributeValuesDict
    )

    return "OK"

def add(data):
    pk = data.get('pk', '')
    sk = data.get('sk', '')
    Description = str(data.get('Description', ''))
    Icon = str(data.get('Icon', ''))
    Priority = str(data.get('Priority', ''))

    item={}
    item['pk'] = {'S' : pk}
    item['sk'] = {'S' : sk}
    item['Description'] = {'S' : Description}
    item['Icon'] = {'S' : Icon}
    item['Priority'] = {'N' : Priority}

    if data.get('STARK-ListView-sk','') != '':
        item['STARK-ListView-sk'] = {'S' : data['STARK-ListView-sk']}

    response = ddb.put_item(
        TableName=ddb_table,
        Item=item,
    )

    return "OK"
