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
    col_list = []
    for keys in columns:
        col_list.append(keys)
    col_to_edit = col_list[randint(0,len(col_list) - 1)]
    col_type = set_type(columns[col_to_edit])
    test_data_for_edit = "'Testing Edit'"
    if col_type == 'SS':
        test_data_for_edit = ["Testing Edit"]
    elif col_type == 'N':
        test_data_for_edit = "'20'"

    col_to_edit_varname = converter.convert_to_system_name(col_to_edit)
    
    source_code = f"""\
    #Python Standard Library
    import json
    from moto import mock_dynamodb
    import boto3
    import pytest

    import {entity_varname} as {entity_to_lower}
    import stark_core as core

    def test_map_results(get_{entity_to_lower}_data):

        mapped_item = {entity_to_lower}.map_results(get_{entity_to_lower}_data)
        pass
        
    def test_create_listview_index_value(set_{entity_to_lower}_payload):

        assert set_{entity_to_lower}_payload['pk'] == {entity_to_lower}.create_listview_index_value(set_{entity_to_lower}_payload)

    @mock_dynamodb
    def test_add(use_moto,set_{entity_to_lower}_payload):
        use_moto()
        ddb = boto3.client('dynamodb', region_name=core.test_region)
        {entity_to_lower}.add(set_{entity_to_lower}_payload, 'POST', ddb)
        assert  {entity_to_lower}.resp_obj['ResponseMetadata']['HTTPStatusCode'] == 200
        
    @mock_dynamodb
    def test_get_by_pk(use_moto,set_{entity_to_lower}_payload):
        use_moto()
        ddb = boto3.client('dynamodb', region_name=core.test_region)
        {entity_to_lower}.add(set_{entity_to_lower}_payload, 'POST', ddb)
        response  = {entity_to_lower}.get_by_pk(set_{entity_to_lower}_payload['pk'], set_{entity_to_lower}_payload['sk'], ddb)

        assert set_{entity_to_lower}_payload['pk'] == response['item']['{pk_varname}']

    @mock_dynamodb
    def test_get_all(use_moto,set_{entity_to_lower}_payload):
        use_moto()
        ddb = boto3.client('dynamodb', region_name=core.test_region)
        {entity_to_lower}.add(set_{entity_to_lower}_payload, 'POST', ddb)
        set_{entity_to_lower}_payload['pk'] = 'Test3'
        {entity_to_lower}.add(set_{entity_to_lower}_payload, 'POST', ddb)
        set_{entity_to_lower}_payload['pk'] = 'Test4'
        {entity_to_lower}.add(set_{entity_to_lower}_payload, 'POST', ddb)
        set_{entity_to_lower}_payload['pk'] = 'Test1'
        {entity_to_lower}.add(set_{entity_to_lower}_payload, 'POST', ddb)
        response  = {entity_to_lower}.get_all('{entity_varname}|Listview', None, ddb)
        # print(response)
        assert len(response[0]) == 4

    @mock_dynamodb
    def test_edit(use_moto,set_{entity_to_lower}_payload):
        use_moto()
        ddb = boto3.client('dynamodb', region_name=core.test_region)
        {entity_to_lower}.add(set_{entity_to_lower}_payload, 'POST', ddb)
        set_{entity_to_lower}_payload['{col_to_edit_varname}'] = {test_data_for_edit}
        {entity_to_lower}.edit(set_{entity_to_lower}_payload, ddb)

        assert set_{entity_to_lower}_payload['{col_to_edit_varname}'] == {entity_to_lower}.resp_obj['Attributes']['{col_to_edit_varname}']['{col_type}']

    @mock_dynamodb
    def test_delete(use_moto,set_{entity_to_lower}_payload):
        use_moto()
        ddb = boto3.client('dynamodb', region_name=core.test_region)
        {entity_to_lower}.add(set_{entity_to_lower}_payload, 'POST', ddb)
        {entity_to_lower}.delete(set_{entity_to_lower}_payload, ddb)
        response  = {entity_to_lower}.get_all('{entity_varname}|Listview', None, ddb)
        assert len(response[0]) == 0
    """

    return textwrap.dedent(source_code)

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