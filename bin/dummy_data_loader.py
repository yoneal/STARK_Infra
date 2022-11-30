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
import json
import datetime
import pprint

pp = pprint.PrettyPrinter(indent=4)

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
    to_save_data_list = []
    upload_keys = {}
    to_upload_files_mapping = []
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

            if metadata[key]['data_type'] == 'file':
                if item != "":
                    filename, file_ext = os.path.splitext(dummy_data_dir + "/" + entity_varname + "/upload_files/" + item)
                    uuid_filename = str(uuid.uuid4()) +file_ext
                    upload_keys.update({key: {'S': uuid_filename}})
                    to_upload_files_mapping.append({"orig_name":item,"new_name": uuid_filename})
            
            if metadata[key]['relationship'] == '1-M':
                sk_value = entity_varname + '|' + key
                many_data = {
                    'pk' : {'S': data[pk_field]},
                    'sk' : {'S': sk_value},
                    sk_value : {'S': item}
                }
                to_save_data_list.append(many_data)
                child_module = importlib.import_module(key)
                many_transformed_data = json.loads(item)
                #get 
                temp_dict = {}
                for child_key, child_items in child_module.metadata.items():
                    if child_items['data_type'] == 'file':
                        temp_child_upload_keys = []
                        for record in many_transformed_data:
                            file_name = ""
                            if item != "":
                                filename, file_ext = os.path.splitext(dummy_data_dir + "/" + entity_varname + "/upload_files/" + record[child_key])
                                uuid_filename = str(uuid.uuid4()) +file_ext
                                to_upload_files_mapping.append({"orig_name":record[child_key],"new_name": uuid_filename})
                            
                            temp_child_upload_keys.append(uuid_filename)

                        temp_dict.update({child_key: {'S': '||'.join(temp_child_upload_keys)}})   
                if len(temp_dict) > 0:        
                    upload_keys.update({f"many_{key}": {'M': temp_dict}})
            else:
                transformed_data.update({key: {data_type: value}})              

    if len(upload_keys) > 0:
        transformed_data.update({"STARK_uploaded_s3_keys": {'M': upload_keys}})

    to_save_data_list.append(transformed_data)
    return to_save_data_list, to_upload_files_mapping


print("Start dummy data loader script.")
start_time = datetime.datetime.now().replace(microsecond=0)
## Collect all data
dummy_table_list = {}

print("Scanning for CSV files..")
for dir in (os.listdir(dummy_data_dir)):
    files =  os.listdir(dummy_data_dir + "/" + dir)
    for file in files:
        filename, fileext = os.path.splitext(dummy_data_dir + "/" + dir+"/"+file)
        if '.csv' == fileext:
            with open(dummy_data_dir+ "/" + dir + "/" + file, 'r') as csv_file:
                print(f"CSV file for {dir} found, collecting data..")
                csv_raw = csv.DictReader(csv_file)
                table_data = []
                data_count = 0
                for row in csv_raw:
                    table_data.append(dict(row))
                    data_count += 1
            dummy_table_list.update({dir: table_data})
            print(f"Collected {data_count} rows from {dir}.")
            # os.unlink(dummy_data_dir+ "/" + dir + "/" + file)

## require python file of each table to get metadata
os.chdir("../lambda")
lambda_folder = os.getcwd()
sys.path = [lambda_folder] + sys.path
import stark_core
from stark_core import utilities

print("Start dumping data in Dynamodb..")
for entity, data in dummy_table_list.items():
    temp_module = importlib.import_module(entity)
    data_count = 0
    for each_data in data:
        data_count += 1
        transformed_data, to_upload_files_mapping = prepare_data(each_data, temp_module.metadata, entity)
        for each_data in transformed_data:
            ddb_arguments = {}
            ddb_arguments['TableName'] = stark_core.ddb_table
            ddb_arguments['Item'] = each_data
            response = ddb.put_item(**ddb_arguments)

        for index in to_upload_files_mapping:
            uuid_filename = index["new_name"]
            filename = index["orig_name"]
            with open(dummy_data_dir + "/" + entity +'/upload_files/'+filename, "rb") as f:
                utilities.save_object_to_bucket(f, uuid_filename, None, f"uploaded_files/{entity}")
        print("\rDumped ", data_count, f" data for {entity}.", end ="", sep='')
    print("")
print("Completed dumping of data.")
end_time = datetime.datetime.now().replace(microsecond=0)
print("Duration: ", end_time-start_time)



