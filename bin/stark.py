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
