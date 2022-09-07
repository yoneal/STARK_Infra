#Python Standard Library
import base64
import json
import sys
import importlib
from urllib.parse import unquote
import math

#Extra modules
import boto3
import csv
import uuid
from io import StringIO
import os
from fpdf import FPDF

#STARK
import stark_core 
from stark_core import utilities
from stark_core import validation

ddb = boto3.client('dynamodb')
s3 = boto3.client("s3")

#######
#CONFIG
ddb_table         = stark_core.ddb_table
bucket_name       = stark_core.bucket_name
region_name       = stark_core.region_name
page_limit        = stark_core.page_limit
bucket_url        = stark_core.bucket_url
bucket_tmp        = stark_core.bucket_tmp
pk_field          = "Role_Name"
default_sk        = "STARK|role"
sort_fields       = ["Role_Name", ]
relationships     = []
entity_upload_dir = stark_core.upload_dir + "STARK_User_Roles/"
metadata          = {
    'Role_Name': {
        'value': '',
        'required': True,
        'max_length': '',
        'data_type': '',
        'state': None,
        'feedback': ''
    },
    'Description': {
        'value': '',
        'required': True,
        'max_length': '',
        'data_type': '',
        'state': None,
        'feedback': ''
    },
    'Permissions': {
        'value': '',
        'required': False,
        'max_length': '',
        'data_type': '',
        'state': None,
        'feedback': ''
    },
}

############
#PERMISSIONS
stark_permissions = {
    'view': 'User Roles|View',
    'add': 'User Roles|Add',
    'delete': 'User Roles|Delete',
    'edit': 'User Roles|Edit',
    'report': 'User Roles|Report'
}

