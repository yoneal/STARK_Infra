#Python Standard Library
import base64
import json

def parse(data):

    data_model      = data['data_model']

    #CLOUDFRONT-SETTINGS-START
    enable = False
    price_class = "PriceClass_200"
    default_root_object = "index.html"
    custom_domain_name = ""

    for key in data_model:
        if key == "__STARK_advanced__":
            for advance_config in data_model[key]:
                if advance_config == 'CloudFront':
                    enable              = data_model[key][advance_config].get('enable', False)
                    price_class         = data_model[key][advance_config].get('price_class', "PriceClass_200")
                    default_root_object = data_model[key][advance_config].get('default_root_object', "index.html")
                    custom_domain_name  = data_model[key][advance_config].get('custom_domain_name', "")
    #CLOUDFRONT-SETTINGS-END

    parsed = {
        "Enabled": enable,
        "PriceClass": price_class,
        "DefaultRootObject": default_root_object
    }

    return parsed