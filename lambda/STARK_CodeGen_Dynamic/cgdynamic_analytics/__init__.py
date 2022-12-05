#STARK Code Generator component.

#Python Standard Library
import base64
import textwrap

import convert_friendly_to_system as converter

def create(data):
    entities              = data["Entities"]
    entities_varname = []
    for entity in entities:
        entities_varname.append(converter.convert_to_system_name(entity))

    source_code = f"""\
    import importlib
    import boto3
    import json
    
    import stark_core
    from stark_core import data_abstraction
    from stark_core import utilities

    def lambda_handler(event, context):
        entities = {entities_varname}

        #FIXME: Temporary solution to duplication of records due to multiple parquet files read in processed bucket
        #       Delete every files inside the processed bucket        
        client = boto3.client('s3')
        resp = client.list_objects(Bucket=stark_core.analytics_processed_bucket_name).get('Contents',{{}})
        for val in resp:
            client.delete_object(Bucket=stark_core.analytics_processed_bucket_name, Key=val["Key"])
        
        child_entity_for_one_to_many = []
        entities_to_dump_list = {{}}
        for entity in entities:

            entity_namespace = importlib.import_module(entity)

            for fields, dictionary in entity_namespace.metadata.items():
                if dictionary['relationship'] == "1-M":
                    child_entity_for_one_to_many.append({{'parent':entity, 'child': fields}})

            object_expression_values = {{':sk' : {{'S' : entity_namespace.default_sk}}}}
            items, aggregated_items = data_abstraction.get_report_data({{}} ,object_expression_values, "", False, entity_namespace.map_results)

            master_fields = []
            for key in entity_namespace.metadata.keys():
                master_fields.append(key)

            entities_to_dump_list.update({{entity: {{'data':items, 'headers': master_fields}}}})

        ##FIXME: might need refactoring
        for index in child_entity_for_one_to_many:
            ## get data one by one
            child_items = []
            many_sk = f"{{index['parent']}}|{{index['child']}}"
            parent_entity_namespace = importlib.import_module(index['parent'])
            pk_field = parent_entity_namespace.pk_field
            parent_data_list = entities_to_dump_list[index['parent']]['data']
            entities_to_dump_list[index['child']]['headers'] = [pk_field, *entities_to_dump_list[index['child']]['headers']]
            for key in parent_data_list:
                response = data_abstraction.get_many_by_pk(key[pk_field], many_sk)
                for each_child_record in json.loads(response[0][many_sk]['S']):
                    item = {{pk_field:key[pk_field], **each_child_record}}
                    child_items.append(item)
            entities_to_dump_list[index['child']]['data'] = child_items

        for entity, entity_data in entities_to_dump_list.items():
            items = entity_data['data']
            headers = entity_data['headers']
            report_list = []
            # print(headers)
            if len(items) > 0:
                for key in items:
                    temp_dict = {{}}
                    #remove primary identifiers and STARK attributes
                    if 'sk' in key:    
                        key.pop("sk")
                    if "STARK_uploaded_s3_keys" in key:
                        key.pop("STARK_uploaded_s3_keys")
                    for index, value in key.items():
                        temp_dict[index] = value
                    # print(temp_dict)
                    report_list.append(temp_dict)
                    
                csv_file, file_buff_value = utilities.create_csv(report_list, headers)
                ## Do not use csv filename provided by the create_csv function, instead use the entity varname
                #  so that each entity will only have one csv file making the dumper overwrite the existing file 
                #  everytime it runs.
                key_filename = entity + ".csv"
                utilities.save_object_to_bucket(file_buff_value, key_filename, stark_core.analytics_raw_bucket_name, entity)
    """
    return textwrap.dedent(source_code)


