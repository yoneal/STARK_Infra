#Python Standard Library
import base64
import json

def parse(data):

    data_model      = data['data_model']

    #CLOUDFRONT-SETTINGS-START
    enabled = False
    price_class = "200"
    default_root_object = "index.html"
    custom_domain_name = ""
    viewer_certificate_arn = None

    for key in data_model:
        if key == "__STARK_advanced__":
            for advance_config in data_model[key]:
                if advance_config == 'CloudFront':
                    enabled                    = data_model[key][advance_config].get('enabled', enabled)
                    price_class                = data_model[key][advance_config].get('price_class', price_class)
                    default_root_object        = data_model[key][advance_config].get('default_root_object', default_root_object)
                    custom_domain_name         = data_model[key][advance_config].get('custom_domain_name', custom_domain_name)
                    viewer_certificate_arn     = data_model[key][advance_config].get('viewer_certificate_arn', viewer_certificate_arn)
    #CLOUDFRONT-SETTINGS-END

    parsed = {
        "enabled": enabled,
        "price_class": price_class,
        "default_root_object": default_root_object,
        "custom_domain_name": custom_domain_name
    }

    if viewer_certificate_arn:
        parsed.update({
                "viewer_certificate_arn": viewer_certificate_arn
                })

    return parsed