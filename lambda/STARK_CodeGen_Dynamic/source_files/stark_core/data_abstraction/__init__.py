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


def get_many_by_pk(pk, sk, db_handler = None):
    if db_handler == None:
        db_handler = ddb

    ddb_arguments = {}
    ddb_arguments['TableName'] = stark_core.ddb_table
    ddb_arguments['Select'] = "ALL_ATTRIBUTES"
    ddb_arguments['KeyConditionExpression'] = "#pk = :pk and #sk = :sk"
    ddb_arguments['ExpressionAttributeNames'] = {
                                                '#pk' : 'pk',
                                                '#sk' : 'sk'
                                            }
    ddb_arguments['ExpressionAttributeValues'] = {
                                                ':pk' : {'S' : pk },
                                                ':sk' : {'S' : sk }
                                            }
                                            
    response = db_handler.query(**ddb_arguments).get('Items')
    return response
    
def get_many_by_pk(pk, sk, db_handler = None):
    if db_handler == None:
        db_handler = ddb

    ddb_arguments = {}
    ddb_arguments['TableName'] = stark_core.ddb_table
    ddb_arguments['Select'] = "ALL_ATTRIBUTES"
    ddb_arguments['KeyConditionExpression'] = "#pk = :pk and #sk = :sk"
    ddb_arguments['ExpressionAttributeNames'] = {
                                                '#pk' : 'pk',
                                                '#sk' : 'sk'
                                            }
    ddb_arguments['ExpressionAttributeValues'] = {
                                                ':pk' : {'S' : pk },
                                                ':sk' : {'S' : sk }
                                            }
    Document = db_handler.query(**ddb_arguments)
    response = Document.get('Items')
    return response

def get_report_data(report_payload, object_expression_value, string_filter, is_aggregate_report, map_results_func):
    ##FIXME: pass map_results function for now, it will be refactored soon and will just process meta data of an entity so that
    #        it can be dynamically used.
    next_token = 'initial'
    items = []
    ddb_arguments = {}
    aggregated_results = {}
    ddb_arguments['TableName'] = stark_core.ddb_table
    ddb_arguments['IndexName'] = "STARK-ListView-Index"
    ddb_arguments['Select'] = "ALL_ATTRIBUTES"
    ddb_arguments['ReturnConsumedCapacity'] = 'TOTAL'
    ddb_arguments['KeyConditionExpression'] = 'sk = :sk'
    ddb_arguments['ExpressionAttributeValues'] = object_expression_value

    if string_filter != "":
        ddb_arguments['FilterExpression'] = string_filter

    while next_token != None:
        next_token = '' if next_token == 'initial' else next_token

        if next_token != '':
            ddb_arguments['ExclusiveStartKey']=next_token

        response = ddb.query(**ddb_arguments)
        raw = response.get('Items')
        next_token = response.get('LastEvaluatedKey')
        for record in raw:
            item = map_results_func(record)
            if is_aggregate_report:
                aggregate_key = report_payload['STARK_group_by_1']
                aggregate_key_value = item.get(aggregate_key)
                if aggregate_key_value in aggregated_results:
                    for field in report_payload['STARK_count_fields']:
                        count_index_name = f"Count of {field}"
                        aggregated_results[aggregate_key_value][count_index_name] += 1

                    for field in report_payload['STARK_sum_fields']:
                        sum_index_name = f"Sum of {field}"
                        sum_value = float(item.get(field))
                        aggregated_results[aggregate_key_value][sum_index_name] = round(aggregated_results[aggregate_key_value][sum_index_name], 1) + sum_value

                    for column in report_payload['STARK_report_fields']:
                        if column != aggregate_key:  
                            aggregated_results[aggregate_key_value][column] = item.get(column.replace(" ","_"))

                else:
                    temp_dict = { aggregate_key : aggregate_key_value}
                    for field in report_payload['STARK_count_fields']:
                        count_index_name = f"Count of {field}"
                        temp_dict.update({
                            count_index_name:  1
                        })

                    for field in report_payload['STARK_sum_fields']:
                        sum_index_name = f"Sum of {field}"
                        sum_value = float(item.get(field))
                        temp_dict.update({
                            sum_index_name: sum_value
                        })

                    for column in report_payload['STARK_report_fields']:
                        if column != aggregate_key:  
                            temp_dict.update({
                                column: item.get(column.replace(" ","_"))
                            })

                    aggregated_results[aggregate_key_value] = temp_dict
            else:
                items.append(item)

    return items, aggregated_results