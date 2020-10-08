#STARK Code Generator component.
#Produces the customized dynamic content for a STARK system

#Python Standard Library
import base64
import textwrap

#Private modules
import convert_friendly_to_system as converter

def create(data):

    entities  = data["Entities"]

    #FIXME: See FIXME note in source_code itself
    source_code = f"""\
        import base64
        import json

        def lambda_handler(event, context):

            #FIXME:
            #For now, this just returns a hard-coded JSON result,
            #   instead of querying DynamoDB or whatever our module config function is
            #   (it could be a YAML file in a private bucket, for example, to allow admin to easily change configs without dealing with DDB)
            modules_list = ["""
    
    #FIXME:
    #This is just a temporary implementation of randomly assigning colored boxes to our modules/
    #   Real implem should use default pretty graphics/icons, like in Cobalt
    i=0
    graphics = ["default_1", "default_2", "default_3", "default_4"]
    for entity in entities:
        entity_varname = converter.convert_to_system_name(entity)
        i+=1
        graphic = graphics[i % len(graphics)]
        source_code += f"""
                            {{
                                "title": "{entity}",
                                "description": "Add/Edit/Delete/View generic functions for the {entity} module",
                                "image": "images/{graphic}.png",
                                "image_alt": "{entity} graphic",
                                "href": "{entity_varname}.html"
                            }},"""
    source_code = source_code[:-1]

    source_code += f"""
                        ]

            return {{
                "isBase64Encoded": False,
                "statusCode": 200,
                "body": json.dumps(modules_list),
                "headers": {{
                    "Content-Type": "application/json",
                }}
            }}
        """

    return textwrap.dedent(source_code)