def lambda_handler(event, context):
    responseStatusCode = 200
    #Get request type
    request_type = event.get('queryStringParameters',{}).get('rt','')

    if request_type == '':
        ########################
        #Handle non-GET requests

        #Get specific request method
        method  = event.get('requestContext').get('http').get('method')

        if event.get('isBase64Encoded') == True :
            payload = json.loads(base64.b64decode(event.get('body'))).get('STARK_User_Roles',"")
        else:    
            payload = json.loads(event.get('body')).get('STARK_User_Roles',"")

        data    = {}

        if payload == "":
            return {
                "isBase64Encoded": False,
                "statusCode": 400,
                "body": json.dumps("Client payload missing"),
                "headers": {
                    "Content-Type": "application/json",
                }
            }
        else:
            isInvalidPayload = False
            data['pk'] = payload.get('Role_Name')
            data['Description'] = payload.get('Description','')
            data['Permissions'] = payload.get('Permissions','')
            if payload.get('STARK_isReport', False) == False:
                data['orig_pk'] = payload.get('orig_Role_Name','')
                data['sk'] = payload.get('sk', '')
                if data['sk'] == "":
                    data['sk'] = default_sk
                ListView_index_values = []
                for field in sort_fields:
                    ListView_index_values.append(payload.get(field))
                data['STARK-ListView-sk'] = "|".join(ListView_index_values)
            else:
                #FIXME: Reporting payload processing:
                # - identifying filter fields
                # - operators validator
                temp = payload.get('STARK_report_fields',[])
                temp_report_fields = []
                for index in temp:
                    temp_report_fields.append(index['label'])
                for index, attributes in data.items():
                    if attributes['value'] != "":
                        if attributes['operator'] == "":
                            isInvalidPayload = True
                data['STARK_report_fields'] = temp_report_fields
                data['STARK_isReport'] = payload.get('STARK_isReport', False)

            if isInvalidPayload:
                return {
                    "isBase64Encoded": False,
                    "statusCode": 400,
                    "body": json.dumps("Missing operators"),
                    "headers": {
                        "Content-Type": "application/json",
                    }
                }

        if method == "DELETE":
            if(stark_core.sec.is_authorized(stark_permissions['delete'], event, ddb)):
                response = delete(data)
            else:
                responseStatusCode, response = stark_core.sec.authFailResponse

        elif method == "PUT":
            if(stark_core.sec.is_authorized(stark_permissions['edit'], event, ddb)):
                payload = data
                payload['Role_Name'] = data['pk']
                invalid_payload = validation.validate_form(payload, metadata)
                if len(invalid_payload) > 0:
                    return {
                        "isBase64Encoded": False,
                        "statusCode": responseStatusCode,
                        "body": json.dumps(invalid_payload),
                        "headers": {
                            "Content-Type": "application/json",
                        }
                    }
                else:
                #We can't update DDB PK, so if PK is different, we need to do ADD + DELETE
                    if data['orig_pk'] == data['pk']:
                        response = edit(data)
                    else:
                        response   = add(data, method)
                        data['pk'] = data['orig_pk']
                        response   = delete(data)
            else:
                responseStatusCode, response = stark_core.sec.authFailResponse

        elif method == "POST":
            if 'STARK_isReport' in data:
                if(stark_core.sec.is_authorized(stark_permissions['report'], event, ddb)):
                    response = report(data, default_sk)
                else:
                    responseStatusCode, response = stark_core.sec.authFailResponse
            else:
                if(stark_core.sec.is_authorized(stark_permissions['add'], event, ddb)):
                    payload = data
                    payload['Role_Name'] = data['pk']
                    invalid_payload = validation.validate_form(payload, metadata)
                    if len(invalid_payload) > 0:
                        return {
                            "isBase64Encoded": False,
                            "statusCode": responseStatusCode,
                            "body": json.dumps(invalid_payload),
                            "headers": {
                                "Content-Type": "application/json",
                            }
                        }

                    else:
                        response = add(data)
                else:
                    responseStatusCode, response = stark_core.sec.authFailResponse

        else:
            return {
                "isBase64Encoded": False,
                "statusCode": 400,
                "body": json.dumps("Could not handle API request"),
                "headers": {
                    "Content-Type": "application/json",
                }
            }

    else:
        ####################
        #Handle GET requests
        if request_type == "all":
            #check for submitted token
            lv_token = event.get('queryStringParameters',{}).get('nt', None)
            if lv_token != None:
                lv_token = unquote(lv_token)
                lv_token = json.loads(lv_token)

            items, next_token = get_all(default_sk, lv_token)

            response = {
                'Next_Token': json.dumps(next_token),
                'Items': items
            }

        elif request_type == "detail":

            pk = event.get('queryStringParameters').get('Role_Name','')
            sk = event.get('queryStringParameters').get('sk','')
            if sk == "":
                sk = default_sk

            response = get_by_pk(pk, sk)
        else:
            return {
                "isBase64Encoded": False,
                "statusCode": 400,
                "body": json.dumps("Could not handle GET request - unknown request type"),
                "headers": {
                    "Content-Type": "application/json",
                }
            }

    return {
        "isBase64Encoded": False,
        "statusCode": responseStatusCode,
        "body": json.dumps(response),
        "headers": {
            "Content-Type": "application/json",
        }
    }

def get_all(sk=default_sk, lv_token=None):

    if lv_token == None:
        response = ddb.query(
            TableName=ddb_table,
            IndexName="STARK-ListView-Index",
            Select='ALL_ATTRIBUTES',
            Limit=page_limit,
            ReturnConsumedCapacity='TOTAL',
            KeyConditionExpression='sk = :sk',
            ExpressionAttributeValues={
                ':sk' : {'S' : sk}
            }
        )
    else:
        response = ddb.query(
            TableName=ddb_table,
            IndexName="STARK-ListView-Index",
            Select='ALL_ATTRIBUTES',
            Limit=page_limit,
            ExclusiveStartKey=lv_token,
            ReturnConsumedCapacity='TOTAL',
            KeyConditionExpression='sk = :sk',
            ExpressionAttributeValues={
                ':sk' : {'S' : sk}
            }
        )

    raw = response.get('Items')

    #Map to expected structure
    #FIXME: this is duplicated code, make this DRY by outsourcing the mapping to a different function.
    items = []
    for record in raw:
        items.append(map_results(record))

    #Get the "next" token, pass to calling function. This enables a "next page" request later.
    next_token = response.get('LastEvaluatedKey')

    return items, next_token

