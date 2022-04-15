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
default_sk  = "STARK|module"
sort_fields = ["Module_Name", ]
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
            payload = json.loads(base64.b64decode(event.get('body'))).get('STARK_Module',"")
        else:    
            payload = json.loads(event.get('body')).get('STARK_Module',"")

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
            data['pk'] = payload.get('Module_Name')
            data['orig_pk'] = payload.get('orig_Module_Name','')
            data['sk'] = payload.get('sk', '')
            if data['sk'] == "":
                data['sk'] = default_sk
            data['Descriptive_Title'] = payload.get('Descriptive_Title','')
            data['Target'] = payload.get('Target','')
            data['Description'] = payload.get('Description','')
            data['Module_Group'] = payload.get('Module_Group','')
            data['Is_Menu_Item'] = payload.get('Is_Menu_Item','')
            data['Is_Enabled'] = payload.get('Is_Enabled','')
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

            pk = event.get('queryStringParameters').get('Module_Name','')
            sk = event.get('queryStringParameters').get('sk','')
            if sk == "":
                sk = default_sk

            response = get_by_pk(pk, sk)

        elif request_type == "usermodules":
            #FIXME: Getting the username should be a STARK Core framework utility. Only here for now for MVP implem, to not hold up more urgent dependent features
            #FIXME: When framework-ized, getting the requestContext should be at the beginning of the handler, and will exit if handler needs the Username and is not present (i.e., not properly authorized)
            #FIXME: Make sure for this framework-ized implementation that it will still work when Framework components call each other directly through the STARK registry instead of through API Gateway.
            username = event.get('requestContext', {}).get('authorizer', {}).get('lambda', {}).get('Username','')
            response = get_user_modules(default_sk, username)

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
        item['Module_Name'] = record.get('pk', {}).get('S','')
        item['sk'] = record.get('sk',{}).get('S','')
        item['Descriptive_Title'] = record.get('Descriptive_Title',{}).get('S','')
        item['Target'] = record.get('Target',{}).get('S','')
        item['Description'] = record.get('Description',{}).get('S','')
        item['Module_Group'] = record.get('Module_Group',{}).get('S','')
        item['Is_Menu_Item'] = record.get('Is_Menu_Item',{}).get('BOOL','')
        item['Is_Enabled'] = record.get('Is_Enabled',{}).get('BOOL','')
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
        item['Module_Name'] = record.get('pk', {}).get('S','')
        item['sk'] = record.get('sk',{}).get('S','')
        item['Descriptive_Title'] = record.get('Descriptive_Title',{}).get('S','')
        item['Target'] = record.get('Target',{}).get('S','')
        item['Description'] = record.get('Description',{}).get('S','')
        item['Module_Group'] = record.get('Module_Group',{}).get('S','')
        item['Is_Menu_Item'] = record.get('Is_Menu_Item',{}).get('BOOL','')
        item['Is_Enabled'] = record.get('Is_Enabled',{}).get('BOOL','')
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
        item['Module_Name'] = record.get('pk', {}).get('S','')
        item['sk'] = record.get('sk',{}).get('S','')
        item['Descriptive_Title'] = record.get('Descriptive_Title',{}).get('S','')
        item['Target'] = record.get('Target',{}).get('S','')
        item['Description'] = record.get('Description',{}).get('S','')
        item['Module_Group'] = record.get('Module_Group',{}).get('S','')
        item['Is_Menu_Item'] = record.get('Is_Menu_Item',{}).get('BOOL','')
        item['Is_Enabled'] = record.get('Is_Enabled',{}).get('BOOL','')
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
    Descriptive_Title = str(data.get('Descriptive_Title', ''))
    Target = str(data.get('Target', ''))
    Description = str(data.get('Description', ''))
    Module_Group = str(data.get('Module_Group', ''))
    Is_Menu_Item = str(data.get('Is_Menu_Item', ''))
    Is_Enabled = str(data.get('Is_Enabled', ''))
    Icon = str(data.get('Icon', ''))
    Priority = str(data.get('Priority', ''))

    if Is_Menu_Item == 'Y':
        Is_Menu_Item = True
    else:
        Is_Menu_Item = False
    Is_Enabled = str(data.get('Is_Enabled', ''))
    if Is_Enabled == 'Y':
        Is_Enabled = True
    else:
        Is_Enabled = False

    UpdateExpressionString = "SET #Descriptive_Title = :Descriptive_Title, #Target = :Target, #Description = :Description, #Module_Group = :Module_Group, #Is_Menu_Item = :Is_Menu_Item, #Is_Enabled = :Is_Enabled, #Icon = :Icon, #Priority = :Priority" 
    ExpressionAttributeNamesDict = {
        '#Descriptive_Title' : 'Descriptive_Title',
        '#Target' : 'Target',
        '#Description' : 'Description',
        '#Module_Group' : 'Module_Group',
        '#Is_Menu_Item' : 'Is_Menu_Item',
        '#Is_Enabled' : 'Is_Enabled',
        '#Icon' : 'Icon',
        '#Priority' : 'Priority',
    }
    ExpressionAttributeValuesDict = {
        ':Descriptive_Title' : {'S' : Descriptive_Title },
        ':Target' : {'S' : Target },
        ':Description' : {'S' : Description },
        ':Module_Group' : {'S' : Module_Group },
        ':Is_Menu_Item' : {'BOOL' : Is_Menu_Item },
        ':Is_Enabled' : {'BOOL' : Is_Enabled },
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
    Descriptive_Title = str(data.get('Descriptive_Title', ''))
    Target = str(data.get('Target', ''))
    Description = str(data.get('Description', ''))
    Module_Group = str(data.get('Module_Group', ''))
    Is_Menu_Item = str(data.get('Is_Menu_Item', ''))
    Icon = str(data.get('Icon', ''))
    Priority = int(data.get('Priority', ''))

    if Is_Menu_Item == 'Y':
        Is_Menu_Item = True
    else:
        Is_Menu_Item = False
    Is_Enabled = str(data.get('Is_Enabled', ''))
    if Is_Enabled == 'Y':
        Is_Enabled = True
    else:
        Is_Enabled = False


    item={}
    item['pk'] = {'S' : pk}
    item['sk'] = {'S' : sk}
    item['Descriptive_Title'] = {'S' : Descriptive_Title}
    item['Target'] = {'S' : Target}
    item['Description'] = {'S' : Description}
    item['Module_Group'] = {'S' : Module_Group}
    item['Is_Menu_Item'] = {'BOOL' : Is_Menu_Item}
    item['Is_Enabled'] = {'BOOL' : Is_Enabled}
    item['Icon'] = {'S' : Icon}
    item['Priority'] = {'N' : Priority}

    if data.get('STARK-ListView-sk','') != '':
        item['STARK-ListView-sk'] = {'S' : data['STARK-ListView-sk']}

    response = ddb.put_item(
        TableName=ddb_table,
        Item=item,
    )

    return "OK"

def get_user_modules(sk, username):
    ########################
    #1.GET USER PERMISSIONS
    #FIXME: Getting user permissions should be a STARK Core framework utility, only here for now for urgent MVP implementation,
    #       to not hold up related features that need implementation ASAP
    response = ddb.query(
        TableName=ddb_table,
        Select='ALL_ATTRIBUTES',
        ReturnConsumedCapacity='TOTAL',
        KeyConditionExpression='pk = :pk and sk = :sk',
        ExpressionAttributeValues={
            ':pk' : {'S' : username},
            ':sk' : {'S' : "STARK|user|permissions"}
        }
    )

    raw = response.get('Items')
    permission_string = ''    
    for record in raw:
        permission_string = record.get('Permissions',{}).get('S','')
    
    #Split permission_string by the delimeter (comma+space / ", ")
    permissions_list = permission_string.split(", ")

    ##################################
    #GET SYSTEM MODULES (ENABLED ONLY)
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

    items = []
    for record in raw:
        # item = {}
        # item['Module_Name'] = record.get('pk', {}).get('S','')
        # item['sk'] = record.get('sk',{}).get('S','')
        # item['Descriptive_Title'] = record.get('Descriptive_Title',{}).get('S','')
        # item['Target'] = record.get('Target',{}).get('S','')
        # item['Description'] = record.get('Description',{}).get('S','')
        # item['Module_Group'] = record.get('Module_Group',{}).get('S','')
        # item['Is_Menu_Item'] = record.get('Is_Menu_Item',{}).get('S','')
        # item['Is_Enabled'] = record.get('Is_Enabled',{}).get('S','')
        # item['Icon'] = record.get('Icon',{}).get('S','')
        # item['Priority'] = record.get('Priority',{}).get('N','')

        #FIXME: If the mapping code above has become DRY, this code should probably be refactored
        #   so that it makes use of the mapping code abstraction results. (i.e., trigger mapping code, then assign values here
        #   using the friendlier reference instead of "record.get...")

        if record.get('Is_Enabled',{}).get('BOOL','') == True:
            if record.get('Is_Menu_Item',{}).get('BOOL','') == True:
                if record.get('pk', {}).get('S','') in permissions_list:
                    #Only modules that are ENABLED, are MENU ITEMS, and are found in the user's permissions list are registered
                    item = {}
                    item['title'] = record.get('Descriptive_Title',{}).get('S','')
                    item['image'] = record.get('Icon',{}).get('S','')
                    #item['image_alt'] = record.get #FIXME: This isn't in the system modules model, because it wasn't in Cobalt as well... add please.
                    item['href'] = record.get('Target',{}).get('S','')
                    item['group'] = record.get('Module_Group',{}).get('S','')
                    item['priority'] = record.get('Priority',{}).get('N','')
                    items.append(item)


    return items