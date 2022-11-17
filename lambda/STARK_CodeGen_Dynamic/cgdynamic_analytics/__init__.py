#STARK Code Generator component.

#Python Standard Library
import base64
import textwrap

import convert_friendly_to_system as converter

def create(data):
    entities = data["Entities"]
    entities_varname = []
    for entity in entities:
        entities_varname.append(converter.convert_to_system_name(entity))

    source_code = f"""\
    import importlib
    import stark_core
    from stark_core import data_abstraction
    from stark_core import utilities

    def lambda_handler(event, context):
        entities = {entities_varname}

        for entity in entities:

            entity_namespace = importlib.import_module(entity)

            object_expression_values = {{':sk' : {{'S' : entity_namespace.default_sk}}}}
            items, aggregated_items = data_abstraction.get_report_data({{}} ,object_expression_values, "", False, entity_namespace.map_results)
            
            master_fields = []
            for key in entity_namespace.metadata.keys():
                master_fields.append(key.replace("_"," "))
                report_header = master_fields

            report_list = []
            if len(items) > 0:
                for key in items:
                    temp_dict = {{}}
                    #remove primary identifiers and STARK attributes    
                    key.pop("sk")
                    for index, value in key.items():
                        temp_dict[index.replace("_"," ")] = value
                    report_list.append(temp_dict)

                csv_file, file_buff_value = utilities.create_csv(report_list, report_header)
                utilities.save_object_to_bucket(file_buff_value, csv_file, stark_core.raw_analytics_bucket_name, entity)
    """
    return textwrap.dedent(source_code)


