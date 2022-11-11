#!/usr/bin/env python

import argparse
import os
import sys

from textwrap import dedent

import yaml
import boto3

import pprint
pprint = pprint.PrettyPrinter(indent=4)

#FIXME:
#   This assumes cwd is always the bin folder inside the project base directory
#   This needs to be updated after a real way to permanently specify project base dir within STARK CLI
#   (so it can be triggered within anywhere within the project folder hierarchy) has been implemented
project_basedir = os.getcwd()[:-3]

#FIXME - make this function an import as a file within libstark
def create_iac_template(cloud_resources):
    with open('libstark/STARK_config.yml') as f:
        yml_config = yaml.safe_load(f.read())

    cleaner_service_token   = yml_config['Cleaner_ARN']
    prelaunch_service_token = yml_config['Prelaunch_ARN']
    codegen_bucket          = yml_config['CodeGen_Bucket_Name']

    #FIXME: CICD Bucket should be retrieved from template_configuration.json
    #       The one in STARK_config.yml is the CICD bucket for the main STARK infra.
    #       This is the default for each project, but that may be overridden by the devs through
    #           template_configuration.json, hence that's the canonical store when we need the project-specific CI/CD bucket 
    cicd_bucket = yml_config['CICD_Bucket_Name']
    
    data = {
        'cloud_resources': cloud_resources,
        'Cleaner_ARN': cleaner_service_token,
        'Prelaunch_ARN': prelaunch_service_token,
        'CICD_Bucket_Name': cicd_bucket,
        'CodeGen_Bucket_Name': codegen_bucket
    }
    cf_template = cgdynamic.create_template_from_cloud_resources(data)

    filename = project_basedir + '/template.yml'
    with open(filename, "w") as f:
        f.write(cf_template)

class ValidateConstruct(argparse.Action):
    def __call__(self, parser, args, values, option_string=None):
        valid_constructs = ('module')
        construct_type, yaml_file = values

        #Check if construct type requested is supported
        if construct_type not in valid_constructs:
            raise ValueError(f'invalid construct type "{construct_type}". Must be one of: {valid_constructs}')

        #Check if yaml file ends in '*.yml' or '*.yaml'
        if yaml_file[-4:].lower() == 'yaml' or yaml_file[-3:].lower() == 'yml':
            #Looks ok, gave a YAML file
            pass
        else:
            print(yaml_file)
            print(yaml_file[-3:].lower())
            print(yaml_file[-4:].lower())
            raise ValueError(f'new construct expects a YAML file. (Was given: {yaml_file})')

        #Check if yaml_file is readable
        if not os.path.isfile(yaml_file):
            raise ValueError(f'cannot read YAML file "{yaml_file}". Please verify path and filename.')

        setattr(args, self.dest, (construct_type, yaml_file))

class ValidateUpdateModule(argparse.Action):
    def __call__(self, parser, args, json_file, option_string=None):
        #Check if file ends in'*.json'
        if json_file[-4:].lower() == 'json':
            #Looks ok, gave a JSON file
            pass
        else:
            raise ValueError(f'Expected a JSON file. (Was given: "{json_file}")')

        #Check if json_file is readable
        if not os.path.isfile(json_file):
            raise ValueError(f'cannot read JSON file "{json_file}". Please verify path and filename.')

        setattr(args, self.dest, json_file)

class ValidateCDNActions(argparse.Action):
    def __call__(self, parser, args, values, option_string=None):
        valid_actions = ('deploy', 'status', 'create-certificate')
        action = values[0]

        if action not in valid_actions:
            raise ValueError(f'invalid construct type "{action}". Must be one of: {valid_actions}')
        setattr(args, self.dest, (action))

##############################################################################
#START OF MAIN STARK CLI CODE
##############################################################################
parser = argparse.ArgumentParser(
    description='STARK CLI, for creating serverless constructs for your application.',
    formatter_class=argparse.RawTextHelpFormatter,
)

parser.add_argument('--new', '-n',
                    required=False,
                    nargs=2,
                    dest='construct',
                    action=ValidateConstruct,
                    metavar=('{type}', '{YAML file}'),
                    help=dedent('''\
                    Create new STARK constructs.
                    This expects two paramaters:
                        [1] construct type (currently only "module" is accepted)
                        [2] full path and filename of your construct definition YAML''')
)

parser.add_argument('--update-modules',
                    required=False,
                    const='STARK_modules_data.json',
                    nargs="?",
                    dest='payload',
                    action=ValidateUpdateModule,
                    help=dedent('''\
                    Update the target database's registry of STARK Modules.
                    Optional parameter:
                        [1] full path and filename of your operation payload ''')
)

