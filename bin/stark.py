import argparse
import os
from textwrap import dedent

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

args = parser.parse_args()

construct = args.construct
construct_type = construct[0]
construct_file = construct[1]

print(f"Will now create new {construct_type} construct, using {construct_file}...")

#New Module Construct: Sequence
#   1. STARK Parser - parse supplied YAML file (entity information)

#   2. Get entity information only (no need for API G creation, S3 creation, DDB creation; these are for New Project)
#   2.1 Specifically: parse_dynamodb (data model in cloud_resources['DynamoDB']['Models'], a.k.a. DDB Model) components
#   2.2 That basically encapsulates everything we need, and is the only thing CGDynamic and CGStatic really need (aside from S3 buckets & Git repos)
#   2.3 Note that while CGDynamic gets the entity list from CodeGen Metadata, it could also have just easily derived that from the DDB Models, like how CGStatic does it.

#   3. Create CGStatic output based on DDB Models from #2.1 (static HTML, CSS, and JS inside the `static` folder)

#   4. Create CGDynamic output based on DD Models from #2.1 (new lambda packages inside the `lambda` folder)

#   5. Add the generated cloud_resources DDB Model as new entries in the project's existing cloud_resources
#   5.1 Since that's a YAML file, read exsting file, load as python Dict. 
#   5.2 Add new entries to the cloud_resources Dict under DDB Models. 
#   5.3 Export back to YAML and write new cloud_resources (similar to how STARK_Parser does it)
