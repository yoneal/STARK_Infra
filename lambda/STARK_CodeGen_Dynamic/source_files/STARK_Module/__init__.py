#Python Standard Library
import base64
from email.policy import default
import json
from urllib.parse import unquote
import sys
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
pk_field          = "Module_Name"
default_sk        = "STARK|module"
sort_fields       = ["Module_Name", ]
relationships     = []
metadata          = {
    'Module_Name': {
        'value': '',
        'required': True,
        'max_length': '',
        'data_type': '',
        'state': None,
        'feedback': ''
    },
    'Descriptive_Title': {
        'value': '',
        'required': True,
        'max_length': '',
        'data_type': '',
        'state': None,
        'feedback': ''
    },
    'Target': {
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
    'Module_Group': {
        'value': '',
        'required': True,
        'max_length': '',
        'data_type': '',
        'state': None,
        'feedback': ''
    },
    'Is_Menu_Item': {
        'value': '',
        'required': False,
        'max_length': '',
        'data_type': '',
        'state': None,
        'feedback': ''
    },
    'Is_Enabled': {
        'value': '',
        'required': False,
        'max_length': '',
        'data_type': '',
        'state': None,
        'feedback': ''
    },
    'Icon': {
        'value': '',
        'required': True,
        'max_length': '',
        'data_type': '',
        'state': None,
        'feedback': ''
    },
    'Priority': {
        'value': '',
        'required': True,
        'max_length': '',
        'data_type': '',
        'state': None,
        'feedback': ''
    },
}

def lambda_handler(event, context):

    #Get request type
    request_type = event.get('queryStringParameters',{}).get('rt','')

    if request_type == '':
        ########################
        #Handle non-GET requests

        #Get specific request method
        method  = event.get('requestContext').get('http').get('method')

        if event.get('isBase64Encoded') == True :
            payload = json.loads(base64.b64decode(event.get('body'))).get('STARK_Module',"")
        else:    
            payload = json.loads(event.get('body')).get('STARK_Module',"")

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
            data['pk'] = payload.get('Module_Name')
            data['Descriptive_Title'] = payload.get('Descriptive_Title','')
            data['Target'] = payload.get('Target','')
            data['Description'] = payload.get('Description','')
            data['Module_Group'] = payload.get('Module_Group','')
            data['Is_Menu_Item'] = payload.get('Is_Menu_Item','')
            data['Is_Enabled'] = payload.get('Is_Enabled','')
            data['Icon'] = payload.get('Icon','')
            data['Priority'] = payload.get('Priority','')
            if payload.get('STARK_isReport', False) == False:
                data['orig_pk'] = payload.get('orig_Module_Name','')
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
            response = delete(data)

        elif method == "PUT":

            #We can't update DDB PK, so if PK is different, we need to do ADD + DELETE
            if data['orig_pk'] == data['pk']:
                response = edit(data)
            else:
                response   = add(data)
                data['pk'] = data['orig_pk']
                response   = delete(data)

        elif method == "POST":
            if 'STARK_isReport' in data:
                response = report(data, default_sk)
            else:
                response = add(data)

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

        elif request_type == "report":
            response = report(default_sk)
        
        elif request_type == "get_fields":
            fields = event.get('queryStringParameters').get('fields','')
            fields = fields.split(",")
            response = get_fields(fields, default_sk)

        elif request_type == "detail":

            pk = event.get('queryStringParameters').get('Module_Name','')
            sk = event.get('queryStringParameters').get('sk','')
            if sk == "":
                sk = default_sk

            response = get_by_pk(pk, sk)

        elif request_type == "usermodules":
            #FIXME: Getting the username should be a STARK Core framework utility. Only here for now for MVP implem, to not hold up more urgent dependent features
            #FIXME: When framework-ized, getting the requestContext should be at the beginning of the handler, and will exit if handler needs the Username and is not present (i.e., not properly authorized)
            #FIXME: Make sure for this framework-ized implementation that it will still work when Framework components call each other directly through the STARK registry instead of through API Gateway.
            username = event.get('requestContext', {}).get('authorizer', {}).get('lambda', {}).get('Username','')
            response = get_user_modules(username, default_sk)

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
        "statusCode": 200,
        "body": json.dumps(response),
        "headers": {
            "Content-Type": "application/json",
        }
    }

