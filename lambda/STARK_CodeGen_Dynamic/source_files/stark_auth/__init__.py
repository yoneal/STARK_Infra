#Python Standard Library
import json
import base64

#Extra modules
import boto3

import stark_core

ddb = boto3.client('dynamodb')

#######
#CONFIG
ddb_table  = stark_core.ddb_table

def lambda_handler(event, context):

    responseStatusCode = 200

    if event.get('isBase64Encoded') == True :
        payload = json.loads(base64.b64decode(event.get('body')))
    else:    
        payload = json.loads(event.get('body'))

    request_type = payload.get('rt','')
    if request_type == '':
        #Default request: Asking for user permissions check
        #event must contain an array of permissions in payload.get('stark_permissions', [])
        permissions = payload.get('stark_permissions',[])

        stark_permissions = {}
        for permission in permissions:
            print(permission)
            stark_permissions[permission] = stark_core.sec.is_authorized(permission, event, ddb)

        return {
            "isBase64Encoded": False,
            "statusCode": responseStatusCode,
            "body": json.dumps(stark_permissions),
            "headers": {
                "Content-Type": "application/json",
            }
        }
    else:
        if request_type == 's3':
            #FIXME: Make sure only logged in and legitimate users can get here
        
            #Query for our creds
            response = ddb.query(
                TableName=ddb_table,
                Select='ALL_ATTRIBUTES',
                KeyConditionExpression="pk = :pk",
                ExpressionAttributeValues={
                    ':pk' : {'S' : "STARK|AccessKey|S3"}
                }
            )

            raw = response.get('Items')

            items = []
            for record in raw:
                item = {}
                item['access_key_id'] = record.get('sk',{}).get('S','')
                item['secret_access_key'] = record.get('key',{}).get('S','')
                items.append(item)

            return {
                "isBase64Encoded": False,
                "statusCode": responseStatusCode,
                "body": json.dumps(items),
                "headers": {
                    "Content-Type": "application/json",
                }
            }

