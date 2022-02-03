#Python Standard Library
import base64
import json

def parse(data):

    entities = data['entities']
 
    #Each entity will be its own lambda function, and will become integrations for API gateway routes
    parsed = {
        "stark_login": {
            "Memory": 1790,
            "Arch": "arm64",
            "Timeout": 5,
            "Layers": [
                "STARKScryptLayer"
            ]
        },
        "stark_logout": {
            "Memory": 128,
            "Arch": "arm64",
            "Timeout": 5
        },
        "stark_sysmodules": {
            "Memory": 128,
            "Arch": "arm64",
            "Timeout": 5
        }
    }
    for entity in entities:
        parsed[entity] = {
            "Memory": 128,
            "Arch": "arm64",
            "Timeout": 5
        }





    return parsed