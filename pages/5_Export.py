import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Export Results", layout="centered")
st.title("📤 Export to Excel")

st.markdown("Export extracted entities and metadata to a CSV file.")

data_file = "data/entities.csv"

if not os.path.exists(data_file):
    st.warning(f"No extracted entity data found in {os.path.abspath(data_file)}")
    st.stop()

# Load CSV
mock_data = pd.read_csv(data_file)

st.dataframe(mock_data)

csv = mock_data.to_csv(index=False).encode('utf-8')
st.download_button("Download CSV", data=csv, file_name="extracted_data.csv", mime="text/csv")