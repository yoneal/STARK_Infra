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

    ddb = boto3.client('dynamodb')

    #######
    #CONFIG
    ddb_table = "{ddb_table_name}"

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

    scrypt_lib = f"""\
    #Scrypt password hashing and validation for STARK default use
    import base64
    import hashlib
    import secrets

    def create_hash(password, n=16, r=8, p=1, b64salt="", salt_len=16):
        cpu_cost = 2**n
        blk_size = r
        parallel = p
        dklen    = 32
        
        if b64salt == "":
            b64salt = secrets.token_urlsafe(salt_len).replace('=','')

        salt = b64salt.encode('utf-8')

        password = password.encode('utf-8)')
        raw_hash = hashlib.scrypt(password, salt=salt, n=cpu_cost, r=blk_size, p=parallel, dklen=dklen, maxmem=(cpu_cost * blk_size * parallel * 128 * 2) )
        b64hash  = base64.b64encode(raw_hash).decode('utf-8').replace("=","")

        #Pattern to follow (taken from Passlib / PHC format):
        #     $scrypt$ln=8,r=8,p=1$WKs1xljLudd6z9kbY0wpJQ$yCR4iDZYDKv+iEJj6yHY0lv/epnfB6f/w1EbXrsJOuQ
        #                65536$8$1$c+Ec8UtUKHU$67e45dcd585c11d75d82f4b5abbad167c3dee1f9033bab63db8365ea24c77c22
        #       Notes:
        #       - Main sections separated by $
        #       - Section 1: algo identifier ("scrypt")
        #       - Section 2: all three scrypt settings, separated by commas ("ln=8,r=8,p=1")
        #               - Note: ln (linear rounds) is cpu cost, but instead if the eventual value, it is the exponent of 2 (i.e., instead of writing cpu_cost=65536, you write ln=16 (65536 = 2^16), which is the Passlib default cost/ln)
        #       - Section 3: the salt, 16 bytes (Passlib default), in base64 ("WKs1xljLudd6z9kbY0wpJQ")
        #       - Section 4: password hash, in base64 (yCR4iDZYDKv+iEJj6yHY0lv/epnfB6f/w1EbXrsJOuQ")
        scrypt_hash = f"$scrypt$n={{n}},r={{r}},p={{p}}${{b64salt}}${{b64hash}}$"

        return scrypt_hash
        
    def validate(password, existing_hash):
        #Get settings from `hash` - call our parse_hash function
        settings = parse_hash(existing_hash)

        if(settings == "INVALID HASH"):
            print ("Logging validation failure: User has invalid existing password hash in user records")
            return False

        n      = settings["n"]
        r      = settings["r"]
        p      = settings["p"]
        salt   = settings["salt"]
        
        new_hash = create_hash(password, n=n, r=r, p=p, b64salt=salt)

        if new_hash == existing_hash:
            return True
        else:
            return False

    def parse_hash(hash):
        #Guard clauses
        if hash[0] != "$" or hash[-1] != "$": return "INVALID HASH"

        #First, remove leading and trailing "$" - no need for them
        hash = hash[1:-1]

        #Second, split into sections by "$", resulting in four sections as per PHC spec
        # - Section 1: algo identifier ("scrypt")
        # - Section 2: all three scrypt settings, separated by commas ("ln=8,r=8,p=1")
        # - Section 3: the salt, 16 bytes (Passlib default), in base64
        # - Section 4: password hash, in base64

        try: 
            section = hash.split("$")
            id      = section[0]
            config  = section[1]
            salt    = section[2]
            pwhash  = section[3] 
            params  = config.split(",")

            if id != "scrypt": return "INVALID HASH"

            settings = {{
                "salt" : salt,
                "pwhash" : pwhash
            }}

            for param in params:
                key, value = param.split("=")
                settings[key] = int(value)

            if "n" not in settings: return "INVALID HASH"
            if "r" not in settings: return "INVALID HASH"
            if "p" not in settings: return "INVALID HASH"

            return settings

        except:
            return "INVALID HASH"
    """


    return textwrap.dedent(source_code), textwrap.dedent(scrypt_lib)