parser.add_argument('--cdn',
                    required=False,
                    nargs=1,
                    dest='construct',
                    action=ValidateCDNActions,
                    help=dedent('''\
                    Perform Cloudfront actions:
                        [1] deploy - Deploys CDN of your project
                        [2] status - Checks current status of deployed CDN
                        [3] create-certificate - Create certificate for custom domain name specified ''')
)

args = parser.parse_args()

construct = args.construct
construct_type = construct
if isinstance(construct, tuple):
    construct_type = construct[0]
    construct_file = construct[1]

if construct_type == "module":
    print(f"Will now create new {construct_type} construct, using {construct_file}...")

    #New Module Construct: Sequence
    #   1. STARK Parser - parse supplied YAML file (entity information)

    #   2. Get entity information only (no need for API G creation, S3 creation, DDB creation; these are for New Project)
    #   2.1 Specifically: parse_dynamodb (data model in cloud_resources['DynamoDB']['Models'], a.k.a. DDB Model) components
    #   2.2 That basically encapsulates everything we need, and is the only thing CGDynamic and CGStatic really need (aside from S3 buckets & Git repos)
    #   2.3 Note that while CGDynamic gets the entity list from CodeGen Metadata, it could also have just easily derived that from the DDB Models, like how CGStatic does it.

    #   3. Create CGDynamic output based on DD Models from #2.1 (new lambda packages inside the `lambda` folder)

    #   4. Create CGStatic output based on DDB Models from #2.1 (static HTML, CSS, and JS inside the `static` folder)

    #   5. Add the generated cloud_resources DDB Model as new entries in the project's existing cloud_resources
    #   5.1 Since that's a YAML file, read exsting file, load as python Dict.
    #   5.2 Add new entries to the cloud_resources Dict under DDB Models.
    #   5.3 Export back to YAML and write new cloud_resources (similar to how STARK_Parser does it)

    #1-2) STARK Parser
    #Add STARK_Parser folder to the beginning of sys.path
    import libstark.STARK_Parser.parser_cli as stark_parser
    cloud_resources, current_cloud_resources = stark_parser.parse(construct_file)
    print(cloud_resources)
    
    #3) CGDynamic
    #Replace STARK_Parser folder in sys.path with STARK_CodeGen_Dynamic
    import libstark.STARK_CodeGen_Dynamic.cgdynamic_cli as cgdynamic
    cgdynamic.create(cloud_resources, project_basedir)

    #4) CGStatic
    #Replace CGDynamic folder in sys.path with CGStatic
    import libstark.STARK_CodeGen_Static.cgstatic_cli as cgstatic
    cgstatic.create(cloud_resources, current_cloud_resources, project_basedir)

    #5) Updating cloud resources doc
    #FIXME: We are purposely only updating the Data Model and Lambda, because all other entries are just entity lists and
    #   are currently unused and redundant
    current_cloud_resources["Data Model"].update(cloud_resources["Data Model"])
    current_cloud_resources["Lambda"].update(cloud_resources["Lambda"])
    filename = project_basedir + "cloud_resources.yml"
    with open(filename, "wb") as f:
        f.write(yaml.dump(current_cloud_resources, sort_keys=False, encoding='utf-8'))

    #Create a new template.yml file based on the newly written cloud_resources.yml
    create_iac_template(current_cloud_resources)

    print("DONE")

