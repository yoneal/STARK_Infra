#Python Standard Library
import base64
import json

def parse(data):

    entities        = data['entities']
    data_model      = data['model']
    project_name    = data['project_name']
    project_varname = data['project_varname']

    parsed = { }

    return parsed