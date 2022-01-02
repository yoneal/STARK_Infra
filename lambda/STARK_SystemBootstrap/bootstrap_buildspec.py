#STARK Code Generator component.
#Produces the customized dynamic content for a STARK system

#Python Standard Library
import base64
import textwrap

#Private modules
import convert_friendly_to_system as converter

def create(data):

    cicd_bucket     = data['cicd_bucket']
    project_varname = data['project_varname']

    source_code = f"""\
        version: 0.2

        phases:
            install:
                runtime-versions:
                    python: 3.8
            build:
                commands:
                - BUCKET={cicd_bucket}
                - aws cloudformation package --template-file template.yml --s3-bucket $BUCKET --s3-prefix {project_varname} --output-template-file outputtemplate.yml
                - aws s3 cp outputtemplate.yml s3://$BUCKET/{project_varname}/

        artifacts:
            files:
                - template.yml
                - outputtemplate.yml
                - template_configuration.json
        """

    return textwrap.dedent(source_code)