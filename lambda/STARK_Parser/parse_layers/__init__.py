#Python Standard Library
import base64
import json

def parse(data):
 
    project_varname = data['project_varname']

    parsed = [
        {
            "Name": f"{project_varname}_CF_CustomResourceHelper",
            "Package": "CF_CustomResourceHelper_py39.zip",
            "Description": "Lambda-backed custom resource library for CloudFormation"
        },
        {
            "Name": f"{project_varname}_PyYAML",
            "Package": "yaml_py39.zip",
            "Description": "YAML module for Python 3.x"
        },
        {
            "Name": f"{project_varname}_Requests",
            "Package": "requests_py39.zip",
            "Description": "Requests module for Python 3.x"
        },
        {
            "Name": f"{project_varname}_scrypt",
            "Package": "STARK_scrypt_py39.zip",
            "Description": "STARK module for working with scrypt from the Python stdlib"
        },
        {
            "Name": f"{project_varname}_Fpdf2",
            "Package": "fpdf2_py39.zip",
            "Description": "PDF Generator module for Python"
       },
    ]

    return parsed