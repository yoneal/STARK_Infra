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

    #Extra modules
    import boto3

    ddb = boto3.client('dynamodb')

    #######
    #CONFIG
    ddb_table  = "{ddb_table_name}"

    def lambda_handler(event, context):

        print("***EVENT DATA***")
        print(event)
        print("***END: EVENT DATA***")

        #Get cookies, if any
        eventCookies = event.get('cookies', {{}})
        cookies = {{}}
        for cookie in eventCookies:
            info = cookie.partition("=")
            cookies[info[0]] = info[2]

        isAuthorized=False
        sess_id = cookies.get('sessid','')
        if sess_id != '':
            #Get session record from DDB
            sess_record = get_session(sess_id)

            #Get username from record 
            username = sess_record['Username']

            #FIXME: Optional/Future - immediately check permissions here and decide if API endpoint requested is authorized

            #Set authorized if everything is ok 
            if username != '':
                isAuthorized=True

        response = {{ 
            "isAuthorized": isAuthorized,
            "context": {{
                "Username": username,
            }} 
        }}

        #FIXME:
        # #Lambda Authorizer Simple Response can return optional `context`, as in below
        # #This could be an efficient and performant way to allow STARK to get a Cobalt-like permissions system
        # #by using `context` to cache frequently needed user information, either from session record, user record, or even
        # #general permissions system infra (e.g., names and other metadata of modules)
        # #NOTE: Format below is from NodeJS example, not necessarily 1:1 for Python 3.
        # response = {{
        #   "isAuthorized": isAuthorized,
        #   "context": {{
        #        "stringKey": "value",
        #        "numberKey": 1,
        #        "booleanKey": True,
        #        "arrayKey": ["value1", "value2"],
        #        "mapKey": {{"value1": "value2"}}
        #    }}
        # }}
        # #NOTE: Response here is sent to the integration (i.e., the Lambda function behind the API call that the Authorizer has authorized)
        # #      and can be retrieved through: event['requestContext']['authorizer']['lambda'][$VARNAME]. Our `username` context var, e.g.:
        # #      username = event['requestContext']['authorizer']['lambda']['username']



        return response

    def get_session(sess_id):
        response = ddb.query(
            TableName=ddb_table,
            Select='ALL_ATTRIBUTES',
            KeyConditionExpression="#pk = :pk and #sk = :sk",
            ExpressionAttributeNames={{
                '#pk' : 'pk',
                '#sk' : 'sk'
            }},
            ExpressionAttributeValues={{
                ':pk' : {{'S' : sess_id }},
                ':sk' : {{'S' : "STARK|session" }}
            }}
        )

        raw = response.get('Items')

        for record in raw:
            item = {{'pk': record['pk']['S'],
                    'sk': record['sk']['S'],
                    'Username': record['Username']['S']}}

        return item
    """

    return textwrap.dedent(source_code)
