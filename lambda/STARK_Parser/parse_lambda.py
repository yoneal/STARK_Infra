#Python Standard Library
import base64
import json

def parse(data, relationship = []):

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
        },
        "STARK_User": {
            "Memory": 128,
            "Arch": "arm64",
            "Timeout": 5,
            "Layers": [
                "STARKScryptLayer"
            ],
            "Dependencies": [
                "STARK_User_Roles",
                "STARK_User_Permissions",
            ]
        },
        "STARK_Module": {
            "Memory": 128,
            "Arch": "arm64",
            "Timeout": 5,
            "Dependencies": [
                "STARK_Module_Groups"
            ]
        },
        "STARK_User_Roles": {
            "Memory": 128,
            "Arch": "arm64",
            "Timeout": 5,
            "Dependencies": [
                "STARK_User",
                "STARK_User_Permissions",
            ]
        },
        "STARK_User_Permissions": {
            "Memory": 128,
            "Arch": "arm64",
            "Timeout": 5
        },
        "STARK_User_Sessions": {
            "Memory": 128,
            "Arch": "arm64",
            "Timeout": 5
        },
        "STARK_Module_Groups": {
            "Memory": 128,
            "Arch": "arm64",
            "Timeout": 5,
            "Dependencies": [
                "STARK_Module"
            ]
        }
    }
    for entity in entities:
        dependencies = []
        for relation in relationship:
            if entity == relation['parent']:
                dependencies.append(relation['child'])
        parsed[entity] = {
            "Memory": 128,
            "Arch": "arm64",
            "Timeout": 5,
            "Dependencies": dependencies
        }





    return parsed