def report(data, sk=default_sk):
    #FIXME: THIS IS A STUB, WILL NEED TO BE UPDATED WITH
    #   ENHANCED LISTVIEW LOGIC LATER WHEN WE ACTUALLY IMPLEMENT REPORTING

    temp_string_filter = ""
    object_expression_value = {':sk' : {'S' : sk}}
    report_param_dict = {}
    for key, index in data.items():
        if key not in ["STARK_isReport", "STARK_report_fields", "STARK_uploaded_s3_keys"]:
            if index['value'] != "":
                processed_operator_and_parameter_dict = compose_report_operators_and_parameters(key, index) 
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
        item = {}
        item['Module_Name'] = record.get('pk', {}).get('S','')
        item['sk'] = record.get('sk',{}).get('S','')
        item['Descriptive_Title'] = record.get('Descriptive_Title',{}).get('S','')
        item['Target'] = record.get('Target',{}).get('S','')
        item['Description'] = record.get('Description',{}).get('S','')
        item['Module_Group'] = record.get('Module_Group',{}).get('S','')
        item['Is_Menu_Item'] = record.get('Is_Menu_Item',{}).get('BOOL','')
        item['Is_Enabled'] = record.get('Is_Enabled',{}).get('BOOL','')
        item['Icon'] = record.get('Icon',{}).get('S','')
        item['Priority'] = record.get('Priority',{}).get('N','')
        items.append(item)

    #Get the "next" token, pass to calling function. This enables a "next page" request later.
    next_token = response.get('LastEvaluatedKey')

    return items, next_token

