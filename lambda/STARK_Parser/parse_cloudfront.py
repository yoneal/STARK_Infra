#Python Standard Library
import base64
import json
from collections import OrderedDict 

def parse(data):

    entities        = data['entities']
    data_model      = data['model']
    project_name    = data['project_name']
    project_varname = data['project_varname']

    #CLOUDFRONT-SETTINGS-START
    cf_enable = False
    cf_price_class = 100

    for key in data_model:
        if key == "__STARK_advanced__":
            cf_enable = data_model[key].get('cf_enable', False)
            cf_price_class = data_model[key].get('cf_price_class', 100)
    #CLOUDFRONT-SETTINGS-END

    parsed = {
        "Enabled": cf_enable,
        "Price Class": str(cf_price_class)
    }

    return parsed