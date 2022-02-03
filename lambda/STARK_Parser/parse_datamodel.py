#Python Standard Library
import base64
import json

def parse(data):

    entities   = data['entities']
    data_model = data['data_model']
    parsed     = {}

    for entity in entities:
        parsed[entity] = {}
        parsed[entity]["pk"] = data_model.get(entity).get('pk')
        parsed[entity]["data"] = {}

        attributes = ''
        for column_dict in data_model.get(entity).get("data"):
            # `column_dict` here is a dictionary with a single key and value: { "Column Name": "Column Type" }
            #  So while we're accessing it now through a for loop, there's really just one value. MAY CHANGE IN FUTURE

            for key, value in column_dict.items():
                column   = key
                col_type = value

            parsed[entity]["data"][column] = col_type

            if isinstance(col_type, list):
                attributes += column + "(Enum: ["
                for item in col_type:
                    attributes += item  + ", "
                attributes = attributes[:-2]  
                attributes += "]),"           
            elif isinstance(col_type, str):
                attributes += column + "(" + col_type + "),"
        attributes = attributes[:-1]


    return parsed