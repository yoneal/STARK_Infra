#Python Standard Library
import base64
import json

def parse(data):

 
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
    }


    return parsed