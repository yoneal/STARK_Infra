#STARK Utility for creating lambda layers

#Python stdlib
import json
import os
import subprocess 
from zipfile import ZipFile

#Third-party
import convert_friendly_to_system as converter
import yaml
import boto3

install_dir_root   = "tmp"
default_py_version = "3.9"

default_response_headers = { 
    "Content-Type": "application/json", 
}

s3 = boto3.client('s3')

def lambda_handler(event, context):

    ########################
    #DATA FETCHING AND SETUP
    ########################

    #Mode defaults to "faas" (i.e., function as a service / lambda), unless explicitly set to "cli" (through STARK CLI usage)
    mode = event.get('mode', '')
    if mode == 'cli': pass
    else: mode == "faas"
        
    package = event.get('package', '')
    if package == '': 
        return {
            "isBase64Encoded": False,
            "statusCode": 400,
            "body": json.dumps("No package name supplied"),
            "headers": default_response_headers
        }

    #Implement arch-specific layer support here
    #arch = event.get('arch', '')
    #arch = os.environ.get('arch', '')

    if mode == "cli":
        project_name     = yaml.load(open("../cloud_resources.yml")).get('Project Name', '')
        project_name_sys = converter.convert_to_system_name(project_name)
        config_json      = json.load(open("../template_configuration.json"))
        cicd_bucket      = config_json['Parameters']['UserCICDPipelineBucketNameParameter']

    else:
        project_name = os.environ['PROJECT_NAME']
        cicd_bucket  = os.environ['CICD_BUCKET_NAME']

    py_version = event.get('py_version', '')
    if py_version == '': py_version = default_py_version

    layer_name  = f"{package}_py{py_version.replace('.','')}" 
    layer_dir   = os.path.join('python', 'lib', f"python{default_py_version}", "site-packages")
    install_dir = os.path.join(install_dir_root, layer_dir)


    ########################
    #START OF LAYER CREATION
    ########################

    #Install package in target directory
    cmd = ["pip", "install", f"--target={install_dir}", f"{package}"]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    output, error = process.communicate()

    print("OUTPUT: ")
    print(output)
    print("ERROR: ")
    print(error)

    #Zip layer directory (layer_dir only, not install_dir)
    os.chdir(install_dir_root)
    files = get_files(layer_dir)

    layer_package = f"{layer_name}.zip"
    with ZipFile(f"{layer_package}",'w') as zip:
        # writing each file one by one
        for file in files:
            zip.write(file)

    #Send zip file to CodeGen bucket
    response = s3.put_object(
        ACL='private',
        Body=open(layer_package, "rb"),
        Bucket=cicd_bucket,
        Key=f"{project_name_sys}/STARKLambdaLayers/{layer_package}"
    )

    print(response)

    if mode == "cli":
        #return layer package bytes
        response_body = open(layer_package, "rb").read()
        pass

    else:
        response_body = json.dumps("Layer created")

    return {
        "isBase64Encoded": False,
        "statusCode": 200,
        "body": response_body,
        "headers": default_response_headers
    }


def get_files(directory):
	files= []
	for dirpath, dirnames, filenames in os.walk(directory):
		for filename in filenames:
			filepath = os.path.join(dirpath, filename)
			files.append(filepath)
	return files