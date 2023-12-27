from datetime import datetime, timezone
from time import time
start_time = time()
from uuid import uuid1
# import google.cloud.logging
# client = google.cloud.logging.Client()
# client.setup_logging()
import logging
from io import StringIO
from pathlib import Path, PurePath
from dotenv import dotenv_values
import functions_framework
from flask import Request, g
# from google.cloud import storage
from flask_expects_json import expects_json
from os import environ
from util_input_validation import schema, Config
from util_helpers import handle_bad_request, handle_exception
from json import dumps, loads
import requests

# Azure Function Imports
import logging
import azure.functions as func
from azure.storage.blob import BlobServiceClient

# Azure Storage Client
storage_account_connection_string = "DefaultEndpointsProtocol=https;AccountName=fuctionappteststorage;AccountKey=QdII1YDI0vVb4/MBK6cvCDprW1B5Hl1pYXBNC/p6DXdiyk78MZJ6i34vxptFLGrEFuFv6N09bl9/+ASti08xcw==;EndpointSuffix=core.windows.net"
storage_client = BlobServiceClient.from_connection_string(storage_account_connection_string)


# from datetime import datetime
# from ciso8601 import parse_datetime
 
### GLOBAL Vars
 
### GLOBAL Vars

# Env Vars
# service = environ.get("FUNCTIONS_WORKER_RUNTIME")
 
# Instance-wide storage Vars
instance_id = str(uuid1())
run_counter = 0
# storage_client = storage.Client()
storage_client = BlobServiceClient.from_connection_string(storage_account_connection_string)
time_cold_start = time() - start_time
 
 
### MAIN
# Azure Function Decorator
@func.http_trigger(auth_level='function', methods=['POST'], route='main')
def main(request: func.HttpRequest):
    """HTTP Azure Function."""
    
    # Input Variables
    global run_counter
    run_counter += 1
    request_recieved = datetime.now(timezone.utc)
    request_json = request.get_json(silent=True)
    CONFIG = Config(request_json)
    del request_json
    g.context = {
        **CONFIG.context.toJson(), 
        "instance": instance_id,
        "instance_run": run_counter,
        "request_recieved": request_recieved.isoformat(),
    }

    response_json = {
        "client_buckets": None,
        "client_config": None,
        "staging_folder_path": None,
        "interaction_id": None,
        "status": "error",
    }

    # Get Config Container
    config_container_client = storage_client.get_container_client(CONFIG.function_config.config_container_name)

 
    """ if CONFIG.function_config.label_tags:
        # Find Client's Buckets by label
        landing, staging, content = find_client_buckets(
            storage_client,
            CONFIG.function_config.config_bucket_name,
            CONFIG.function_config.label_tags,
            CONFIG.context.client_id,
        )
        response_json["client_buckets"] = {
            "landing": landing.name if landing else None,
            "staging": staging.name if staging else None,
            "content": content.name if content else None,
        }"""
    response_json["client_buckets"] = {
        "content": "247ai-stg-cca-butterfly-content",
        "landing": "247ai-stg-cca-butterfly-video-landing",
        "staging": "247ai-stg-cca-butterfly-staging",
    }
    if CONFIG.function_config.functions:
        merged_config = get_config(
            config_container_client, CONFIG.context.client_id, CONFIG.function_config.functions
        )
        response_json["client_config"] = merged_config
 
    # Generate Staging Folder path
    if (
        CONFIG.input_files
        and CONFIG.input_files.source_file.uploaded
    ):
        interaction_id, staging_folder_path, content_folder_path = generate_staging_folder_details(
            CONFIG.context,
            CONFIG.input_files.source_file,
            request_recieved
        )
        response_json["staging_folder_path"] = staging_folder_path
        response_json["content_folder_path"] = content_folder_path
        response_json["interaction_id"] = interaction_id
 
    # Return with all the configuration info
    response_json["status"] = "success"
    return response_json, 200
    # except Exception as e:
    #     return handle_exception(e,CONFIG.context.toJson(),{x:y for x,y in CONFIG.toJson().items() if x !='context'})
 
 
