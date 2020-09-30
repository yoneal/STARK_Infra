#Python Standard Library
import base64
import json
from collections import OrderedDict 

def parse(data):

    entities        = data['entities']
    data_model      = data['model']
    project_name    = data['project_name']
    project_varname = data['project_varname']


    #SQS-SETTINGS-START
    #We're looking at DDB because our SQS for now is really just for surge protection
    ddb_surge_protection      = False
    ddb_surge_protection_fifo = False

    for key in data_model:
        if key == "__STARK_advanced__":
            ddb_surge_protection      = data_model[key].get('ddb_surge_protection', False)
            ddb_surge_protection_fifo = data_model[key].get('ddb_surge_protection_fifo', False)
    #SQS-SETTINGS-END


    parsed = {}

    if ddb_surge_protection:
        if ddb_surge_protection_fifo:
            parsed["Queue Type"] = "FIFO"
            parsed["Queue Name"] = project_varname + "_write_queue_fifo"
        else:
            parsed["Queue Type"] = "Standard"
            parsed["Queue Name"] = project_varname + "_write_queue"
            parsed["DLQ Name"]   = project_varname + "_write_queue_dlq"

    return parsed