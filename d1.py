# This is an ANALYTICAL dashboard because it supports exploration 
# of structural salary differences across gender, education, sector, and experience.

import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

st.set_page_config(layout="wide")

# -----------------------
# LOAD DATA
# -----------------------
df = pd.read_csv("colombia_salary_gap_analysis(in).csv")

# Clean column names
df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

# Try to standardize common variable names (adjust if needed)
possible_salary_cols = [col for col in df.columns if "salary" in col or "salario" in col]
possible_gender_cols = [col for col in df.columns if "gender" in col or "genero" in col]
possible_exp_cols = [col for col in df.columns if "experience" in col or "experiencia" in col]
possible_sector_cols = [col for col in df.columns if "sector" in col]
possible_edu_cols = [col for col in df.columns if "education" in col or "educacion" in col]

salary_col = possible_salary_cols[0]
gender_col = possible_gender_cols[0]

exp_col = possible_exp_cols[0] if possible_exp_cols else None
sector_col = possible_sector_cols[0] if possible_sector_cols else None
edu_col = possible_edu_cols[0] if possible_edu_cols else None

# Ensure salary numeric
df[salary_col] = pd.to_numeric(df[salary_col], errors="coerce")
df = df.dropna(subset=[salary_col])

# -----------------------
# TITLE
# -----------------------
st.title("Colombia Gender Salary Gap Dashboard")
st.markdown(
    "This analytical dashboard helps policymakers and labor analysts explore structural salary differences across gender, sector, education, and experience in Colombia."
)

# -----------------------
# SIDEBAR FILTERS
# -----------------------
st.sidebar.header("Filters")

selected_genders = st.sidebar.multiselect(
    "Select Gender",
    df[gender_col].unique(),
    default=df[gender_col].unique()
)

if sector_col:
    selected_sectors = st.sidebar.multiselect(
        "Select Sector",
        df[sector_col].unique(),
        default=df[sector_col].unique()
    )
else:
    selected_sectors = None

filtered = df[df[gender_col].isin(selected_genders)]

if sector_col and selected_sectors:
    filtered = filtered[filtered[sector_col].isin(selected_sectors)]

# -----------------------
# KPI SECTION
# -----------------------
st.subheader("Key Indicators")

col1, col2, col3 = st.columns(3)

male_avg = filtered[filtered[gender_col] == "Male"][salary_col].mean()
female_avg = filtered[filtered[gender_col] == "Female"][salary_col].mean()

gap = None
if male_avg and female_avg:
    gap = ((male_avg - female_avg) / male_avg) * 100

with col1:
    st.metric("Average Male Salary", f"${male_avg:,.0f}" if male_avg else "N/A")

with col2:
    st.metric("Average Female Salary", f"${female_avg:,.0f}" if female_avg else "N/A")

with col3:
    st.metric("Gender Pay Gap (%)", f"{gap:.2f}%" if gap else "N/A")

st.divider()

# -----------------------
# CHART 1 — Boxplot
# -----------------------
st.subheader("Salary Distribution by Gender")

fig1 = px.box(
    filtered,
    x=gender_col,
    y=salary_col,
    color=gender_col,
    color_discrete_sequence=px.colors.qualitative.Set2
)

st.plotly_chart(fig1, use_container_width=True)

# -----------------------
# CHART 2 — Gap by Sector
# -----------------------
if sector_col:
    st.subheader("Average Salary by Sector and Gender")

    sector_avg = (
        filtered
        .groupby([sector_col, gender_col])[salary_col]
        .mean()
        .reset_index()
    )

    fig2 = px.bar(
        sector_avg,
        x=sector_col,
        y=salary_col,
        color=gender_col,
        barmode="group",
        color_discrete_sequence=px.colors.qualitative.Set2
    )

    st.plotly_chart(fig2, use_container_width=True)

# -----------------------
# CHART 3 — Experience vs Salary
# -----------------------
if exp_col:
    st.subheader("Experience vs Salary")

    fig3 = px.scatter(
        filtered,
        x=exp_col,
        y=salary_col,
        color=gender_col,
        trendline="ols",
        color_discrete_sequence=px.colors.qualitative.Set2
    )

    st.plotly_chart(fig3, use_container_width=True)

# -----------------------
# CHART 4 — Education Impact
# -----------------------
if edu_col:
    st.subheader("Salary by Education Level and Gender")

    edu_avg = (
        filtered
        .groupby([edu_col, gender_col])[salary_col]
        .mean()
        .reset_index()
    )

    fig4 = px.bar(
        edu_avg,
        x=edu_col,
        y=salary_col,
        color=gender_col,
        barmode="group",
        color_discrete_sequence=px.colors.qualitative.Set2
    )

    st.plotly_chart(fig4, use_container_width=True)

st.markdown("---")
st.caption("Dashboard built with Streamlit | Analytical exploration of structural wage inequality in Colombia.")
