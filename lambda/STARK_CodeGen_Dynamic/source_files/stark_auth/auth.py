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

    #event must contain an array of permissions in event.get('stark_permissions', [])
    stark_permissions = payload.get('stark_permissions',[])

    print(stark_permissions)

    for permission in stark_permissions:
        if(stark_core.sec.is_authorized(permission, event, ddb)):
            print("permission: " + permission)
            stark_permissions[permission] = True
        else:
            stark_permissions[permission] = False

    return {
        "isBase64Encoded": False,
        "statusCode": responseStatusCode,
        "body": json.dumps(stark_permissions),
        "headers": {
            "Content-Type": "application/json",
        }
    }