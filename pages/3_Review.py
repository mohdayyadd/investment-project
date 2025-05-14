import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Manual Review", layout="centered")
st.title("👀 Manual Review")

st.markdown("""
Below are extracted entities with confidence < 95%.
You can approve or update each one.
""")

entities_path = "data/entities.csv"

if not os.path.exists(entities_path):
    st.warning("No entities.csv file found. Please upload and process documents first.")
    st.stop()

# Load data
df = pd.read_csv(entities_path)
low_conf_df = df[df["Confidence"] < 0.95]

if low_conf_df.empty:
    st.success("✅ All entities meet the confidence threshold. Nothing to review.")
    st.stop()

updated_rows = []

for i, row in low_conf_df.iterrows():
    with st.expander(f"{row['Key']} ({row['Confidence']*100:.1f}%) – {row['Document']} page {row['Page']}"):
        new_key = st.text_input(f"Entity Key ({i})", value=row["Key"], key=f"key_{i}")
        new_value = st.text_input(f"Value ({i})", value=row["Value"], key=f"value_{i}")
        approve = st.checkbox("Approve and mark as reviewed", key=f"approve_{i}")

        if approve:
            updated_row = row.copy()
            updated_row["Key"] = new_key
            updated_row["Value"] = new_value
            updated_row["Confidence"] = 0.99
            updated_rows.append((i, updated_row))

if updated_rows:
    for i, new_row in updated_rows:
        df.iloc[i] = new_row
    df.to_csv(entities_path, index=False)
    st.success("✅ Updated entries saved to entities.csv.")
