import os
import json
import uuid
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

# === Load environment variables
load_dotenv()

# === Config
search_endpoint = os.getenv("search_endpoint")
search_key = os.getenv("search_key")
index_name = os.getenv("index_name")

blob_connection_string = os.getenv("blob_connection_string")
embedding_container_name = os.getenv("embeddings_container_name")

# === Init clients
search_client = SearchClient(
    endpoint=search_endpoint,
    index_name=index_name,
    credential=AzureKeyCredential(search_key)
)

blob_service_client = BlobServiceClient.from_connection_string(blob_connection_string)
embedding_container_client = blob_service_client.get_container_client(embedding_container_name)

# === Loop through each embedding file
documents_to_upload = []

for blob in embedding_container_client.list_blobs():
    if not blob.name.endswith(".embedding.json"):
        continue

    blob_data = embedding_container_client.download_blob(blob.name).readall()
    data = json.loads(blob_data)

    document = {
        "id": str(uuid.uuid4()),  # Unique ID for index
        "text": data["text"],
        "source": data["source"],
        "page": data["page"],
        "embedding": data["embedding"]
    }

    documents_to_upload.append(document)

    # Upload in batches of 100
    if len(documents_to_upload) == 100:
        search_client.upload_documents(documents=documents_to_upload)
        print(f"✅ Uploaded 100 embeddings to index")
        documents_to_upload = []

# Upload remaining documents
if documents_to_upload:
    search_client.upload_documents(documents=documents_to_upload)
    print(f"✅ Uploaded final {len(documents_to_upload)} embeddings to index")

print("🎉 All documents uploaded to Azure AI Search index!")
