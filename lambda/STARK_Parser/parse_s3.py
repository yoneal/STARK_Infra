#Python Standard Library
import base64
import json
import convert_friendly_to_system as converter


def parse(data):

    data_model      = data['data_model']
    project_varname = data['project_varname']

    #S3-SETTINGS-START
    s3_static_bucket_name = ""

    for key in data_model:
        if key == "__STARK_advanced__":
            s3_static_bucket_name = data_model[key].get('s3_static_bucket_name', "")
            s3_webserve_only      = data_model[key].get('s3_webserve_only', True)

    if s3_static_bucket_name == "":
        s3_static_bucket_name = project_varname + "-stark-dynamic-site"

    s3_static_bucket_name = converter.convert_to_system_name(s3_static_bucket_name, 's3')

    parsed =  {
        "Bucket Name": s3_static_bucket_name,
        "Error Document": "error.html",
        "Index Document": "index.html"
    }

    return parsed