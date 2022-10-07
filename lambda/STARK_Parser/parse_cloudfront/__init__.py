#Python Standard Library
import base64
import json

def parse(data):

    data_model      = data['data_model']

    #CLOUDFRONT-SETTINGS-START
    cf_enable = True
    cf_price_class = "PriceClass_200"
    cf_default_root_object = "index.html"
    cf_custom_domain_name = ""

    for key in data_model:
        if key == "__STARK_advanced__":
            cf_enable              = data_model[key].get('cf_enable', False)
            cf_price_class         = data_model[key].get('cf_price_class', "PriceClass_200")
            cf_default_root_object = data_model[key].get('cf_default_root_object', "index.html")
            cf_custom_domain_name  = data_model[key].get('cf_custom_domain_name', "")
    #CLOUDFRONT-SETTINGS-END

    parsed = {
        "Enabled": cf_enable,
        "PriceClass": cf_price_class,
        "DefaultRootObject": cf_default_root_object
    }

    return parsed