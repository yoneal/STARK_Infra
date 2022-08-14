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
    import stark_scrypt as scrypt

    #STARK
    import stark_core

    ddb = boto3.client('dynamodb')

    #######
    #CONFIG
    ddb_table = stark_core.ddb_table

    def lambda_handler(event, context):

        #Get cookies, if any
        eventCookies = event.get('cookies', {{}})
        cookies = {{}}
        for cookie in eventCookies:
            info = cookie.partition("=")
            cookies[info[0]] = info[2]
 
        method  = event.get('requestContext').get('http').get('method')

        if event.get('isBase64Encoded') == True :
            print("[INFO] b64decode payload...")
            payload = json.loads(base64.b64decode(event.get('body'))).get('Login',"")
        else:    
            payload = json.loads(event.get('body')).get('Login',"")


        data    = {{}}
        headers = {{"Content-Type": "application/json",}}
        
        if payload == "":
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
                headers['Set-Cookie'] = f"sessid={{sess_id}}; Path=/; HttpOnly; Secure; SameSite=None; Max-Age=43200"
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
                ':sk' : {{'S' : 'STARK|user|info' }}
            }}
        )
        raw = response.get('Items')
        for record in raw:
            #We can set `failure` to False if we get inside this loop - this means the user is in our records
            failure       = False
            password_hash = record['Password_Hash']['S']

        #2. Verify hash
        if failure == False:
            if scrypt.validate(password, password_hash):
                #This means the user exists, and the password was verified.
                
                #FIXME
                #Stuff to do
                #1. Generate session id token
                sess_id = secrets.token_urlsafe(16)
                #This should also be where bearer token is created when bearer token support is implemented

                #2. Create USER SESSION, with token in it
                dt_now             = datetime.datetime.now()
                ttl_datetime       = dt_now + datetime.timedelta(hours=12)
                ttl_timestamp      = int(ttl_datetime.timestamp()) #int cast to remove microseconds
                item               = {{}}
                item['pk']         = {{'S' : sess_id}}
                item['sk']         = {{'S' : "STARK|session"}}
                item['TTL']        = {{'N' : str(ttl_timestamp)}}
                item['Sess_Start'] = {{'S' : str(dt_now)}}
                item['Username']   = {{'S' : username}}

                #This special attribute makes the record show up in the GSI "STARK-ListView-Index",
                item['STARK-ListView-sk'] = {{'S' : username}}

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
    """
    return textwrap.dedent(source_code)