elif construct_type == 'deploy':
    print("Enabling CloudFront deployment..")
    with open("../cloud_resources.yml", "r") as f:
        current_cloud_resources = yaml.safe_load(f.read())
        project_name            = current_cloud_resources["Project Name"]
    import libstark.STARK_CodeGen_Dynamic.cgdynamic_cli as cgdynamic
    cdn_domain_name = None
    filename = project_basedir + "cloud_resources.yml"
    current_cloud_resources["CloudFront"]['enabled'] = True
    with open(filename, "wb") as f:
        f.write(yaml.dump(current_cloud_resources, sort_keys=False, encoding='utf-8'))

    is_continue_create_iac = True
    custom_domain_name = current_cloud_resources["CloudFront"].get("custom_domain_name", "")
    viewer_certificate_arn = current_cloud_resources["CloudFront"].get("viewer_certificate_arn", None)

    if custom_domain_name != "":        
        is_continue_create_iac = False
        acm = boto3.client('acm', region_name="us-east-1")
        response = acm.describe_certificate(CertificateArn=viewer_certificate_arn).get('Certificate')
        status = response.get("Status")

        if status != "ISSUED":
            print("Certificate for Custom Domain Name:", custom_domain_name, 'is still pending for DNS validation. Validate to proceed')
        else:
            is_continue_create_iac = True      
    
    else:
        stack_name = f"STARK-project-{project_name.replace(' ','')}"

        ##fetch the physical distribution id of CloudFront
        cfn = boto3.resource('cloudformation')
        stack_resource = cfn.StackResource(stack_name, 'STARKCloudFront')
        distribution_id = stack_resource.physical_resource_id
        try:
            client = boto3.client("cloudfront")
            response = client.get_distribution(
                Id=distribution_id
            )
            cdn_domain_name = response['Distribution']['DomainName'] 
          
        except Exception as error :
                print(error)
    
    if is_continue_create_iac:
        print("Updating template.yml..")
        create_iac_template(current_cloud_resources)
        print("Done")
        print("Commit then push the changes to take effect.")
        if cdn_domain_name:
            print("Cloudfront Distribution Name:", cdn_domain_name)

elif construct_type == 'status':
    print("Checking status..")

    ## Get project name from cloud resources
    cloud_resources_dir = '../cloud_resources.yml'
    with open(cloud_resources_dir, "r") as f:
        current_cloud_resources = yaml.safe_load(f.read())
        project_name            = current_cloud_resources["Project Name"]

    ## compose stack name by trimming whitespaces in project name then append to project stack name template 
    stack_name = f"STARK-project-{project_name.replace(' ','')}"

    ##fetch the physical distribution id of CloudFront
    cfn = boto3.resource('cloudformation')
    stack_resource = cfn.StackResource(stack_name, 'STARKCloudFront')
    distribution_id = stack_resource.physical_resource_id
    try:
        client = boto3.client("cloudfront")
        response = client.get_distribution(
            Id=distribution_id
        )

        print("Distribution Domain Name:", response['Distribution']['DomainName']) 
        print("Distribution ID:", response['Distribution']['Id']) 
        print("Status:", response['Distribution']['Status'])
        print("Enabled:", response['Distribution']['DistributionConfig'].get('Enabled'))  

    except Exception as error :
            print(error)

elif construct_type == 'create-certificate':
    with open("../cloud_resources.yml", "r") as f:
        current_cloud_resources = yaml.safe_load(f.read())

    custom_domain_name = current_cloud_resources.get("CloudFront").get("custom_domain_name")

    try:
        if custom_domain_name:
            print("Custom Domain Name specified, checking for certificate..")
            new_cert = False
            acm = boto3.client('acm', region_name="us-east-1")
            viewer_certificate_arn = current_cloud_resources['CloudFront'].get("viewer_certificate_arn", None)

            if viewer_certificate_arn:
                print("Certificate found, checking status..")
                default_status = "Pending for Validation. "
            else:
                new_cert = True
                print("No certificate yet, creating..")
                default_status = ""
                response = acm.request_certificate(
                            DomainName= custom_domain_name,
                            ValidationMethod= 'DNS'
                )
                # print(response)
                viewer_certificate_arn = response['CertificateArn']
                current_cloud_resources.get("CloudFront").update({
                        'viewer_certificate_arn': viewer_certificate_arn
                    })    

                filename = project_basedir + "cloud_resources.yml"
                with open(filename, "wb") as f:
                    f.write(yaml.dump(current_cloud_resources, sort_keys=False, encoding='utf-8'))
                print("Certificate created.")
            
            domain_validation_options = None
            iteration = 1
            while domain_validation_options == None:
                if new_cert:
                    print("\rFetching validation requirements", "." * iteration, end ="", sep='')
                response = acm.describe_certificate(CertificateArn=viewer_certificate_arn)
                domain_validation_options = response.get('Certificate').get('DomainValidationOptions')[0].get("ResourceRecord", None)
                iteration += 1
                
            certificate = response.get('Certificate')    
            status = certificate.get("Status")
            if new_cert:
                print("")

            if status != "ISSUED":
                print(f"{default_status}Create the following DNS record for", certificate.get('DomainName'), "to complete the validation:")
                print("Name:", domain_validation_options.get('Name'))
                print("Type:", domain_validation_options.get('Type'))
                print("Value:", domain_validation_options.get('Value'))
            else:
                print("Certificate validated, you can deploy the CDN.")
        else:
            print("No Custom Domain Name specified in cloud_resources.yml")
    except Exception as error:
        print(error)