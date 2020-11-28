import json


complex_json_value = """
__STARK_project_name__: 
Customer:
    pk: Customer ID
    data:
        - Customer Name: string
        - Gender: [ Male, Female, LGBTQ+ ]
        - Join Date: date
        - Preferred Customer: yes-no
        - Customer Type: 
            type: relationship
            has_one: Customer Type
            value: Customer Type
            display: Customer Type
        - Remarks: multi-line-string
Item:
    pk: Product Code
    data:
        - Title: string
        - In Stock:
            type: int-spinner
            min: 5
            max: 50
        - Weight in kg:
            type: decimal-spinner
            wrap: no-wrap
        - Categories:
            type: tags
            limit: 3
            values: [ "Regular", "Deluxe", "Premium" ]
        - Rating:
            type: rating
            max: 10
        - Variations Available:
            type: multiple choice
            values: [ "Small", "Medium", "Large", "XL"]
        - Description: multi-line-string
        - Packaging Type:
            type: radio button
            values: [ "Traditional Box", "Standard Cardboard", "Eco-Friendly" ]
        - Max Discount Rate:
            type: radio bar
            values: [ "None", "10%", "15%", "20%", "25%" ]
        - Last Update: time
Customer Type:
    pk: Customer Type
    data:
        - Description: multi-line-string
Document:
    pk: Document ID
    data:
        - Title: string
        - Revision: string
        - Description: string
"""

print (json.dumps(complex_json_value))