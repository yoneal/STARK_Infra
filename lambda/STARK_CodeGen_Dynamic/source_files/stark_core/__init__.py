import os
import stark_core.data_abstraction as data
import stark_core.security as sec
import stark_core.logging as log

ddb_table   = "[[STARK_DDB_TABLE_NAME]]"
bucket_name = "[[STARK_WEB_BUCKET]]"
region_name = os.environ['AWS_REGION']
test_region = 'eu-west-2'
page_limit  = 100
bucket_url  = f"{bucket_name}.s3.{region_name}.amazonaws.com/"
bucket_tmp  = f"{bucket_url}tmp/"
upload_dir  = f"uploaded_files/"