def get_config(
    config_bucket: storage.Bucket,
    client_id: str,
    functions: Config.FunctionConfig.Functions,
):
    # Find config for requested functions
    config_list = {}
    # Create Struct to hold config i.e. {"deepgram":None, "process-transcript":None}
    for function_name, config_array in functions.items():
        for item in config_array:
            config_list[item] = None
    for config_item in config_list.keys():
        # Pull Config from bucket
        config_list[config_item] = get_client_function_config(
            config_bucket, client_id, config_item
        )
    # Now iterate through the original configuration requests,
    # and merge all of the found config in the order of the arrays
    merged_config = {}
    for function_name, config_array in functions.items():
        merged = {}
        for item in config_array:
            merged = {
                **merged,
                **(config_list[item] if config_list[item] else {}),
            }
        merged_config[function_name] = merged
    return merged_config
 
 
def generate_staging_folder_details(context: Config.Context, source_file: Config.InputFiles.InputFile, request_recieved: datetime):
    interaction_id = Path(source_file.full_path).stem
    if source_file.uploaded:
        trigger_file_upload_time = source_file.uploaded
        staging_folder_path = Path(
            str(trigger_file_upload_time.year),
            str(trigger_file_upload_time.month).zfill(2),
            str(trigger_file_upload_time.day).zfill(2),
            str(interaction_id),
            str(str(context.execution_start.strftime("%Y%m%d%H%M%S")) if context.execution_start else str(request_recieved.strftime("%Y%m%d%H%M%S")))
            + "_"
            + str(str(context.execution_id) if context.execution_id else str(source_file.version))
        ).as_posix()
        content_folder_path=Path(
            str(interaction_id),
            str(str(context.execution_start.strftime("%Y%m%d%H%M%S")) if context.execution_start else str(request_recieved.strftime("%Y%m%d%H%M%S")))
            + "_"
            + str(str(context.execution_id) if context.execution_id else str(source_file.version))
        ).as_posix()
    else:
        staging_folder_path = None
        content_folder_path = None
 
    return interaction_id, staging_folder_path, content_folder_path
 
def find_client_buckets(
    storage_client: storage.Client,
    bucket_prefix: str,
    label_tags: Config.FunctionConfig.LabelTags,
    client_id: str,
):
    landing = None
    staging = None
    content = None
    buckets = storage_client.list_buckets(prefix=bucket_prefix)
    for bucket in [
        bucket
        for bucket in buckets
        if label_tags.client in bucket.labels
        and bucket.labels[label_tags.client] == client_id
        and label_tags.step in bucket.labels
    ]:
        if bucket.labels[label_tags.step] == "landing":
            landing = bucket
        elif bucket.labels[label_tags.step] == "staging":
            staging = bucket
        elif bucket.labels[label_tags.step] == "content":
            content = bucket
    return landing, staging, content
 
 
def get_client_function_config(
    bucket: storage.Bucket, client_id: str, config_item: str
):
    releases_folder = PurePath(
        "config", "config-releases", client_id, config_item
    ).as_posix()
    in_use_path = PurePath(releases_folder, "in_use").with_suffix(".sh").as_posix()
    in_use_blob = bucket.get_blob(in_use_path)
    if not in_use_blob:
        return None
    in_use_vars = dotenv_values(stream=StringIO(in_use_blob.download_as_text()))
    if "DEPLOY_RELEASE_VERSION" not in in_use_vars:
        return None
    target_release_folder = PurePath(
        releases_folder, str(in_use_vars["DEPLOY_RELEASE_VERSION"])
    ).as_posix()
    target_config_path = (
        PurePath(target_release_folder, "config").with_suffix(".json").as_posix()
    )
    config_blob = bucket.get_blob(target_config_path)
    if not config_blob:
        return None
    return loads(config_blob.download_as_text())