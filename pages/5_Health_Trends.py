# pages/5_Health_Trends.py

"""
This page allows users to log their health vitals and visualize trends over time.
It uses Pandas for data manipulation and Plotly for interactive charts.
"""

# ==============================================================================
# 1. IMPORTS
# ==============================================================================
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# Import utility functions and database models
from modules.utils import page_setup, check_login, get_db_session
from modules.database import HealthVital

# ==============================================================================
# 2. PAGE SETUP AND AUTHENTICATION CHECK
# ==============================================================================
page_setup()
check_login()

# Get the current user's database ID
user_id = st.session_state.get("user_db_id")
if not user_id:
    st.error("User not properly logged in. Cannot load health data.")
    st.stop()

# ==============================================================================
# 3. ADD NEW HEALTH LOG (CREATE)
# ==============================================================================
st.title("📈 Health Trends")
st.write("Log your health metrics and visualize your progress over time.")

VITAL_TYPES = ["Blood Pressure", "Blood Sugar", "Weight", "Heart Rate"]

with st.expander("➕ Add a New Health Log"):
    with st.form("new_vital_form", clear_on_submit=True):
        st.subheader("New Log Details")
        
        col1, col2 = st.columns(2)
        with col1:
            vital_type = st.selectbox("Select Vital Type", options=VITAL_TYPES)
            record_date = st.date_input("Date", value=datetime.today())
        
        with col2:
            if vital_type == "Blood Pressure":
                value1 = st.number_input("Systolic (SYS)", min_value=0)
                value2 = st.number_input("Diastolic (DIA)", min_value=0)
                unit = "mmHg"
            elif vital_type == "Blood Sugar":
                value1 = st.number_input("Value", min_value=0)
                value2 = None
                unit = st.selectbox("Unit", ["mg/dL", "mmol/L"])
            elif vital_type == "Weight":
                value1 = st.number_input("Value", min_value=0.0, format="%.2f")
                value2 = None
                unit = st.selectbox("Unit", ["kg", "lbs"])
            elif vital_type == "Heart Rate":
                value1 = st.number_input("Beats Per Minute (BPM)", min_value=0)
                value2 = None
                unit = "BPM"

        submitted = st.form_submit_button("Save Log")

        if submitted:
            if value1 > 0:
                with get_db_session() as db:
                    new_vital = HealthVital(
                        vital_type=vital_type, record_date=record_date,
                        value1=value1, value2=value2, unit=unit, owner_id=user_id
                    )
                    db.add(new_vital)
                    db.commit()
                st.success(f"{vital_type} log saved successfully.")
            else:
                st.warning("Please enter a valid value greater than 0.")
                
# ==============================================================================
# 4. VISUALIZE TRENDS (READ)
# ==============================================================================
st.divider()
st.subheader("Visualize Your Trends")

with get_db_session() as db:
    # Query all vitals and convert to a Pandas DataFrame
    vitals_query = db.query(HealthVital).filter(HealthVital.owner_id == user_id).order_by(HealthVital.record_date.asc())
    df = pd.read_sql(vitals_query.statement, db.bind)

if df.empty:
    st.info("You haven't logged any health data yet. Add a log above to see your trends.")
else:
    # Let user select which vital to plot
    available_vitals = df['vital_type'].unique()
    selected_vital = st.selectbox("Select a vital to visualize:", options=available_vitals)

    plot_df = df[df['vital_type'] == selected_vital].copy()
    plot_df['record_date'] = pd.to_datetime(plot_df['record_date'])
    
    # Create the plot using Plotly Express
    if selected_vital == "Blood Pressure":
        fig = px.line(plot_df, x='record_date', y=['value1', 'value2'],
                      title=f'{selected_vital} Trend', markers=True)
        # Update trace names for clarity
        fig.data[0].name = 'Systolic'
        fig.data[1].name = 'Diastolic'
        fig.update_layout(yaxis_title='mmHg')
    else:
        fig = px.line(plot_df, x='record_date', y='value1',
                      title=f'{selected_vital} Trend ({plot_df["unit"].iloc[0]})', markers=True)
        fig.update_layout(yaxis_title=plot_df["unit"].iloc[0])

    st.plotly_chart(fig, use_container_width=True)
    
    # --- Data Table and Deletion ---
    st.subheader(f"Log History for {selected_vital}")
    with st.container():
        for index, row in plot_df.sort_values('record_date', ascending=False).iterrows():
            col1, col2 = st.columns([5, 1])
            with col1:
                if selected_vital == "Blood Pressure":
                    val_str = f"{int(row.value1)} / {int(row.value2)} {row.unit}"
                else:
                    val_str = f"{row.value1} {row.unit}"
                
                st.markdown(f"**{row.record_date.strftime('%Y-%m-%d')}**: {val_str}")
            with col2:
                if st.button("🗑️", key=f"delete_vital_{row.id}", help="Delete this log entry"):
                    with get_db_session() as db_session:
                        vital_to_delete = db_session.query(HealthVital).get(row.id)
                        db_session.delete(vital_to_delete)
                        db_session.commit()
                    st.success("Log entry deleted.")
                    st.rerun()