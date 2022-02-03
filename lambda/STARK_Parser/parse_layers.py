#Python Standard Library
import base64
import json

def parse(data):
 
    parsed = [
        {
            "Name": "Local_mk5_CF_CustomResourceHelper",
            "Package": "CF_CustomResourceHelper_py39.zip",
            "Description": "Lambda-backed custom resource library for CloudFormation"
        },
        {
            "Name": "Local_mk5_PyYAML",
            "Package": "yaml_py39.zip",
            "Description": "YAML module for Python 3.x"
        },
        {
            "Name": "Local_mk5_scrypt",
            "Package": "STARK_scrypt_py39.zip",
            "Description": "STARK module for working with scrypt from the Python stdlib"
       },
    ]

    return parsed