import stark_core
import boto3

ddb    = boto3.client('dynamodb')
name = "STARK Data Abstraction"


def whoami():
    return name

def get_fields(fields, pk_field, sk):

    ddb_arguments = {}
    next_token = 'initial'
    items = []
    while next_token != None:
        next_token = '' if next_token == 'initial' else next_token
        ddb_arguments['TableName'] = stark_core.ddb_table
        ddb_arguments['IndexName'] = "STARK-ListView-Index"
        ddb_arguments['Limit'] = stark_core.page_limit
        ddb_arguments['ReturnConsumedCapacity'] ='TOTAL'
        ddb_arguments['KeyConditionExpression'] = 'sk = :sk'
        ddb_arguments['ExpressionAttributeValues'] = {
            ':sk' : {'S' : sk}
        }

        if next_token != '':
            ddb_arguments['ExclusiveStartKey']=next_token

        response = ddb.query(**ddb_arguments)
        raw = response.get('Items')

        for record in raw:

            item = {}
            for field in fields:
                if field == pk_field:
                    get_record = record.get('pk',{}).get('S','')
                else:
                    get_record = record.get(field,{}).get('S','')

                item[field] = get_record
            items.append(item)
        next_token = response.get('LastEvaluatedKey')

    return items