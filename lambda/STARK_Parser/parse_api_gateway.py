#Python Standard Library
import base64
import json
from collections import OrderedDict 

def parse(data):

    entities = data['entities']
 
    #Entities will be converted to routes by the writer. Some transformation will be needed for non-URL friendly entity names
    parsed = { "entities": [] }
    for entity in entities:
        parsed['entities'].append(entity)

    return parsed