def get_by_pk(pk, sk=default_sk):
    response = ddb.query(
        TableName=ddb_table,
        Select='ALL_ATTRIBUTES',
        KeyConditionExpression="#pk = :pk and #sk = :sk",
        ExpressionAttributeNames={
            '#pk' : 'pk',
            '#sk' : 'sk'
        },
        ExpressionAttributeValues={
            ':pk' : {'S' : pk },
            ':sk' : {'S' : sk }
        }
    )

    raw = response.get('Items')

    #Map to expected structure
    response = {}
    response['item'] = map_results(raw[0])

    return response

def delete(data):
    pk = data.get('pk','')
    sk = data.get('sk','')
    if sk == '': sk = default_sk
    
    response = ddb.delete_item(
        TableName=ddb_table,
        Key={
            'pk' : {'S' : pk},
            'sk' : {'S' : sk}
        }
    )

    return "OK"

def edit(data):                
    pk = data.get('pk', '')
    sk = data.get('sk', '')
    if sk == '': sk = default_sk
    Description = str(data.get('Description', ''))
    Permissions = str(data.get('Permissions', ''))

    UpdateExpressionString = "SET #Description = :Description, #Permissions = :Permissions" 
    ExpressionAttributeNamesDict = {
        '#Description' : 'Description',
        '#Permissions' : 'Permissions',
    }
    ExpressionAttributeValuesDict = {
        ':Description' : {'S' : Description },
        ':Permissions' : {'S' : Permissions },
    }

    STARK_ListView_sk = data.get('STARK-ListView-sk','')
    if STARK_ListView_sk == '':
        STARK_ListView_sk = create_listview_index_value(data)

    UpdateExpressionString += ", #STARKListViewsk = :STARKListViewsk"
    ExpressionAttributeNamesDict['#STARKListViewsk']  = 'STARK-ListView-sk'
    ExpressionAttributeValuesDict[':STARKListViewsk'] = {'S' : data['STARK-ListView-sk']}

    response = ddb.update_item(
        TableName=ddb_table,
        Key={
            'pk' : {'S' : pk},
            'sk' : {'S' : sk}
        },
        UpdateExpression=UpdateExpressionString,
        ExpressionAttributeNames=ExpressionAttributeNamesDict,
        ExpressionAttributeValues=ExpressionAttributeValuesDict
    )

    response = cascade_pk_change_to_child(data)
    return "OK"

def add(data, method ='POST'):
    pk = data.get('pk', '')
    sk = data.get('sk', '')
    if sk == '': sk = default_sk
    Description = str(data.get('Description', ''))
    Permissions = str(data.get('Permissions', ''))

    item={}
    item['pk'] = {'S' : pk}
    item['sk'] = {'S' : sk}
    item['Description'] = {'S' : Description}
    item['Permissions'] = {'S' : Permissions}

    if data.get('STARK-ListView-sk','') == '':
        item['STARK-ListView-sk'] = {'S' : create_listview_index_value(data)}
    else:
        item['STARK-ListView-sk'] = {'S' : data['STARK-ListView-sk']}
    response = ddb.put_item(
        TableName=ddb_table,
        Item=item,
    )
    if method == 'POST':
        data['orig_pk'] = pk
    response = cascade_pk_change_to_child(data)

    return "OK"

