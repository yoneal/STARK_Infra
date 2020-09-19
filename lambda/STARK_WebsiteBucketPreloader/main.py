#This is the Lambda function of the Lamba-backed custom resource used by
#   the STARK Code Generator (CFWriter) that will preload the standard
#   STARK HTML/CSS/JS files into the STARK-produced bucket.

#Python Standard Library
import base64
import json

#Extra modules
import boto3
from crhelper import CfnResource

s3  = boto3.resource('s3')
ssm = boto3.client('ssm')

response = ssm.get_parameter(Name="STARK_SourceBucketName")
source_bucket_name = response.get('Parameter', {}).get('Value')

helper = CfnResource() #We're using the AWS-provided helper library to minimize the tedious boilerplate just to signal back to CloudFormation

@helper.create
@helper.update
def preload_files(event, _):

    target_bucket_name = event.get('ResourceProperties', {}).get('Bucket','')
    target_bucket      = s3.Bucket(target_bucket_name)
    source_bucket      = s3.Bucket(source_bucket_name)

    for object in source_bucket.objects.all():
        copy_source = {
            'Bucket': source_bucket_name,
            'Key': object.key
        }
        target_bucket.copy(copy_source, object.key)
        s3.Object(target_bucket_name, object.key).Acl().put(ACL='public-read')


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
        target_bucket.object_versions.all().delete()


def lambda_handler(event, context):
    helper(event, context)
