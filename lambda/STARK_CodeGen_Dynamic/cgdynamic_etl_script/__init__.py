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

    entity_varname = converter.convert_to_system_name(entity)

    source_code = f"""\ 
    import sys
    from awsglue.transforms import *
    from awsglue.utils import getResolvedOptions
    from pyspark.context import SparkContext
    from awsglue.context import GlueContext
    from awsglue.job import Job

    import {entity_varname}

    metadata = {entity_varname}.metadata
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
        metadata_mappings.append((field, item.data_type, field, item.data_type))

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
        catalogDatabase="{project_varname}_db", catalogTableName="{entity_varname}"
    )
    S3bucket_node3.setFormat("glueparquet")
    S3bucket_node3.writeFrame(ApplyMapping_node2)
    job.commit()

    """
    return textwrap.dedent(source_code)