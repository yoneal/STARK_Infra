import stark_core

name = "STARK Security"
authFailCode = 400
authFailResponse = []

def whoami():
    return name


def is_authorized(permission_required, event, ddb):
    username = event['requestContext']['authorizer']['lambda']['Username']
    
    response = ddb.query(
        TableName=stark_core.ddb_table,
        Select='ALL_ATTRIBUTES',
        KeyConditionExpression="#pk = :pk and #sk = :sk",
        ExpressionAttributeNames={
            '#pk' : 'pk',
            '#sk' : 'sk'
        },
        ExpressionAttributeValues={
            ':pk' : {'S' : username },
            ':sk' : {'S' : 'STARK|user|permissions' }
        }
    )

    raw = response.get('Items')

    permissions_string = ''
    for record in raw:
        permissions_string = record['Permissions']['S']

    if permissions_string != '':
        #Parse permissions_string to check if permission_required exists in it
        permissions_list = permissions_string.split(", ")
        if permission_required in permissions_list:
            return True

    global authFailResponse, authFailCode
    authFailResponse = [authFailCode, f"Could not find {permission_required} for {username}"]
    return False
