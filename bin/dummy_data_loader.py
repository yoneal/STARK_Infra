## Data loader to help devs dump data into dynamodb using a CSV file
#  To use this: 
#  1. Create a dummy_data folder inside the base directory of your stark generated project
#  2. Create a folder for the table you want to populate, the name should be the same as the table and it is case sensitive
#  3. Put the CSV file inside the table folder
#     3.1 Only one csv file should exist inside the table folder
#     3.2 Make sure the first column is for headers
#     3.3 Column Names should be exactly the same as the ones in metadata
#  4. Run the script
# 
#  For tables with upload fields, create a folder inside your table folder, name it upload_files
#  Add all the files to upload there 

import csv
import os
import importlib
import sys
import boto3
import uuid

ddb = boto3.client('dynamodb')
s3 = boto3.client('s3')
project_basedir = os.getcwd()[:-3]
dummy_data_dir = project_basedir + "dummy_data"

def set_type(col_type):

    #Default is 'S'. Defined here so we don't need duplicate Else statements below
    col_type_id = 'S'

    if col_type in [ "integer", "float" ]:
        col_type_id = 'N'
    
    elif col_type in [ "list" ]:
            col_type_id = 'SS'

    return col_type_id

def prepare_data(data, metadata, entity_varname):
    ## change key of pk field to 'pk' before passing to add function
    upload_keys = {}
    for key, item in metadata.items():
        if item['key'] == 'pk':
            pk_field = key
        
        if item['data_type'] == 'file':
            upload_keys.update({key: ''})
        

    transformed_data = {
            'pk' : {'S': data[pk_field]},
            'sk' : {'S': entity_varname + '|info'},
            'STARK-ListView-sk': {'S': data[pk_field]}
        }
    
    for key, item in data.items():
        if key == pk_field:
            pass
        else:
            value = item
            data_type = set_type(metadata[key]['data_type'])
            if data_type == 'SS':
                value = item.split(',')

            transformed_data.update({key: {data_type: value}})
            if metadata[key]['data_type'] == 'file':
                if item != "":

                    filename, file_ext = os.path.splitext(dummy_data_dir + "/" + entity_varname + "/upload_files/" + item)
                    upload_keys.update({key: {'S': str(uuid.uuid4()) +file_ext}})

    if len(upload_keys) > 0:
        transformed_data.update({"STARK_uploaded_s3_keys": {'M': upload_keys}})

    return transformed_data


## Collect all data
dummy_table_list = {}
for dir in (os.listdir(dummy_data_dir)):
    files =  os.listdir(dummy_data_dir + "/" + dir)
    for file in files:
        filename, fileext = os.path.splitext(dummy_data_dir + "/" + dir+"/"+file)
        if '.csv' == fileext:
            with open(dummy_data_dir+ "/" + dir + "/" + file, 'r') as csv_file:
                csv_raw = csv.DictReader(csv_file)
                table_data = []
                for row in csv_raw:
                    table_data.append(dict(row))
            dummy_table_list.update({dir: table_data})
            # os.unlink(dummy_data_dir+ "/" + dir + "/" + file)

## require python file of each table to get metadata
os.chdir("../lambda")
lambda_folder = os.getcwd()
sys.path = [lambda_folder] + sys.path
import stark_core
from stark_core import utilities

for entity, data in dummy_table_list.items():
    temp_module = importlib.import_module(entity)
    for each_data in data:
        transformed_data = prepare_data(each_data, temp_module.metadata, entity)
        ddb_arguments = {}
        ddb_arguments['TableName'] = stark_core.ddb_table
        ddb_arguments['Item'] = transformed_data
        response = ddb.put_item(**ddb_arguments)

        to_upload_keys = transformed_data.get('STARK_uploaded_s3_keys',{}).get('M',{})
        for key, file_from_map in to_upload_keys.items():
            uuid_filename = file_from_map['S']
            filename = transformed_data[key]['S']
            with open(dummy_data_dir + "/" + entity +'/upload_files/'+filename, "rb") as f:
                utilities.save_object_to_bucket(f, uuid_filename, None, f"uploaded_files/{entity}")