def get_by_pk(pk, sk=default):
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
    items = []
    for record in raw:
        item = {}
        item['Module_Name'] = record.get('pk', {}).get('S','')
        item['sk'] = record.get('sk',{}).get('S','')
        item['Descriptive_Title'] = record.get('Descriptive_Title',{}).get('S','')
        item['Target'] = record.get('Target',{}).get('S','')
        item['Description'] = record.get('Description',{}).get('S','')
        item['Module_Group'] = record.get('Module_Group',{}).get('S','')
        item['Is_Menu_Item'] = record.get('Is_Menu_Item',{}).get('BOOL','')
        item['Is_Enabled'] = record.get('Is_Enabled',{}).get('BOOL','')
        item['Icon'] = record.get('Icon',{}).get('S','')
        item['Priority'] = record.get('Priority',{}).get('N','')
        items.append(item)
    #FIXME: Mapping is duplicated code, make this DRY

    return items

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
    Descriptive_Title = str(data.get('Descriptive_Title', ''))
    Target = str(data.get('Target', ''))
    Description = str(data.get('Description', ''))
    Module_Group = str(data.get('Module_Group', ''))
    Is_Menu_Item = data.get('Is_Menu_Item', False)
    Is_Enabled = data.get('Is_Enabled', False)
    Icon = str(data.get('Icon', ''))
    Priority = str(data.get('Priority', ''))

    # if Is_Menu_Item == 'Y':
    #     Is_Menu_Item = True
    # else:
    #     Is_Menu_Item = False
    # Is_Enabled = str(data.get('Is_Enabled', ''))
    # if Is_Enabled == 'Y':
    #     Is_Enabled = True
    # else:
    #     Is_Enabled = False

    UpdateExpressionString = "SET #Descriptive_Title = :Descriptive_Title, #Target = :Target, #Description = :Description, #Module_Group = :Module_Group, #Is_Menu_Item = :Is_Menu_Item, #Is_Enabled = :Is_Enabled, #Icon = :Icon, #Priority = :Priority" 
    ExpressionAttributeNamesDict = {
        '#Descriptive_Title' : 'Descriptive_Title',
        '#Target' : 'Target',
        '#Description' : 'Description',
        '#Module_Group' : 'Module_Group',
        '#Is_Menu_Item' : 'Is_Menu_Item',
        '#Is_Enabled' : 'Is_Enabled',
        '#Icon' : 'Icon',
        '#Priority' : 'Priority',
    }
    ExpressionAttributeValuesDict = {
        ':Descriptive_Title' : {'S' : Descriptive_Title },
        ':Target' : {'S' : Target },
        ':Description' : {'S' : Description },
        ':Module_Group' : {'S' : Module_Group },
        ':Is_Menu_Item' : {'BOOL' : Is_Menu_Item },
        ':Is_Enabled' : {'BOOL' : Is_Enabled },
        ':Icon' : {'S' : Icon },
        ':Priority' : {'N' : Priority },
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

    return "OK"

def add(data):
    pk = data.get('pk', '')
    sk = data.get('sk', '')
    if sk == '': sk = default_sk
    Descriptive_Title = str(data.get('Descriptive_Title', ''))
    Target = str(data.get('Target', ''))
    Description = str(data.get('Description', ''))
    Module_Group = str(data.get('Module_Group', ''))
    Is_Menu_Item = data.get('Is_Menu_Item', False)
    Is_Enabled = data.get('Is_Enabled', False)
    Icon = str(data.get('Icon', ''))
    Priority = str(data.get('Priority', ''))

    # if Is_Menu_Item == 'Y':
    #     Is_Menu_Item = True
    # else:
    #     Is_Menu_Item = False
    # 
    # if Is_Enabled == 'Y':
    #     Is_Enabled = True
    # else:
    #     Is_Enabled = False


    item={}
    item['pk'] = {'S' : pk}
    item['sk'] = {'S' : sk}
    item['Descriptive_Title'] = {'S' : Descriptive_Title}
    item['Target'] = {'S' : Target}
    item['Description'] = {'S' : Description}
    item['Module_Group'] = {'S' : Module_Group}
    item['Is_Menu_Item'] = {'BOOL' : Is_Menu_Item}
    item['Is_Enabled'] = {'BOOL' : Is_Enabled}
    item['Icon'] = {'S' : Icon}
    item['Priority'] = {'N' : Priority}

    if data.get('STARK-ListView-sk','') == '':
        item['STARK-ListView-sk'] = {'S' : create_listview_index_value(data)}
    else:
        item['STARK-ListView-sk'] = {'S' : data['STARK-ListView-sk']}

    response = ddb.put_item(
        TableName=ddb_table,
        Item=item,
    )

    return "OK"

def unique(list1):
 
    # initialize a null list
    unique_list = []
 
    # traverse for all elements
    for x in list1:
        # check if exists in unique_list or not
        if x not in unique_list:
            unique_list.append(x)
    
    return unique_list

def get_user_modules(username, sk=default_sk):
    ########################
    #1.GET USER PERMISSIONS
    #FIXME: Getting user permissions should be a STARK Core framework utility, only here for now for urgent MVP implementation,
    #       to not hold up related features that need implementation ASAP
    response = ddb.query(
        TableName=ddb_table,
        Select='ALL_ATTRIBUTES',
        ReturnConsumedCapacity='TOTAL',
        KeyConditionExpression='pk = :pk and sk = :sk',
        ExpressionAttributeValues={
            ':pk' : {'S' : username},
            ':sk' : {'S' : "STARK|user|permissions"}
        }
    )

    raw = response.get('Items')
    permissions = []
    for record in raw:
        permission_string = record.get('Permissions',{}).get('S','')
    
    #Split permission_string by the delimeter (comma+space / ", ")
    permissions_list = permission_string.split(", ")

    ##################################
    #GET SYSTEM MODULES (ENABLED ONLY)
    response = ddb.query(
        TableName=ddb_table,
        IndexName="STARK-ListView-Index",
        Select='ALL_ATTRIBUTES',
        ReturnConsumedCapacity='TOTAL',
        KeyConditionExpression='sk = :sk',
        ExpressionAttributeValues={
            ':sk' : {'S' : sk}
        }
    )

    raw = response.get('Items')

    items = []
    grps = []
    for record in raw:
        if record.get('Is_Enabled',{}).get('BOOL','') == True:
            if record.get('Is_Menu_Item',{}).get('BOOL','') == True:
                if record.get('pk', {}).get('S','') in permissions_list:
                    #Only modules that are ENABLED, are MENU ITEMS, and are found in the user's permissions list are registered
                    item = {}
                    item['title'] = record.get('Descriptive_Title',{}).get('S','')
                    item['image'] = record.get('Icon',{}).get('S','')
                    #item['image_alt'] = record.get #FIXME: This isn't in the system modules model, because it wasn't in Cobalt as well... add please.
                    item['href'] = record.get('Target',{}).get('S','')
                    item['group'] = record.get('Module_Group',{}).get('S','')
                    item['priority'] = record.get('Priority',{}).get('N','')
                    grps.append(item['group'])
                    items.append(item)
    
    grps = unique(grps) 

    from os import getcwd 
    STARK_folder = getcwd() + '/STARK_Module_Groups'
    sys.path = [STARK_folder] + sys.path
    import STARK_Module_Groups as module_groups
    module_grps = module_groups.get_module_groups(grps)

    return {
        'items': items,
        'module_grps': module_grps
    }

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
    item['Module_Name'] = record.get('pk', {}).get('S','')
    item['sk'] = record.get('sk',{}).get('S','')
    item['Descriptive_Title'] = record.get('Descriptive_Title',{}).get('S','')
    item['Target'] = record.get('Target',{}).get('S','')
    item['Description'] = record.get('Description',{}).get('S','')
    item['Module_Group'] = record.get('Module_Group',{}).get('S','')
    item['Is_Menu_Item'] = record.get('Is_Menu_Item',{}).get('BOOL','')
    item['Is_Enabled'] = record.get('Is_Enabled',{}).get('BOOL','')
    item['Icon'] = record.get('Icon',{}).get('S','')
    item['Priority'] = record.get('Priority',{}).get('S','')
    return item

def generate_reports(mapped_results = [], display_fields=[], report_params = {}): 
    diff_list = []
    master_fields = ['Module Name', 'Descriptive Title', 'Target', 'Description', 'Module Group', 'Is Menu Item', 'Is Enabled', 'Icon', 'Priority', ]
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

    create_pdf(report_list, csv_header, pdf_file, report_params)

    csv_bucket_key = bucket_tmp + csv_file
    pdf_bucket_key = bucket_tmp + pdf_file

    return csv_bucket_key, pdf_bucket_key

def map_results(record):
    item = {}
    item['Module_Name'] = record.get('pk', {}).get('S','')
    item['sk'] = record.get('sk',{}).get('S','')
    item['Descriptive_Title'] = record.get('Descriptive_Title',{}).get('S','')
    item['Target'] = record.get('Target',{}).get('S','')
    item['Description'] = record.get('Description',{}).get('S','')
    item['Module_Group'] = record.get('Module_Group',{}).get('S','')
    item['Is_Menu_Item'] = record.get('Is_Menu_Item',{}).get('BOOL','')
    item['Is_Enabled'] = record.get('Is_Enabled',{}).get('BOOL','')
    item['Icon'] = record.get('Icon',{}).get('S','')
    item['Priority'] = record.get('Priority',{}).get('S','')
    return item

def create_pdf(data_to_tuple, master_fields, pdf_filename, report_params):
    #FIXME: PDF GENERATOR: can be outsourced to a layer, for refining 
    row_list = []
    print(data_to_tuple)
    for key in data_to_tuple:
        column_list = []
        for index in master_fields:
            column_list.append(key[index])
        row_list.append(tuple(column_list))

    header_tuple = tuple(master_fields) 
    data_tuple = tuple(row_list)
    pdf = FPDF(orientation='L')
    pdf.add_page()
    pdf.set_font("Helvetica", size=10)
    line_height = pdf.font_size * 2.5
    col_width = pdf.epw / len(master_fields)  # distribute content evenly

    render_page_header(pdf, line_height, report_params)
    render_table_header(pdf, header_tuple,  col_width, line_height) 
    counter = 0
    for row in data_tuple:
        if pdf.will_page_break(line_height):
            render_table_header(pdf, header_tuple,  col_width, line_height) 
        row_height = pdf.font_size * estimate_lines_needed(pdf, row, col_width)
        if row_height < line_height: #min height
            row_height = line_height
        elif row_height > 120: #max height tested, beyond this value will distort the table
            row_height = 120

        if counter % 2 ==0:
            pdf.set_fill_color(222,226,230)
        else:
            pdf.set_fill_color(255,255,255)

        for datum in row:
            pdf.multi_cell(col_width, row_height, str(datum), border=0, new_x="RIGHT", new_y="TOP", max_line_height=pdf.font_size, fill = True)
        pdf.ln(row_height)
        counter += 1

    s3_action = s3.put_object(
        ACL='public-read',
        Body= pdf.output(),
        Bucket=bucket_name,
        Key='tmp/'+pdf_filename
    )

def render_table_header(pdf, header_tuple, col_width, line_height):
    pdf.set_font(style="B")  # enabling bold text
    pdf.set_fill_color(52, 58,64)
    pdf.set_text_color(255,255,255)
    row_header_line_height = line_height * 1.5
    for col_name in header_tuple:
        pdf.multi_cell(col_width, row_header_line_height, col_name, border='TB', align='C',
                new_x="RIGHT", new_y="TOP",max_line_height=pdf.font_size, fill=True)
    pdf.ln(row_header_line_height)
    pdf.set_font(style="")  # disabling bold text
    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(0, 0, 0)

def render_page_header(pdf, line_height, report_params):
    param_width = pdf.epw / 4
    #Report Title
    pdf.set_font("Helvetica", size=14, style="B")
    pdf.multi_cell(0,line_height, "System Modules Report", 0, 'C',
                    new_x="RIGHT", new_y="TOP", max_line_height=pdf.font_size)
    pdf.ln()

    #Report Parameters
    newline_print_counter = 1
    pdf.set_font("Helvetica", size=12, style="B")
    pdf.multi_cell(0,line_height, "Report Parameters:", 0, "L", new_x="RIGHT", new_y="TOP", max_line_height=pdf.font_size)
    pdf.ln(pdf.font_size *1.5)
    if len(report_params) > 0:
        pdf.set_font("Helvetica", size=10)
        for key, value in report_params.items():
            if key == 'pk':
                key = pk_field
            pdf.multi_cell(30,line_height, key.replace("_", " "), 0, "L", new_x="RIGHT", new_y="TOP", max_line_height=pdf.font_size)
            pdf.multi_cell(param_width,line_height, value, 0, "L", new_x="RIGHT", new_y="TOP", max_line_height=pdf.font_size)
            if newline_print_counter == 2:
                pdf.ln(pdf.font_size *1.5)
                newline_print_counter = 0
            newline_print_counter += 1
    else:
        pdf.multi_cell(30,line_height, "N/A", 0, "L", new_x="RIGHT", new_y="TOP", max_line_height=pdf.font_size)
    pdf.ln()


def estimate_lines_needed(self, iter, col_width: float) -> int:
    font_width_in_mm = (
        self.font_size_pt * 0.33 * 0.6
    )  # assumption: a letter is half his height in width, the 0.5 is the value you want to play with
    max_cell_text_len_header = max([len(str(col)) for col in iter])  # how long is the longest string?
    return math.ceil(max_cell_text_len_header * font_width_in_mm / col_width)

def create_listview_index_value(data):
    ListView_index_values = []
    for field in sort_fields:
        if field == pk_field:
            ListView_index_values.append(data['pk'])
        else:
            ListView_index_values.append(data.get(field))
    STARK_ListView_sk = "|".join(ListView_index_values)
    return STARK_ListView_sk

def get_all_by_old_parent_value(old_pk_val, sk = default_sk):
    
    string_filter = " #attribute = :old_parent_value"
    object_expression_value = {':sk' : {'S' : sk},
                                ':old_parent_value': {'S' : old_pk_val}}
    ExpressionAttributeNamesDict = {
        '#attribute' : 'Module_Group',
    }
    response = ddb.query(
        TableName=ddb_table,
        IndexName="STARK-ListView-Index",
        Select='ALL_ATTRIBUTES',
        ReturnConsumedCapacity='TOTAL',
        FilterExpression=string_filter,
        KeyConditionExpression='sk = :sk',
        ExpressionAttributeValues=object_expression_value,
        ExpressionAttributeNames=ExpressionAttributeNamesDict
    )
    raw = response.get('Items')
    items = []
    for record in raw:
        item = {}
        item['pk'] = record.get('pk', {}).get('S','')
        item['sk'] = record.get('sk',{}).get('S','')
        item['Descriptive_Title'] = record.get('Descriptive_Title',{}).get('S','')
        item['Target'] = record.get('Target',{}).get('S','')
        item['Description'] = record.get('Description',{}).get('S','')
        item['Module_Group'] = record.get('Module_Group',{}).get('S','')
        item['Is_Menu_Item'] = record.get('Is_Menu_Item',{}).get('BOOL','')
        item['Is_Enabled'] = record.get('Is_Enabled',{}).get('BOOL','')
        item['Icon'] = record.get('Icon',{}).get('S','')
        item['Priority'] = record.get('Priority',{}).get('N','')
        item['STARK-ListView-sk'] = record.get('STARK-ListView-sk',{}).get('S','')
        items.append(item)

    return items

def get_fields(fields, sk = default_sk):

    dd_arguments = {}
    next_token = 'initial'
    items = []
    while next_token != None:
        next_token = '' if next_token == 'initial' else next_token
        dd_arguments['TableName']=ddb_table
        dd_arguments['IndexName']="STARK-ListView-Index"
        dd_arguments['Limit']=5
        dd_arguments['ReturnConsumedCapacity']='TOTAL'
        dd_arguments['KeyConditionExpression']='sk = :sk'
        dd_arguments['ExpressionAttributeValues']={
            ':sk' : {'S' : sk}
        }

        if next_token != '':
            dd_arguments['ExclusiveStartKey']=next_token

        response = ddb.query(**dd_arguments)
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
        #Get the "next" token, pass to calling function. This enables a "next page" request later.
        next_token = response.get('LastEvaluatedKey')

    return items