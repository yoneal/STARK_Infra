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
    import secrets

    #Extra modules
    import boto3
    import bcrypt

    ddb = boto3.client('dynamodb')

    #######
    #CONFIG
    ddb_table  = "{ddb_table_name}"

    def lambda_handler(event, context):

        #Get cookies, if any
        eventCookies = event.get('cookies')
        cookies = {{}}
        for cookie in eventCookies:
            info = cookie.partition("=")
            cookies[info[0]] = info[2]
 
        method  = event.get('requestContext').get('http').get('method')
        payload = json.loads(event.get('body')).get('Login',"")
        data    = {{}}
        headers = {{"Content-Type": "application/json",}}
        
        if payload == "":
            #If payload is blank and there's a session ID cookie, this means this is a logout request.
            #Else, it's a malformed request.
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
                    "body": json.dumps("Client payload missing"),
                    "headers": headers
                }}
        else:
            data['username'] = payload.get('username','')
            data['password'] = payload.get('password','')

        if method == "POST":
            sess_id = validate(data)

            if sess_id == False:
                #Auth failure
                response={{"message": "AuthFailure"}}
            else:
                headers['Set-Cookie'] = f"sessid={{sess_id}}; Path=/; HttpOnly; Secure; SameSite=None; Max-Age=43200; Domain=.amazonaws.com"
                response={{
                    "message": "AuthSuccess"
                }}
                #This should also be where bearer token is sent back when bearer token support is implemented

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

    def validate(data):
        username = data['username']
        password = data['password']
        failure  = True
        #Our default password hashing algo is Bcrypt, so the steps here are:
        #   1. Get `PasswordHash` from `User` record for `username`
        #       `Password_Hash` already contains algo (just bcrypt), salt and work factor
        #   2. We verify that the submitted `password` is the original one by calling verify(`password`, `Password_Hash`)
        #       That verify() call will use the algo/salt/work factor info to hash `password`. 
        #       If the result is the same as `Password_Hash`, then we know it is the correct plaintext password.
        #   3. Otherwise, we will return a login failure message.
        #       This same failure message will also handle the case where the `username` submitted is not in our records.


        #1. Get `Password_Hash`
        response = ddb.query(
            TableName=ddb_table,
            Select='ALL_ATTRIBUTES',
            KeyConditionExpression="#pk = :pk and #sk = :sk",
            ExpressionAttributeNames={{
                '#pk' : 'pk',
                '#sk' : 'sk'
            }},
            ExpressionAttributeValues={{
                ':pk' : {{'S' : username }},
                ':sk' : {{'S' : 'user|info' }}
            }}
        )
        raw = response.get('Items')
        for record in raw:
            #We can set `failure` to False if we get inside this loop - this means the user is in our records
            failure       = False
            password_hash = record['Password_Hash']['S']

        #2. Verify hash
        if failure == False:
            if bcrypt.checkpw(password.encode(), password_hash.encode()):
                #This means the user exists, and the password was verified.
                
                #FIXME
                #Stuff to do
                #1. Generate session id token
                sess_id = secrets.token_urlsafe(16)
                #This should also be where bearer token is created when bearer token support is implemented


                #2. Create USER SESSION, with token in it
                dt_now             = datetime.datetime.now()
                dt_p12             = dt_now + datetime.timedelta(hours=12)
                item               = {{}}
                item['pk']         = {{'S' : sess_id}}
                item['sk']         = {{'S' : "sess|info"}}
                item['TTL']        = {{'S' : str(dt_p12)}}
                item['sess_start'] = {{'S' : str(dt_now)}}
                response = ddb.put_item(
                    TableName=ddb_table,
                    Item=item,
                )
                #FIXME: embed permissions in session as well? (Tentative design)

                

                #3. Return token (and session ID?) to client for cookie creating purposes

                return sess_id
            else:
                failure = True


        #3: If `failure` is True, whether due to non-existent user or wrong password, handle here
        if failure == True:
            return False

    def logout(sess_id):
        #Delete session information
        key       = {{}}
        key['pk'] = {{'S' : sess_id}}
        key['sk'] = {{'S' : "sess|info"}}
        response = ddb.delete_item(
            TableName=ddb_table,
            Key=key
        )
        
        return response
    """

    return textwrap.dedent(source_code)
