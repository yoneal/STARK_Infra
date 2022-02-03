#Python Standard Library
import base64
import json

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
    #S3-SETTINGS-END

    #Sample of removing invalid characters in bucket name, replacing with acceptable ones
    #FIXME: This definitely needs to be done by a shared common library instead of in-lined like this.
    s3_static_bucket_name = s3_static_bucket_name.replace("_", "-")

    parsed =  {
        "Bucket Name": s3_static_bucket_name,
        "Error Document": "error.html",
        "Index Document": "index.html"
    }

    return parsed