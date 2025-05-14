# === Page: 1_Upload.py ===

import streamlit as st
import os
import pandas as pd
import uuid
import random
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Upload Documents", layout="centered")
st.title("📥 Upload Documents")

st.markdown("Upload PDFs to simulate adding extracted entity data.")

# === Paths and storage setup ===
data_path = "data/entities.csv"
existing_entities = pd.read_csv(data_path) if os.path.exists(data_path) else pd.DataFrame(columns=[
    "Document", "Company", "Year", "Key", "Value", "Page", "Confidence"])

# === Simulated company datasets ===
dummy_sets = {
    "ADNOC": [
        {"Document": "ADNOC_2023.pdf", "Company": "ADNOC", "Year": 2023, "Key": "Revenue", "Value": 4034, "Page": 3, "Confidence": 0.96},
        {"Document": "ADNOC_2023.pdf", "Company": "ADNOC", "Year": 2023, "Key": "Net Profit", "Value": 1304, "Page": 3, "Confidence": 0.91},
        {"Document": "ADNOC_2023.pdf", "Company": "ADNOC", "Year": 2023, "Key": "EBITDA", "Value": 2015, "Page": 3, "Confidence": 0.88}
    ],
    "ENOC": [
        {"Document": "ENOC_2022.pdf", "Company": "ENOC", "Year": 2022, "Key": "Revenue", "Value": 2900, "Page": 2, "Confidence": 0.87},
        {"Document": "ENOC_2022.pdf", "Company": "ENOC", "Year": 2022, "Key": "Net Profit", "Value": 1100, "Page": 2, "Confidence": 0.91}
    ],
    "Mubadala": [
        {"Document": "Mubadala_2023.pdf", "Company": "Mubadala", "Year": 2023, "Key": "Investment Capital", "Value": 5200, "Page": 4, "Confidence": 0.89},
        {"Document": "Mubadala_2023.pdf", "Company": "Mubadala", "Year": 2023, "Key": "Revenue", "Value": 1800, "Page": 4, "Confidence": 0.84}
    ]
}

# === Upload simulation ===
uploaded_files = st.file_uploader("Upload PDFs", type=["pdf"], accept_multiple_files=True)

def append_entities(rows):
    global existing_entities
    new_df = pd.DataFrame(rows)
    existing_entities = pd.concat([existing_entities, new_df], ignore_index=True)
    existing_entities.to_csv(data_path, index=False)
    st.success(f"Added {len(rows)} rows to entities.csv")

if uploaded_files:
    for file in uploaded_files:
        company = random.choice(list(dummy_sets.keys()))
        st.info(f"Simulated extraction for '{company}' from uploaded file: {file.name}")
        append_entities(dummy_sets[company])