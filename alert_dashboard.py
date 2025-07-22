import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

# Set up page
st.set_page_config(page_title="Alert Analytics Dashboard", layout="wide")

# Simulate the dataset
np.random.seed(42)
base_date = pd.to_datetime("2025-01-01")
dates = pd.date_range(start=base_date, end=base_date + pd.DateOffset(days=120))
vessels = [f"Vessel_{i}" for i in range(1, 21)]
fleets = ['Fleet A', 'Fleet B', 'Fleet C', 'Fleet D']
alert_types = ['Speeding', 'Late Report', 'Excess Slip', 'Bilge ROB', 'Sludge ROB', 'AE Usage', 'Shaft Generator Usage']

# Create mock alert data
data = []
for date in dates:
    for _ in range(np.random.randint(5, 15)):
        data.append({
            'Date': date,
            'Fleet': np.random.choice(fleets),
            'Vessel': np.random.choice(vessels),
            'Alert Type': np.random.choice(alert_types),
            'Resolution Time (hrs)': round(np.random.exponential(2), 2),
            'Auto-Cleared': np.random.choice([True, False], p=[0.6, 0.4])
        })
df = pd.DataFrame(data)

# Sidebar filters
st.sidebar.header("🔎 Filters")
period = st.sidebar.selectbox("Select Period", ["Last 7 Days", "Last 30 Days", "Quarter to Date", "Year to Date", "Custom Range"])
today = df["Date"].max()

if period == "Last 7 Days":
    start_date = today - timedelta(days=7)
    end_date = today
elif period == "Last 30 Days":
    start_date = today - timedelta(days=30)
    end_date = today
