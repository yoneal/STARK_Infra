#Python Standard Library
import base64
import json
from collections import OrderedDict 

def parse(data):

    entities        = data['entities']
    data_model      = data['model']
    project_name    = data['project_name']
    project_varname = data['project_varname']

    #DDB-SETTINGS-START
    #Lots of DDB config to get from data model, or just use defaults
    ddb_table_name            = ""
    ddb_auto_scaling          = False
    ddb_surge_protection      = False
    ddb_surge_protection_fifo = False
    ddb_capacity_type         = "provisioned"
    ddb_rcu_provisioned       = 3
    ddb_wcu_provisioned       = 3

    for key in data_model:
        if key == "__STARK_advanced__":
            ddb_table_name            = data_model[key].get('ddb_table_name', "")
            ddb_surge_protection      = data_model[key].get('ddb_surge_protection', False)
            ddb_surge_protection_fifo = data_model[key].get('ddb_surge_protection_fifo', False)
            ddb_auto_scaling          = data_model[key].get('ddb_auto_scaling', False)
            ddb_capacity_type         = data_model[key].get('ddb_capacity_type', "provisioned")
            ddb_rcu_provisioned       = data_model[key].get('ddb_rcu_provisioned', 3)
            ddb_wcu_provisioned       = data_model[key].get('ddb_wcu_provisioned', 3)

    if ddb_table_name == "":
        ddb_table_name = project_varname  + "_ddb"

    if ddb_auto_scaling:
        ddb_auto_scaling = "ENABLED"
    else:
        ddb_auto_scaling = "OFF"
    #DDB-SETTINGS-END


    parsed = {
        "Table Name": ddb_table_name,
        "Capacity Type": ddb_capacity_type,
        "Surge Protection": ddb_surge_protection,
        "Surge Protection FIFO": ddb_surge_protection_fifo,
        "Models": {}
    }

    if ddb_capacity_type == "provisioned":
        parsed["RCU"]          = ddb_rcu_provisioned
        parsed["WCU"]          = ddb_wcu_provisioned
        parsed["Auto Scaling"] = ddb_auto_scaling

    for entity in entities:
        parsed["Models"][entity] = {}
        parsed["Models"][entity]["pk"] = data_model.get(entity).get('pk')
        parsed["Models"][entity]["data"] = OrderedDict() 

        attributes = ''
        for column_dict in data_model.get(entity).get("data"):
            # `column_dict` here is a dictionary with a single key and value: { "Column Name": "Column Type" }
            #  So while we're accessing it now through a for loop, there's really just one value. MAY CHANGE IN FUTURE

            for key, value in column_dict.items():
                column   = key
                col_type = value

            parsed["Models"][entity]["data"][column] = col_type

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