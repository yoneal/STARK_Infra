#STARK Code Generator component.
#Produces the customized dynamic content for a STARK system

#Python Standard Library
import base64
import textwrap
from random import randint

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
    
    i=0
    for entity in entities:
        entity_varname = converter.convert_to_system_name(entity)
        i+=1
        graphic = suggest_graphic(entity)
        source_code += f"""
                            {{
                                "title": "{entity}",
                                "description": "Add/Edit/Delete/View generic functions for the {entity} module",
                                "image": "images/{graphic}",
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

def suggest_graphic(entity_name):
    #FIXME: When STARK data modeling grammar is finalized, it should include a way for
    #   devs to include a type hint for the entity (e.g., "people") to guide the parser
    #   towards choosing a more appropriate default graphic.
    #   Should also include a way to directly specify the desired image name (e.g. "user.png")

    default_icon_map = {
        "award": ["award.png"],
        "archive": ["archive.png"],
        "book": ["book.png"],
        "commerce": ["shopping-bag.png", "shopping-cart.png"],
        "config": ["gear.png", "sliders.png"],
        "data": ["pie-chart.png"],
        "document": ["file-text.png", "folder.png"],
        "event": ["calendar.png"],
        "item": ["box.png","package.png"],
        "location": ["map.png", "map-pin.png"],
        "logistics": ["truck.png"],
        "person": ["user.png", "users.png"],
        "sales": ["dollar.png", "credit-card.png"],
        "tasks": ["clipboard.png"],
        "travel": ["briefcase.png"],
        "type": ["tag.png"],
    }

    abstract_icons = [ "square.png", "triangle.png", "circle.png", "hexagon.png", "star.png"]

    #The order of these types matter. Types that come first take precedence.
    entity_type_map = {
        "type": ["type", "category", "categories", "tag", "price"],
        "tasks": ["task", "to do", "todo", "to-do", "list"],
        "data": ["data", "report"],
        "award": ["award", "prize"],
        "archive": ["archive", "storage", "warehouse"],
        "book": ["book"],
        "commerce": ["order", "shop"],
        "config": ["config", "configuration", "settings", "option"],
        "document": ["document", "file", "form",],
        "event": ["event", "meeting", "date", "call", "conference"],
        "item": ["item", "package", "inventory"],
        "location": ["address", "place", "location", "country", "countries", "city", "cities", "branch", "office"],
        "logistics": ["delivery", "deliveries", "vehicle", "fleet", "shipment"],
        "person": ["customer", "agent", "employee", "student", "teacher", "person", "people", "human"],
        "sales": ["sale", "sale", "purchase", "money", "finance"],
        "travel": ["travel"],
    }

    suggested_type = ''
    entity_name = entity_name.lower()
    for type in entity_type_map:
        #First, try a naive match
        if entity_name in entity_type_map[type]:
            suggested_type = type

        #If no match, see if we can match by attempting to turn name to singular
        if suggested_type == '':
            if entity_name[-1] == "s":
                singular_name = entity_name[0:-1]
                if singular_name in entity_type_map[type]:
                    suggested_type = type

        #If no match, see if we can substr the type map entries into entity name
        if suggested_type == '':
            for keyword in entity_type_map[type]:
                if keyword in entity_name:
                    suggested_type = type


    #If still no match, abstract icons will be assigned to this entity
    if suggested_type == '':
        suggested_type = 'abstract'

    print(suggested_type)
    if suggested_type == 'abstract':
        limit = len(abstract_icons) - 1
        suggested_icon = abstract_icons[randint(0, limit)]
    else:
        limit = len(default_icon_map[suggested_type]) - 1
        suggested_icon = default_icon_map[suggested_type][randint(0, limit)]

    return suggested_icon




