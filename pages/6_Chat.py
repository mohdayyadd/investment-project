import os
import json
import re
import requests
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from datetime import datetime, timedelta, timezone
from html import escape

# Load environment variables
load_dotenv()

# === Config ===
openai_key = os.getenv("openai_key")
openai_endpoint = os.getenv("openai_endpoint")
embedding_model = os.getenv("deployment_name")

search_endpoint = os.getenv("search_endpoint")
search_key = os.getenv("search_key")
index_name = os.getenv("index_name")

gpt4o_uri = os.getenv("gpt-4o-uri")
container_name = os.getenv("parsed_container_name")
doc_container_name = os.getenv("doc_container_name")
connection_string = os.getenv("blob_connection_string")
account_key = os.getenv("blob_account_key")

# === Init clients ===
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

# === SAS Token Generator ===
def generate_sas_url(container, blob_name, expiry_minutes=60):
    if not account_key:
        raise ValueError("Missing blob_account_key in environment.")
    blob_service = BlobServiceClient.from_connection_string(connection_string)
    sas_token = generate_blob_sas(
        account_name=blob_service.account_name,
        container_name=container,
        blob_name=blob_name,
        account_key=account_key,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.now(timezone.utc) + timedelta(minutes=expiry_minutes)
    )
    return f"https://{blob_service.account_name}.blob.core.windows.net/{container}/{blob_name}?{sas_token}"

# === Streamlit UI ===
st.set_page_config(page_title="Ask in Chat", layout="centered")
st.title("🧠 Ask in Chat")

query = st.text_input("Ask your question:", placeholder="e.g. What was the revenue in 2023?")
submit = st.button("Get Answer")

if submit and query.strip():
    with st.spinner("Thinking..."):
        try:
            # Step 1: Embed the query
            embedding_response = openai_client.embeddings.create(
                model=embedding_model,
                input=[query]
            )
            query_vector = embedding_response.data[0].embedding

            # Step 2: Search the vector index
            results = search_client.search(
                search_text=None,
                vector_queries=[{
                    "vector": query_vector,
                    "k": 10,
                    "fields": "embedding",
                    "kind": "vector"
                }]
            )

            # Step 3: Clean and deduplicate
            seen_texts = set()
            cleaned_chunks = []
            for r in results:
                text = r["text"].strip()
                if not text or len(text.split()) < 30 or text in seen_texts:
                    continue
                seen_texts.add(text)
                cleaned_chunks.append({
                    "source": r.get("source", "").strip(),
                    "page": r.get("page", 1),
                    "text": text,
                    "score": r["@search.score"]
                })

            if not cleaned_chunks:
                st.warning("⚠️ No relevant content found in the documents.")
                st.stop()

            cleaned_chunks = sorted(cleaned_chunks, key=lambda x: -x["score"])[:4]
            context = "\n\n---\n\n".join([c["text"] for c in cleaned_chunks])

            # Step 4: Ask GPT-4o using the context
            headers = {
                "Content-Type": "application/json",
                "api-key": openai_key
            }

            payload = {
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a helpful assistant answering questions based strictly on the provided document context. "
                            "Always cite the source document file name (e.g., adnoc_financials.pdf) and the page number where the information came from, "
                            "formatted like this: (Source: adnoc_financials.pdf, Page 3). on a seperate line. "
                            "Do not guess or include information not explicitly stated in the provided context. "
                            "Do not summarize unrelated files. "
                            "Your goal is to deliver a precise, well-structured answer using only the content retrieved from the documents."
                        )
                    },
                    {
                        "role": "user",
                        "content": f"Answer the question: '{query}' using the context below:\n\n{context}"
                    }
                ],
                "temperature": 0.3,
                "max_tokens": 800
            }

            response = requests.post(gpt4o_uri, headers=headers, json=payload)

            if response.status_code == 200:
                try:
                    answer = response.json()["choices"][0]["message"]["content"]
                except (KeyError, IndexError):
                    answer = "⚠️ Unexpected response format from GPT-4o."
            else:
                answer = f"❌ Request failed: {response.status_code} - {response.text}"

            # === Display answer (safely, without markdown formatting)
            lines = answer.strip().count('\n') + 1
            dynamic_height = min(600, max(100, lines * 20))

            st.subheader("GPT-4o Answer")
            st.write(answer, unsafe_allow_html=True)

            # === Show attached documents (unique files with page groupings)
            st.subheader("Attached Source Documents")

            file_page_map = {}
            for chunk in cleaned_chunks:
                source = chunk.get("source", "").strip()
                page = chunk.get("page", 1)
                if not source:
                    continue
                file_page_map.setdefault(source, set()).add(page)

            for source, pages in file_page_map.items():
                try:
                    display_name = source.replace(".json", "").replace("-", " ").strip()
                    pdf_file = source.replace(".json", ".pdf")
                    sas_url = generate_sas_url(doc_container_name, pdf_file, expiry_minutes=60)
                    pages_str = ", ".join(str(p) for p in sorted(pages))
                    st.markdown(
                        f'<a href="{sas_url}" target="_blank">📄 {display_name} (pages {pages_str})</a>',
                        unsafe_allow_html=True
                    )
                except Exception as e:
                    st.markdown(f"- ⚠️ Error rendering source link for {source}: {str(e)}")

        except Exception as e:
            st.error(f"🚨 An error occurred: {str(e)}")
