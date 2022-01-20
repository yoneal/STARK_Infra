#Python Standard Library
import base64
import json
from collections import OrderedDict 

def parse(data):

    entities = data['entities']
 
    #Each entity will be its own lambda function, and will become integrations for API gateway routes
    parsed = { "entities": [] }
    for entity in entities:
        parsed['entities'].append(entity)

    return parsed