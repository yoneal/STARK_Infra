#STARK Code Generator component.
#Produces the customized dynamic content for a STARK system

#Python Standard Library
import base64
import textwrap

#Private modules
import convert_friendly_to_system as converter

def create(data):

    cicd_bucket    = data['cicd_bucket']
    website_bucket = data['website_bucket']

    source_code = f"""\
        {{
            "Parameters" : {{
                "UserCICDPipelineBucketNameParameter" : "{cicd_bucket}",
                "UserWebsiteBucketNameParameter" : "{website_bucket}"
            }}
        }}
        """

    return textwrap.dedent(source_code)