#!/bin/bash


curl -m 59 -X POST 
https://us-east4-stg-cca-23f7.cloudfunctions.net/wf-configure
 \

-H "Authorization: bearer $(gcloud auth print-identity-token)" \

-H "Content-Type: application/json" \

-d '{

    "context": {

        "client_id": "butterfly"

    },

    "function_config": {

        "functions": {

            "deepgram": ["deepgram"]

        },

        "config_bucket_name": "247ai-stg-cca"

    }

}'

# curl -m 1780 -X POST 
https://us-east4-stg-cca-23f7.cloudfunctions.net/wf-configure
 \

# -H "Authorization: bearer $(gcloud auth print-identity-token)" \

# -H "Content-Type: application/json" \

# -d '{

#      "context": {

#         "gcp_project": "cca-sandbox-329818",

#         "gcp_location": "us-east4",

#         "client_id": "client_abc"

#      },

#      "input_files":{

#         "source_file":{

#             "bucket_name":"knjhfkjhg",

#             "full_path": "folder1/MISSING-83f01231-6f24-48dc-8aa0-b23518041188.wav",

#             "version": "1685071015507797",

#             "uploaded": "2023-05-26T08:05:24.794Z"

#         }

#      },

#      "function_config": {

#         "label_tags": {"client":"ci_client","step":"ci_step","type":"ci_media_type"},

#         "functions": {

#             "wf-process-media": 

#                             ["deepgram",

#                             "process-audio",

#                             "test"],

#             "wf-transcribe":

#                         ["deepgram",

#                         "process-transcript"] 

#         },

#         "config_bucket_name": "247ai-cca-sandbox"

#      }

# }'

# -d '{

#     "gcp_project": "cca-sandbox-329818",

#     "gcp_location": "us-east4",

#     "client_id": "client_abc",

#     "bucket_name": "247ai-cca-sandbox-workflow-test",

#     "file_path": "folder1/pexels-artem-podrez-5752729-3840x2160-30fps.mp4",

#     "file_version": "1685088324694467",

#     "file_size": "865324",

#     "file_name": "folder1/pexels-artem-podrez-5752729-3840x2160-30fps.mp4",

#     "file_content_type": "video/mp4",

#     "staging_bucket_name":"247ai-cca-sandbox-workflow-test-stage",

#     "signing_account": "cca-sandbox-functions@cca-sandbox-329818.iam.gserviceaccount.com"

# }'

# -d '{

#     "gcp_project": "cca-sandbox-329818",

#     "gcp_location": "us-east4",

#     "client_id": "client_abc",

#     "bucket_name": "247ai-cca-sandbox-workflow-test",

#     "file_path": "folder1/nginx_fixed.txt",

#     "file_version": "1685088239644876",

#     "file_size": "865324",

#     "file_name": "MISSING-83f01231-6f24-48dc-8aa0-b23518041188.wav",

#     "file_content_type": "application/txt",

#     "staging_bucket_name":"247ai-cca-sandbox-workflow-test-stage",

#     "signing_account": "cca-sandbox-functions@cca-sandbox-329818.iam.gserviceaccount.com"

# }'



######################### NEW 
#!/bin/bash

# Replace with your Azure Function App URL
function_url=""  ###"https://<function-app-name>.azurewebsites.net/api/<function-name>"

# Replace with your Azure Function App key or any other authentication mechanism
api_key=""  ###"your-api-key"

curl -m 59 -X POST "$function_url" \
-H "x-functions-key: $api_key" \
-H "Content-Type: application/json" \
-d '{
    "context": {
        "client_id": "butterfly"
    },
    "function_config": {
        "functions": {
            "deepgram": ["deepgram"]
        },
        "config_bucket_name": "247ai-stg-cca"
    }
}'