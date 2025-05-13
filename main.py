from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
import datetime
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# === CONFIGURATION ===
blob_connection_string = os.getenv("blob_connection_string")
input_container_name = os.getenv("doc_container_name")
output_container_name = os.getenv("parsed_container_name")  # name of output container in Blob Storage

endpoint = os.getenv("endpoint")
key = os.getenv("key")

# === INIT CLIENTS ===
blob_service_client = BlobServiceClient.from_connection_string(blob_connection_string)
input_container_client = blob_service_client.get_container_client(input_container_name)
output_container_client = blob_service_client.get_container_client(output_container_name)

# === Ensure output container exists ===
try:
    output_container_client.create_container()
except Exception as e:
    print(f"Output container already exists or error: {e}")

document_client = DocumentAnalysisClient(endpoint, AzureKeyCredential(key))

# === LIST BLOBS + GENERATE SAS + PROCESS ===
for blob in input_container_client.list_blobs():
    # Generate SAS URL for each blob
    sas_token = generate_blob_sas(
        account_name=blob_service_client.account_name,
        container_name=input_container_name,
        blob_name=blob.name,
        account_key=blob_service_client.credential.account_key,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    )

    blob_url = f"https://{blob_service_client.account_name}.blob.core.windows.net/{input_container_name}/{blob.name}?{sas_token}"

    print(f"Processing {blob.name}...")

    poller = document_client.begin_analyze_document_from_url("prebuilt-read", blob_url)
    result = poller.result()

    # Extract text
    output_json = []
    for page in result.pages:
        text = " ".join([line.content for line in page.lines])
        output_json.append({"page": page.page_number, "text": text})

    # Serialize JSON to string
    json_str = json.dumps(output_json, ensure_ascii=False, indent=2)

    # Upload JSON string as blob
    json_blob_name = blob.name.replace(".pdf", ".json")
    output_container_client.upload_blob(name=json_blob_name, data=json_str, overwrite=True)

    print(f"✅ Saved parsed {json_blob_name} to container '{output_container_name}'")

print("🎉 All files processed and saved to Azure Blob Storage!")
