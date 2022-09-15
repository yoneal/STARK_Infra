#STARK Code Generator component.
#Produces the test cases for modules of a STARK system

#Python Standard Library
import base64
from random import randint
import textwrap

#Private modules
import convert_friendly_to_system as converter

def create(data):
  
    pk             = data["PK"]
    entity         = data["Entity"]
    columns        = data["Columns"]
    ddb_table_name = data["DynamoDB Name"]
    bucket_name    = data['Bucket Name']
    relationships  = data["Relationships"]
    
    #Convert human-friendly names to variable-friendly names
    entity_varname  = converter.convert_to_system_name(entity)
    entity_to_lower = entity_varname.lower()
    pk_varname     = converter.convert_to_system_name(pk)

    default_sk     = entity_varname + "|info"
    with_upload    = False

    source_code = f"""\
    def get_data():
        data = {{}}
        data['pk'] = {{'S':'Test1'}}
        data['sk'] = {{'S':'{entity_varname}|Listview'}}"""
    for col, col_type in columns.items():
        col_varname = converter.convert_to_system_name(col)
        col_type_id = set_type(col_type)
        test_data   = generate_test_data(col_type)
        source_code += f"""
        data['{col_varname}'] = {{'{col_type_id}': {test_data}}}"""
    source_code += f"""

        return data

    def set_payload():
        payload = {{}}
        payload['pk'] = 'Test2'
        payload['orig_{pk_varname}'] = 'Test2'
        payload['sk'] = '{entity_varname}|Listview'"""
    for col, col_type in columns.items():
        col_varname = converter.convert_to_system_name(col)
        col_type_id = set_type(col_type)
        test_data   = generate_test_data(col_type)
        source_code += f"""
        payload['{col_varname}'] = {test_data}"""
    source_code += f"""
        payload['STARK-ListView-sk'] = '{pk_varname}'
        return payload
        """
        
    return textwrap.dedent(source_code)

def generate_test_data(col_type):

    string_test_data = ['Nico', 'Kim', 'JV', 'Jen', 'Ryan', 'Lorem Ipsum', 'John Doe', 'Sample', 'Test Data 1', 'Test Data 2']
    limit = len(string_test_data) - 1
    data = ""
    if isinstance(col_type, dict):
        #special/complex types
        if col_type["type"] in [ "int-spinner", "decimal-spinner" ]:
            data = randint(0, 100)
        
        if col_type["type"] in [ "tags", "multiple choice" ]:
            data = list(string_test_data[randint(0, limit)]
)    
    elif col_type in [ "int", "number" ]:
        data = randint(0, 100)
    
    else:
        data = string_test_data[randint(0, limit)]
          
    if isinstance(data, str):
        data = f"'{data}'"
    return data

def set_type(col_type):

    #Default is 'S'. Defined here so we don't need duplicate Else statements below
    col_type_id = 'S'

    if isinstance(col_type, dict):
        #special/complex types
        if col_type["type"] in [ "int-spinner", "decimal-spinner" ]:
            col_type_id = 'N'
        
        if col_type["type"] in [ "tags", "multiple choice" ]:
            col_type_id = 'SS'
    
    elif col_type in [ "int", "number" ]:
        col_type_id = 'N'

    return col_type_id