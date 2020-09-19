import base64
import json

def lambda_handler(event, context):

    #For now, this just returns a hard-coded JSON result,
    #instead of querying DynamoDB
    modules_list = [
                    {
                        "title": "Customers",
                        "description": "Manage your customer masterlist",
                        "image": "images/gray_customer.png",
                        "image_alt": "customers graphic",
                        "href": "customer.html"
                    },
                    {
                        "title": "Items",
                        "description": "Manage your item masterlist",
                        "image": "images/orange_items.png",
                        "image_alt": "items graphic",
                        "href": "items.html"
                    },
                    {
                        "title": "Sales",
                        "description": "Transactions and sales data",
                        "image": "images/green_sales.png",
                        "image_alt": "sales percent graphic",
                        "href": "sales.html"
                    },
                    {
                        "title": "Price Management",
                        "description": "Review and set effective prices",
                        "image": "images/blue_pricetag.png",
                        "image_alt": "price tag graphic",
                        "href": "prices.html"
                    }
                   ]

    return {
      "isBase64Encoded": False,
      "statusCode": 200,
      "body": json.dumps(modules_list),
      "headers": {
        "Content-Type": "application/json",
      }
    }

###Local testing only
# clouding = lambda_handler({},{})
# json_object = json.loads(clouding['body'])
# json_formatted_str = json.dumps(json_object, indent=2)
# print(json_formatted_str)
