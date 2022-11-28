#This is the Lambda function of the Lamba-backed custom resource used by
#   the STARK Code Generator (CFWriter) that will empty the website bucket 
#   for deletion when the user calls DELETE STACK.

#Python Standard Library
import base64
import json
import os

#Extra modules
import boto3
from crhelper import CfnResource

s3  = boto3.resource('s3')
helper = CfnResource() #We're using the AWS-provided helper library to minimize the tedious boilerplate just to signal back to CloudFormation

@helper.create
@helper.update
def do_nothing(event, _):
    pass

@helper.delete
def empty_bucket(event, _):
    target_bucket_name = event.get('ResourceProperties', {}).get('Bucket','')
    target_bucket      = s3.Bucket(target_bucket_name)

    if event.get('RequestType') in ['Delete']:
        #For non-versioned buckets, this would be enough to empty the bucket.
        #   For versioned buckets, though, it'd just create delete markers.
        #target_bucket.objects.all().delete()

        #For versioned buckets, we have to delete ALL versions.
        #   This also works for non-versioned buckets, so this is the
        #   "I really want to empty the damn bucket no matter what!" command.
        try:
            target_bucket.object_versions.all().delete()
        except Exception as error:
            print(target_bucket + "does not exist or already deleted")
            
        #FIXME: update when naming for raw and processed buckets are final
        trimmed_project_name = target_bucket_name[0:-19]
        analytics_bucket_suffix = ['-stark-analytics-raw', '-stark-analytics-processed', '-stark-analytics-athena']
        for suffix in analytics_bucket_suffix:
            try:
                target_bucket = s3.Bucket(trimmed_project_name + suffix)
                target_bucket.object_versions.all().delete()
            except Exception as error:
                print(trimmed_project_name + suffix + "does not exist or already deleted")

def lambda_handler(event, context):
    helper(event, context)