def report(data, sk=default_sk):
    #FIXME: THIS IS A STUB, WILL NEED TO BE UPDATED WITH
    #   ENHANCED LISTVIEW LOGIC LATER WHEN WE ACTUALLY IMPLEMENT REPORTING

    temp_string_filter = ""
    object_expression_value = {':sk' : {'S' : sk}}
    report_param_dict = {}
    for key, index in data.items():
        if key not in ["STARK_isReport", "STARK_report_fields", "STARK_uploaded_s3_keys"]:
            if index['value'] != "":
                processed_operator_and_parameter_dict = utilities.compose_report_operators_and_parameters(key, index) 
                temp_string_filter += processed_operator_and_parameter_dict['filter_string']
                object_expression_value.update(processed_operator_and_parameter_dict['expression_values'])
                report_param_dict.update(processed_operator_and_parameter_dict['report_params'])
    string_filter = temp_string_filter[1:-3]

    if temp_string_filter == "":
        response = ddb.query(
            TableName=ddb_table,
            IndexName="STARK-ListView-Index",
            Select='ALL_ATTRIBUTES',
            ReturnConsumedCapacity='TOTAL',
            KeyConditionExpression='sk = :sk',
            ExpressionAttributeValues=object_expression_value
        )
    else:
        response = ddb.query(
            TableName=ddb_table,
            IndexName="STARK-ListView-Index",
            Select='ALL_ATTRIBUTES',
            ReturnConsumedCapacity='TOTAL',
            FilterExpression=string_filter,
            KeyConditionExpression='sk = :sk',
            ExpressionAttributeValues=object_expression_value
        )
    raw = response.get('Items')

    #Map to expected structure
    #FIXME: this is duplicated code, make this DRY by outsourcing the mapping to a different function.
    items = []
    for record in raw:
        items.append(map_results(record))

    report_filenames = generate_reports(items, data['STARK_report_fields'], report_param_dict)
    #Get the "next" token, pass to calling function. This enables a "next page" request later.
    next_token = response.get('LastEvaluatedKey')

    return items, next_token, report_filenames

def compose_report_operators_and_parameters(key, data):
    composed_filter_dict = {"filter_string":"","expression_values": {}}
    if data['operator'] == "IN":
        string_split = data['value'].split(',')
        composed_filter_dict['filter_string'] += f" {key} IN "
        temp_in_string = ""
        in_string = ""
        in_counter = 1
        composed_filter_dict['report_params'] = {key : f"Is in {data['value']}"}
        for in_index in string_split:
            in_string += f" :inParam{in_counter}, "
            composed_filter_dict['expression_values'][f":inParam{in_counter}"] = {data['type'] : in_index.strip()}
            in_counter += 1
        temp_in_string = in_string[1:-2]
        composed_filter_dict['filter_string'] += f"({temp_in_string}) AND"
    elif data['operator'] in [ "contains", "begins_with" ]:
        composed_filter_dict['filter_string'] += f" {data['operator']}({key}, :{key}) AND"
        composed_filter_dict['expression_values'][f":{key}"] = {data['type'] : data['value'].strip()}
        composed_filter_dict['report_params'] = {key : f"{data['operator'].capitalize().replace('_', ' ')} {data['value']}"}
    elif data['operator'] == "between":
        from_to_split = data['value'].split(',')
        composed_filter_dict['filter_string'] += f" ({key} BETWEEN :from{key} AND :to{key}) AND"
        composed_filter_dict['expression_values'][f":from{key}"] = {data['type'] : from_to_split[0].strip()}
        composed_filter_dict['expression_values'][f":to{key}"] = {data['type'] : from_to_split[1].strip()}
        composed_filter_dict['report_params'] = {key : f"Between {from_to_split[0].strip()} and {from_to_split[1].strip()}"}
    else:
        composed_filter_dict['filter_string'] += f" {key} {data['operator']} :{key} AND"
        composed_filter_dict['expression_values'][f":{key}"] = {data['type'] : data['value'].strip()}
        operator_string_equivalent = ""
        if data['operator'] == '=':
            operator_string_equivalent = 'Is equal to'
        elif data['operator'] == '>':
            operator_string_equivalent = 'Is greater than'
        elif data['operator'] == '>=':
            operator_string_equivalent = 'Is greater than or equal to'
        elif data['operator'] == '<':
            operator_string_equivalent = 'Is less than'
        elif data['operator'] == '<=':
            operator_string_equivalent = 'Is greater than or equal to'
        elif data['operator'] == '<=':
            operator_string_equivalent = 'Is not equal to'
        else:
            operator_string_equivalent = 'Invalid operator'
        composed_filter_dict['report_params'] = {key : f" {operator_string_equivalent} {data['value'].strip()}" }

    return composed_filter_dict

