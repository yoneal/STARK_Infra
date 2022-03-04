#STARK Code Generator component.
#Produces the customized dynamic content for a STARK system

#Python Standard Library
import base64
import textwrap

#Private modules
import convert_friendly_to_system as converter

def create(data):
  
    ddb_table_name = data["DynamoDB Name"]

    source_code = f"""\
    #Python Standard Library
    import base64
    import datetime
    import json

    #Extra modules
    import boto3

    ddb = boto3.client('dynamodb')

    #######
    #CONFIG
    ddb_table  = "{ddb_table_name}"

    def lambda_handler(event, context):

        #Get cookies, if any
        eventCookies = event.get('cookies', {{}})
        cookies = {{}}
        for cookie in eventCookies:
            info = cookie.partition("=")
            cookies[info[0]] = info[2]
 
        method  = event.get('requestContext').get('http').get('method')
        headers = {{"Content-Type": "application/json",}}

        if method == "POST":
            if cookies.get('sessid','') != '':
                response = logout(cookies['sessid'])
                print("Logged out")
                print(response)
                #Send cookie back, this time with past date, to ask client to delete it
                headers['Set-Cookie'] = f"sessid={{cookies['sessid']}}; Path=/; HttpOnly; Secure; SameSite=None; Max-Age=0; Domain=.amazonaws.com"
                return {{
                    "isBase64Encoded": False,
                    "statusCode": 200,
                    "body": json.dumps("Logged out"),
                    "headers": headers
                }}
        else:
            return {{
                "isBase64Encoded": False,
                "statusCode": 400,
                "body": json.dumps("Could not handle API request"),
                "headers": headers
            }}

        return {{
            "isBase64Encoded": False,
            "statusCode": 200,
            "body": json.dumps(response),
            "headers": headers
        }}

    def logout(sess_id):
        #Delete session information
        key       = {{}}
        key['pk'] = {{'S' : sess_id}}
        key['sk'] = {{'S' : "STARK|session"}}
        response = ddb.delete_item(
            TableName=ddb_table,
            Key=key
        )
        
        return response
    """

    return textwrap.dedent(source_code)
