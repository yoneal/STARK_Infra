#Python Standard Library
import base64
import textwrap

#Private modules
import convert_friendly_to_system as converter

def create(data):
  
    entity                = data["Entity"]
    raw_bucket_name       = data["Raw Bucket Name"]
    processed_bucket_name = data["Processed Bucket Name"]
    project_varname       = data["Project Name"]
    columns               = data["Columns"]
    pk                    = data["PK"]

    pk_varname     = converter.convert_to_system_name(pk)
    entity_varname = converter.convert_to_system_name(entity)

    source_code = f"""\
    import sys
    from awsglue.transforms import *
    from awsglue.utils import getResolvedOptions
    from pyspark.context import SparkContext
    from awsglue.context import GlueContext
    from awsglue.job import Job
    
    metadata = {{
                "{pk_varname}": {{
                    'value': '',
                    'key': 'pk',
                    'required': True,
                    'max_length': '',
                    'data_type': 'string',
                    'state': None,
                    'feedback': ''
                }},"""
        
    
    for col, col_type in columns.items():
        col_varname = converter.convert_to_system_name(col)
        data_type = set_data_type(col_type)
        source_code += f"""
                '{col_varname}': {{
                    'value': '',
                    'key': '',
                    'required': True,
                    'max_length': '',
                    'data_type': '{data_type}',
                    'state': None,
                    'feedback': ''
                }},""" 
                    
    source_code += f"""
    }}
                  
    args = getResolvedOptions(sys.argv, ["JOB_NAME"])
    sc = SparkContext()
    glueContext = GlueContext(sc)
    spark = glueContext.spark_session
    job = Job(glueContext)
    job.init(args["JOB_NAME"], args)

    # Script generated for node S3 bucket
    S3bucket_node1 = glueContext.create_dynamic_frame.from_options(
        format_options={{
            "quoteChar": '"',
            "withHeader": True,
            "separator": ",",
            "multiline": False,
            "optimizePerformance": False,
        }},
        connection_type="s3",
        format="csv",
        connection_options={{
            "paths": ["s3://{raw_bucket_name}/{entity_varname}/{entity_varname}.csv"],
            "recurse": True,
        }},
        transformation_ctx="S3bucket_node1",
    )

    metadata_mappings = []
    for field, item in metadata.items():
        metadata_mappings.append((field, item['data_type'], field, item['data_type']))

    # Script generated for node ApplyMapping
    ApplyMapping_node2 = ApplyMapping.apply(
        frame=S3bucket_node1,
        mappings=metadata_mappings,
        transformation_ctx="ApplyMapping_node2",
    )

    # Script generated for node S3 bucket
    S3bucket_node3 = glueContext.getSink(
        path="s3://{processed_bucket_name}/{entity_varname}/",
        connection_type="s3",
        updateBehavior="LOG",
        partitionKeys=[],
        compression="snappy",
        enableUpdateCatalog=True,
        transformation_ctx="S3bucket_node3",
    )
    S3bucket_node3.setCatalogInfo(
        catalogDatabase="stark_{project_varname.lower()}_db", catalogTableName="{entity_varname}"
    )
    S3bucket_node3.setFormat("glueparquet")
    S3bucket_node3.writeFrame(ApplyMapping_node2)
    job.commit()

    """
    return textwrap.dedent(source_code)
    
def set_data_type(col_type):

    #Default is 'S'. Defined here so we don't need duplicate Else statements below
    data_type = 'string'

    if isinstance(col_type, dict):
        #special/complex types
        if col_type["type"] in [ "int-spinner" ]:
            data_type = 'integer'

        if col_type["type"] in [ "decimal-spinner" ]:
            data_type = 'float'
        
        if col_type["type"] in [ "tags", "multiple choice" ]:
            data_type = 'list'

        if col_type["type"] == 'file-upload':
            data_type = 'file'
    
    elif col_type in [ "int", "number" ]:
        data_type = 'integer'

    elif col_type == 'date':
        data_type = 'date'

    return data_type