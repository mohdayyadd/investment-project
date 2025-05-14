# === Page: 4_Dashboard.py ===

import streamlit as st
import pandas as pd
import altair as alt
import os

st.set_page_config(page_title="Dashboard", layout="wide")
st.title("📊 Investment Insights Dashboard")

data_file = "data/entities.csv"

if not os.path.exists(data_file):
    st.warning("No extracted entity data found in ../data/entities.csv")
    st.stop()

# Load CSV
raw_df = pd.read_csv(data_file)

# === Sidebar filters ===
st.sidebar.header("Filters")
companies = raw_df["Company"].dropna().unique().tolist()
years = sorted(raw_df["Year"].dropna().unique())

selected_company = st.sidebar.selectbox("Select Company", ["All"] + companies)
selected_year = st.sidebar.selectbox("Select Year", ["All"] + [str(y) for y in years])

df = raw_df.copy()
if selected_company != "All":
    df = df[df["Company"] == selected_company]
if selected_year != "All":
    df = df[df["Year"] == int(selected_year)]

# === Show key metric summary ===
st.metric("Total Reports", df["Document"].nunique())
st.metric("Total Revenue Extracted", f"${df[df['Key'] == 'Revenue']['Value'].sum():,.2f}")
st.metric("Average Confidence", f"{df['Confidence'].mean():.2%}")

# === Charts ===
st.subheader("📈 Revenue by Company and Year")

revenue_data = df[df["Key"] == "Revenue"]
if not revenue_data.empty:
    chart = alt.Chart(revenue_data).mark_bar().encode(
        x=alt.X("Year:O", title="Year"),
        y=alt.Y("Value:Q", title="Revenue", stack=False),
        color="Company:N",
        tooltip=["Company", "Year", "Value", "Document"]
    ).interactive()
    st.altair_chart(chart, use_container_width=True)
else:
    st.info("No revenue data found in current filters.")

# === Table ===
st.subheader("📄 Extracted Entities Table")
st.dataframe(df[["Company", "Year", "Key", "Value", "Document", "Page", "Confidence"]])
