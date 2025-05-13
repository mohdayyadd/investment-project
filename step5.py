import os
from dotenv import load_dotenv
from openai import OpenAI
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient

load_dotenv()

# Config
openai_key = os.getenv("openai_key")
openai_endpoint = os.getenv("openai_endpoint")
embedding_model = os.getenv("deployment_name")

search_endpoint = os.getenv("search_endpoint")
search_key = os.getenv("search_key")
index_name = os.getenv("index_name")

# Clients
openai_client = OpenAI(
    api_key=openai_key,
    base_url=openai_endpoint,
    default_query={"api-version": "2023-05-15"}
)

search_client = SearchClient(
    endpoint=search_endpoint,
    index_name=index_name,
    credential=AzureKeyCredential(search_key)
)

# === Run a test query
query = "What was the revenue in 2023?"

# Step 1: Embed
response = openai_client.embeddings.create(
    model=embedding_model,
    input=[query]
)
query_vector = response.data[0].embedding

# Step 2: Vector Search
results = search_client.search(
    search_text=None,
    vector_queries=[{
        "vector": query_vector,
        "k": 3,
        "fields": "embedding",
        "kind": "vector"  # ✅ This line is essential
    }]
)

# Step 3: Print results
for r in results:
    print(f"[{r['source']}, page {r['page']}]")
    print(r["text"])
    print("-" * 50)
