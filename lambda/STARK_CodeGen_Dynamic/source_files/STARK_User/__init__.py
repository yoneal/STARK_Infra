#Python Standard Library
import base64
import json
import sys
from urllib.parse import unquote
import math

#Extra modules
import boto3
import stark_scrypt as scrypt
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
pk_field          = "Username"
default_sk        = "STARK|user|info"
sort_fields       = ["Username", ]
relationships     = []
metadata          = {
    'Username': {
        'value': '',
        'required': True,
        'max_length': '',
        'data_type': '',
        'state': None,
        'feedback': ''
    },
    'Full_Name': {
        'value': '',
        'required': True,
        'max_length': '',
        'data_type': '',
        'state': None,
        'feedback': ''
    },
    'Nickname': {
        'value': '',
        'required': True,
        'max_length': '',
        'data_type': '',
        'state': None,
        'feedback': ''
    },
    'Password_Hash': {
        'value': '',
        'required': True,
        'max_length': '',
        'data_type': '',
        'state': None,
        'feedback': ''
    },
    'Role': {
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
            payload = json.loads(base64.b64decode(event.get('body'))).get('STARK_User',"")
        else:    
            payload = json.loads(event.get('body')).get('STARK_User',"")

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
            data['pk'] = payload.get('Username')
            data['Full_Name'] = payload.get('Full_Name','')
            data['Nickname'] = payload.get('Nickname','')
            data['Role'] = payload.get('Role','')
            if payload.get('STARK_isReport', False) == False:
                data['orig_pk'] = payload.get('orig_Username','')
                data['sk'] = payload.get('sk', '')
                data['Password_Hash'] = payload.get('Password_Hash','')
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

        elif request_type == "detail":

            pk = event.get('queryStringParameters').get('Username','')
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
        "statusCode": 200,
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
        item = {}
        item['Username'] = record.get('pk', {}).get('S','')
        item['sk'] = record.get('sk',{}).get('S','')
        item['Full_Name'] = record.get('Full_Name',{}).get('S','')
        item['Nickname'] = record.get('Nickname',{}).get('S','')
        item['Role'] = record.get('Role',{}).get('S','')

        items.append(item)
    #NOTE: We explicitly left out the password hash. Since this is the generic "get all records" function, there's really no
    #   legitimate reason to get something as sensitive as the passwordh hash. Functionality that actually has to mass list
    #   users alongside their password hashes will have to use a function specifically made for that. Safety first.

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

    #FIXME: Mapping is duplicated code, make this DRY
    #Map to expected structure
    items = []
    for record in raw:
        item = {}
        item['Username'] = record.get('pk', {}).get('S','')
        item['sk'] = record.get('sk',{}).get('S','')
        item['Full_Name'] = record.get('Full_Name',{}).get('S','')
        item['Nickname'] = record.get('Nickname',{}).get('S','')
        item['Role'] = record.get('Role',{}).get('S','')
        items.append(item)
    #NOTE: We explicitly left out the password hash. Functionality that requires the user record along with the password hash should use 
    #       a specialized function instead of the generic "get" function.

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
    Full_Name = str(data.get('Full_Name', ''))
    Nickname = str(data.get('Nickname', ''))
    Password_Hash = str(data.get('Password_Hash', ''))
    Role = str(data.get('Role', ''))

    UpdateExpressionString = "SET #Full_Name = :Full_Name, #Nickname = :Nickname, #Role = :Role" 
    ExpressionAttributeNamesDict = {
        '#Full_Name' : 'Full_Name',
        '#Nickname' : 'Nickname',
        '#Role' : 'Role',
    }
    ExpressionAttributeValuesDict = {
        ':Full_Name' : {'S' : Full_Name },
        ':Nickname' : {'S' : Nickname },
        ':Role' : {'S' : Role },
    }

    #If Password_Hash is not an empty string, this means it's a password reset request.
    if Password_Hash != '':
        UpdateExpressionString += ", #Password_Hash = :Password_Hash"
        ExpressionAttributeNamesDict['#Password_Hash'] = 'Password_Hash'
        ExpressionAttributeValuesDict[':Password_Hash'] = {'S': scrypt.create_hash(Password_Hash)}

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

    assign_role_permissions({'Username': pk, 'Role': Role })

    return "OK"

def add(data):
    pk = data.get('pk', '')
    sk = data.get('sk', '')
    if sk == '': sk = default_sk
    Full_Name = str(data.get('Full_Name', ''))
    Nickname = str(data.get('Nickname', ''))
    Password_Hash = str(data.get('Password_Hash', ''))
    Role = str(data.get('Role', ''))

    item={}
    item['pk'] = {'S' : pk}
    item['sk'] = {'S' : sk}
    item['Full_Name'] = {'S' : Full_Name}
    item['Nickname'] = {'S' : Nickname}
    item['Password_Hash'] = {'S' : scrypt.create_hash(Password_Hash)}
    item['Role'] = {'S' : Role}

    if data.get('STARK-ListView-sk','') == '':
        item['STARK-ListView-sk'] = {'S' : create_listview_index_value(data)}
    else:
        item['STARK-ListView-sk'] = {'S' : data['STARK-ListView-sk']}
    response = ddb.put_item(
        TableName=ddb_table,
        Item=item,
    )

    assign_role_permissions({'Username': pk, 'Role': Role })

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
    item['Username'] = record.get('pk', {}).get('S','')
    item['sk'] = record.get('sk',{}).get('S','')
    item['Full_Name'] = record.get('Full_Name',{}).get('S','')
    item['Nickname'] = record.get('Nickname',{}).get('S','')
    item['Role'] = record.get('Role',{}).get('S','')
    return item

def generate_reports(mapped_results = [], display_fields=[], report_params = {}): 
    diff_list = []
    master_fields = ['Username', 'Full Name', 'Nickname', 'Role', ]
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

def create_pdf(data_to_tuple, master_fields, pdf_filename, report_params):
    #FIXME: PDF GENERATOR: can be outsourced to a layer, for refining 
    row_list = []
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
            pdf.multi_cell(col_width, row_height, datum, border=0, new_x="RIGHT", new_y="TOP", max_line_height=pdf.font_size, fill = True)
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
    pdf.multi_cell(0,line_height, "User Report", 0, 'C',
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

def assign_role_permissions(data):
    username  = data['Username']
    role_name = data['Role']
 
    from os import getcwd 
    STARK_folder = getcwd() + '/STARK_User_Roles'
    sys.path = [STARK_folder] + sys.path
    import STARK_User_Roles as user_roles

    response = user_roles.get_by_pk(role_name)
    permissions = response[0]['Permissions']
    
    sys.path[0] = getcwd() + '/STARK_User_Permissions'
    import STARK_User_Permissions as user_permissions
    data = {
        'pk': username,
        'Permissions': permissions
    }
    response = user_permissions.add(data)

    return "OK"

def get_all_by_old_parent_value(old_pk_val, sk = default_sk):
    
    string_filter = " #Role = :old_parent_value"
    object_expression_value = {':sk' : {'S' : sk},
                                ':old_parent_value': {'S' : old_pk_val}}
    ExpressionAttributeNamesDict = {
        '#Role' : 'Role',
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
        item['Full_Name'] = record.get('Full_Name',{}).get('S','')
        item['Nickname'] = record.get('Nickname',{}).get('S','')
        item['Role'] = record.get('Role',{}).get('S','')
        item['STARK-ListView-sk'] = record.get('STARK-ListView-sk',{}).get('S','')
        items.append(item)

    return items