def map_results(record):
    item = {}
    item['Role_Name'] = record.get('pk', {}).get('S','')
    item['sk'] = record.get('sk',{}).get('S','')
    item['Description'] = record.get('Description',{}).get('S','')
    item['Permissions'] = record.get('Permissions',{}).get('S','')
    return item

def generate_reports(mapped_results = [], display_fields=[], report_params = {}): 
    diff_list = []
    master_fields = ['Role Name', 'Description', 'Permissions', ]
    if len(display_fields) > 0:
        csv_header = display_fields
        diff_list = list(set(master_fields) - set(display_fields))
    else:
        csv_header = master_fields

    report_list = []
    for key in mapped_results:
        temp_dict = {}
        #remove primary identifiers and STARK attributes
        key.pop("sk")
        for index, value in key.items():
            temp_dict[index.replace("_"," ")] = value
        report_list.append(temp_dict)

    file_buff = StringIO()
    writer = csv.DictWriter(file_buff, fieldnames=csv_header)
    writer.writeheader()
    for rows in report_list:
        for index in diff_list:
            rows.pop(index)
        writer.writerow(rows)
    filename = f"{str(uuid.uuid4())}"
    csv_file = f"{filename}.csv"
    pdf_file = f"{filename}.pdf"
    s3_action = s3.put_object(
        ACL='public-read',
        Body= file_buff.getvalue(),
        Bucket=bucket_name,
        Key='tmp/'+csv_file
    )

    prepare_pdf_data(report_list, csv_header, pdf_file, report_params)

    csv_bucket_key = bucket_tmp + csv_file
    pdf_bucket_key = bucket_tmp + pdf_file

    return csv_bucket_key, pdf_bucket_key


def prepare_pdf_data(data_to_tuple, master_fields, pdf_filename, report_params):
    #FIXME: PDF GENERATOR: can be outsourced to a layer, for refining 
    master_fields.insert(0, '#')
    numerical_columns = {}
    for key, items in metadata.items():
        if items['data_type'] == 'number':
            numerical_columns.update({key: 0})
    row_list = []
    counter = 1 
    for key in data_to_tuple:
        column_list = []
        for index in master_fields:
            if(index != '#'):
                if index in numerical_columns.keys():
                    numerical_columns[index] += int(key[index])
                column_list.append(key[index])
        column_list.insert(0, str(counter)) 
        row_list.append(tuple(column_list))
        counter += 1

    if len(numerical_columns) > 0:
        column_list = []
        for values in master_fields:
            if values in numerical_columns:
                column_list.append(str(numerical_columns.get(values, '')))
            else:
                column_list.append('')
        row_list.append(column_list)

    header_tuple = tuple(master_fields) 
    data_tuple = tuple(row_list)

    pdf = utilities.create_pdf(header_tuple, data_tuple, report_params, pk_field, metadata)
    s3_action = s3.put_object(
        ACL='public-read',
        Body= pdf.output(),
        Bucket=bucket_name,
        Key='tmp/'+pdf_filename
    )


def create_listview_index_value(data):
    ListView_index_values = []
    for field in sort_fields:
        if field == pk_field:
            ListView_index_values.append(data['pk'])
        else:
            ListView_index_values.append(data.get(field))
    STARK_ListView_sk = "|".join(ListView_index_values)
    return STARK_ListView_sk

def cascade_pk_change_to_child(params):
    import STARK_User as user

    #fetch all records from child using old pk value
    response = user.get_all_by_old_parent_value(params['orig_pk'])

    #loop through response and update each record
    for record in response:
        record['Role'] = params['pk']
        user.edit(record)

    return "OK"