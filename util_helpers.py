from typing import Union
from azure.functions import HttpRequest, HttpResponse
from google.auth import default, impersonated_credentials
import logging
from jsonschema import ValidationError
from json import dumps
from traceback import format_exc
from google.cloud import storage
from util_input_validation import Config

def impersonate_account(signing_account: str, lifetime: int):
    credentials, project = default()
    return impersonated_credentials.Credentials(
        source_credentials=credentials,
        target_principal=signing_account,
        target_scopes="https://www.googleapis.com/auth/devstorage.read_write",
        lifetime=lifetime,
    )

def create_outgoing_file_ref(file: Union[storage.Blob, Config.InputFiles.InputFile]):
    if isinstance(file, storage.Blob):
        bucket: storage.Bucket = file.bucket
        return {
            "bucket_name": str(bucket.name),
            "full_path": str(file.name),
            "version": str(file.generation),
            "size": str(file.size),
            "content_type": str(file.content_type),
            "uploaded": str(file.time_created.isoformat()) if file.time_created else None,
        }
    elif isinstance(file, Config.InputFiles.InputFile):
        return {
            "bucket_name": str(file.bucket_name),
            "full_path": str(file.full_path),
            "version": str(file.version),
            "size": str(file.size),
            "content_type": str(file.content_type),
            "uploaded": str(file.uploaded.isoformat()) if file.uploaded else None,
        }
    else:
        return {}


def handle_exception(context, e: Exception) -> HttpResponse:
    """Return JSON instead of HTML for HTTP errors."""
    request_json = context.bindings['req'].get_json()
    context_json = context.res
    msg = {
        "code": e.status_code if hasattr(e, 'status_code') else 500,
        "name": e.name,
        "description": e.description,
        "trace": format_exc(),
    }
    logging.error(dumps({**msg, "context": context_json, "request": request_json}))
    response = e.get_response()
    response.set_data(dumps(msg))
    response.mimetype = "application/json"
    return response


def handle_not_found(context, e: Exception) -> HttpResponse:
    request_json = context.bindings['req'].get_json()
    context_json = context.res
    msg = {"code": e.status_code if hasattr(e, 'status_code') else 404, "name": e.name, "description": e.description}
    logging.error(dumps({**msg, "context": context_json, "request": request_json}))
    response = e.get_response()
    response.set_data(dumps(msg))
    response.mimetype = "application/json"
    return response


def handle_bad_request(context, e: Exception) -> HttpResponse:
    msg = {
        "code": e.status_code if hasattr(e, 'status_code') else 400,
        "name": e.name,
        "description": e.description,
    }
    try:
        request_json = context.bindings['req'].get_json()
        context_json = request_json.pop("context")
        if isinstance(e.description, ValidationError):
            original_error = e.description
            msg = {
                **msg,
                "name": "Validation Error",
                "description": original_error.message,
                "trace": original_error.__str__(),
            }
        else:
            msg = {**msg, "trace": format_exc()}
        logging.warning(dumps({**msg, "context": context_json, "request": request_json}))
    except:
        request_json = context.bindings['req'].get_body()
        msg = {**msg, "trace": format_exc()}
        logging.warning(dumps({**msg, "request": str(request_json, "utf-8")}))
    response = e.get_response()
    response.set_data(dumps(msg))
    response.mimetype = "application/json"
    return response