elif period == "Quarter to Date":
    start_date = pd.Timestamp(today.year, (today.month - 1) // 3 * 3 + 1, 1)
    end_date = today
elif period == "Year to Date":
    start_date = pd.Timestamp(today.year, 1, 1)
    end_date = today
else:
    start_date = st.sidebar.date_input("Start Date", today - timedelta(days=30))
    end_date = st.sidebar.date_input("End Date", today)
    if isinstance(start_date, list): start_date = start_date[0]
    if isinstance(end_date, list): end_date = end_date[0]

df = df[(df['Date'] >= pd.to_datetime(start_date)) & (df['Date'] <= pd.to_datetime(end_date))]
selected_fleets = st.sidebar.multiselect("Select Fleets", options=fleets, default=fleets)
df = df[df['Fleet'].isin(selected_fleets)]
selected_alerts = st.sidebar.multiselect("Select Alert Types", options=alert_types, default=alert_types)
df = df[df['Alert Type'].isin(selected_alerts)]
available_vessels = sorted(df['Vessel'].unique())
selected_vessels = st.sidebar.multiselect("Select Vessels", options=available_vessels, default=available_vessels)
df = df[df['Vessel'].isin(selected_vessels)]

# KPI values
total_alerts = len(df)
vessels_with_alerts = df['Vessel'].nunique()
auto_cleared_percent = round(df['Auto-Cleared'].mean() * 100, 1)
avg_resolution = round(df['Resolution Time (hrs)'].mean(), 2)
active_alerts = len(df[~df['Auto-Cleared']])
resolved_alerts = len(df[df['Auto-Cleared']])

# Alerts over time
alerts_time_df = df.groupby("Date").size().reset_index(name="Total Alerts")
active_df = df[~df['Auto-Cleared']].groupby("Date").size().reset_index(name="Active Alerts")
resolved_df = df[df['Auto-Cleared']].groupby("Date").size().reset_index(name="Resolved Alerts")
alerts_time_df = alerts_time_df.merge(active_df, on="Date", how="left").merge(resolved_df, on="Date", how="left").fillna(0)

# Dashboard Title
st.title("🚨 Alert Analytics Dashboard")

# KPI Cards
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Alerts", f"{total_alerts:,}")
    st.markdown(f"<span style='font-size:13px;'>Active: {active_alerts:,} &nbsp;&nbsp;&nbsp;&nbsp; Resolved: {resolved_alerts:,}</span>", unsafe_allow_html=True)
col2.metric("Vessels With Alerts", f"{vessels_with_alerts:,}")
col3.metric("Auto-Cleared Alerts", f"{auto_cleared_percent}%")
col4.metric("Avg Resolution", f"{avg_resolution} hrs")

# Alerts Over Time (Line Chart)
st.markdown("### 📈 Alerts Over Time – Line View")
fig1 = go.Figure()
fig1.add_trace(go.Scatter(x=alerts_time_df['Date'], y=alerts_time_df['Total Alerts'], mode='lines+markers', name='Total Alerts'))
fig1.add_trace(go.Scatter(x=alerts_time_df['Date'], y=alerts_time_df['Active Alerts'], mode='lines+markers', name='Active Alerts'))
fig1.add_trace(go.Scatter(x=alerts_time_df['Date'], y=alerts_time_df['Resolved Alerts'], mode='lines+markers', name='Resolved Alerts'))
fig1.update_layout(height=300, margin=dict(l=0, r=0, t=30, b=0), legend=dict(orientation="h", y=1.02, x=1))
st.plotly_chart(fig1, use_container_width=True)

# Area Chart
st.markdown("### 🔄 Alert Resolution Trend – Area Chart View")
fig_area = px.area(alerts_time_df, x='Date',
                   y=['Active Alerts', 'Resolved Alerts'],
                   labels={'value': 'Number of Alerts', 'variable': 'Alert Status'},
                   color_discrete_map={'Active Alerts': '#EF553B', 'Resolved Alerts': '#00CC96'})
fig_area.update_layout(height=300, margin=dict(l=0, r=0, t=30, b=0), legend=dict(orientation="h", y=1.02, x=1))
st.plotly_chart(fig_area, use_container_width=True)

# Alert Type and Fleet Breakdown
alert_type_counts = df['Alert Type'].value_counts()
fleet_alerts = df['Fleet'].value_counts()

col5, col6 = st.columns(2)
with col5:
    st.markdown("### 🍩 Alert Type Distribution (Donut Chart)")
    fig_donut = go.Figure(data=[go.Pie(labels=alert_type_counts.index,
                                       values=alert_type_counts.values,
                                       hole=0.55,
                                       textinfo='label+percent')])
    fig_donut.update_layout(height=300, margin=dict(l=0, r=0, t=30, b=0))
    st.plotly_chart(fig_donut, use_container_width=True)

with col6:
    st.markdown("### 📊 Fleet Comparison")
    fig3 = px.bar(x=fleet_alerts.values, y=fleet_alerts.index, orientation='h', labels={'x': 'Alerts', 'y': 'Fleet'})
    fig3.update_layout(height=300, margin=dict(l=0, r=0, t=30, b=0))
    st.plotly_chart(fig3, use_container_width=True)

# Resolution Time Distribution
bins = [0, 0.25, 1, 3, 6, 12, np.inf]
labels = ['0–15 min', '15–60 m', '1–3 hrs', '3–6 hrs', '6–12 hrs', '> 12 hrs']
df['ResBin'] = pd.cut(df['Resolution Time (hrs)'], bins=bins, labels=labels, include_lowest=True)
res_time_counts = df['ResBin'].value_counts().sort_index()
st.markdown("### ⏱️ Resolution Time Distribution")
fig4 = px.bar(x=res_time_counts.index, y=res_time_counts.values, labels={'x': 'Resolution Time', 'y': 'Number of Alerts'})
fig4.update_layout(height=300, margin=dict(l=0, r=0, t=30, b=0))
st.plotly_chart(fig4, use_container_width=True)

# --------------------------
# SECTION: Overview KPIs
# --------------------------
st.markdown("## 🧮 Overview KPIs")
sla_threshold = 2
within_sla_pct = round((df['Resolution Time (hrs)'] <= sla_threshold).mean() * 100, 1)
resolution_rate = round((df['Auto-Cleared'].sum() / len(df)) * 100, 1)
colA, colB = st.columns(2)
colA.metric("Resolved Within 2 Hours", f"{within_sla_pct}%")
colB.metric("Auto-Cleared Resolution Rate", f"{resolution_rate}%")

# --------------------------
# SECTION: Root Cause Analysis
# --------------------------
st.markdown("## 🔍 Root Cause Analysis")
colC, colD = st.columns(2)
with colC:
    st.markdown("### 🏆 Top 5 Alert Types")
    top_alerts = df['Alert Type'].value_counts().head(5)
    fig = px.bar(top_alerts, x=top_alerts.values, y=top_alerts.index,
                 orientation='h', labels={'x': 'Count', 'index': 'Alert Type'})
    st.plotly_chart(fig, use_container_width=True)

with colD:
    st.markdown("### 🚢 Top 5 Vessels with Most Alerts")
    top_vessels = df['Vessel'].value_counts().head(5)
    fig = px.bar(top_vessels, x=top_vessels.values, y=top_vessels.index,
                 orientation='h', labels={'x': 'Count', 'index': 'Vessel'})
    st.plotly_chart(fig, use_container_width=True)

st.markdown("### 🐌 Slowest Alerts to Resolve")
slowest_types = df.groupby('Alert Type')['Resolution Time (hrs)'].mean().sort_values(ascending=False).head(5)
fig = px.bar(slowest_types, x=slowest_types.values, y=slowest_types.index,
             orientation='h', labels={'x': 'Avg Resolution Time (hrs)', 'index': 'Alert Type'})
st.plotly_chart(fig, use_container_width=True)

# --------------------------
# SECTION: Crew / Process Flags
# --------------------------
st.markdown("## 🧑‍✈️ Crew / Process Flags")

st.markdown("### 🔁 Repeat Alerts (>=3) per Vessel & Type")
repeat_alerts = df.groupby(['Vessel', 'Alert Type']).size().reset_index(name='Count')
repeat_alerts = repeat_alerts[repeat_alerts['Count'] >= 3]
st.dataframe(repeat_alerts.sort_values(by='Count', ascending=False))

st.markdown("### 🔥 Heatmap of Repeat Alerts by Vessel & Alert Type")
heatmap_df = df.groupby(['Vessel', 'Alert Type']).size().unstack().fillna(0)
fig_heatmap = px.imshow(heatmap_df,
                        labels=dict(x="Alert Type", y="Vessel", color="Count"),
                        aspect="auto", color_continuous_scale="Reds")
fig_heatmap.update_layout(height=500, margin=dict(l=0, r=0, t=30, b=0))
st.plotly_chart(fig_heatmap, use_container_width=True)
