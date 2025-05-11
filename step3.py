import os
import json
from openai import OpenAI
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# === CONFIGURATION ===
openai_endpoint = os.getenv("openai_endpoint")
openai_key = os.getenv("openai_key")
deployment_name = os.getenv("deployment_name")

blob_connection_string = os.getenv("blob_connection_string")
parsed_container_name = os.getenv("parsed_container_name")
embedding_container_name = os.getenv("embeddings_container_name")

# === INIT CLIENTS ===
openai_client = OpenAI(
    api_key=openai_key,
    base_url=openai_endpoint,
    default_query={"api-version": "2023-05-15"},
)

blob_service_client = BlobServiceClient.from_connection_string(blob_connection_string)
parsed_container_client = blob_service_client.get_container_client(parsed_container_name)
embedding_container_client = blob_service_client.get_container_client(embedding_container_name)

# === PROCESS EACH JSON FILE ===
for blob in parsed_container_client.list_blobs():
    if not blob.name.endswith(".json"):
        continue

    blob_data = parsed_container_client.download_blob(blob.name).readall()
    pages = json.loads(blob_data)

    for page in pages:
        page_text = page["text"]
        if not page_text.strip():
            continue  # skip empty pages

        response = openai_client.embeddings.create(
            model=deployment_name,
            input=[page_text]
        )
        embedding = response.data[0].embedding

        output = {
            "embedding": embedding,
            "text": page_text,
            "source": blob.name,
            "page": page["page"]
        }

        json_blob_name = blob.name.replace(".json", f".page{page['page']}.embedding.json")
        embedding_container_client.upload_blob(
            name=json_blob_name,
            data=json.dumps(output),
            overwrite=True
        )

        print(f"✅ Embedded page {page['page']} of {blob.name} → {json_blob_name}")

print("🎉 All embeddings generated and uploaded!")
