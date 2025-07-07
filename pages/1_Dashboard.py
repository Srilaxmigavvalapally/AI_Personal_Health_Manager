# pages/1_Dashboard.py

"""
This page serves as the user's main dashboard after they log in.
It provides a high-level overview of their health information, including:
- Upcoming appointments.
- A summary of current medications.
- Quick links to other sections of the app.
"""

# ==============================================================================
# 1. IMPORTS
# ==============================================================================
import streamlit as st
from datetime import datetime, timedelta

# Import utility functions for page setup and login check
from modules.utils import page_setup, check_login, get_db_session

# Import database models to query for dashboard data
from modules.database import Appointment, Medication

# ==============================================================================
# 2. PAGE SETUP AND AUTHENTICATION CHECK
# ==============================================================================

# Configure the page
page_setup()

# Verify that the user is logged in.
check_login()

# ==============================================================================
# 3. DASHBOARD UI AND DATA DISPLAY
# ==============================================================================

st.title(f"👋 Welcome to Your Dashboard, {st.session_state.get('name', 'User')}!")
st.info("This is your central hub for managing your health. Here you'll find quick summaries and reminders.")
st.divider()

# --- Fetch Data for the Dashboard ---
# We use a single database session for all queries on this page.
user_id = st.session_state.get("user_db_id")
upcoming_appointments = []
active_medications_count = 0

if user_id:
    with get_db_session() as db:
        # Query for appointments in the next 7 days
        now = datetime.utcnow()
        next_week = now + timedelta(days=7)
        upcoming_appointments = (
            db.query(Appointment)
            .filter(Appointment.owner_id == user_id)
            .filter(Appointment.appointment_datetime.between(now, next_week))
            .order_by(Appointment.appointment_datetime.asc())
            .all()
        )

        # Query for the count of active medications
        active_medications_count = (
            db.query(Medication)
            .filter(Medication.owner_id == user_id)
            .count() # A simple count for now
        )
else:
    st.error("Could not retrieve user data. Please try logging in again.")

# --- Display Dashboard Content in Columns ---
col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.subheader("🗓️ Upcoming Appointments")
        st.metric(label="Appointments in the next 7 days", value=len(upcoming_appointments))
        
        if upcoming_appointments:
            for appt in upcoming_appointments:
                # Format the datetime object for display
                appt_date_str = appt.appointment_datetime.strftime("%A, %b %d at %I:%M %p")
                st.markdown(f"- **{appt.doctor_name}** ({appt.specialty}) on **{appt_date_str}**")
        else:
            st.success("You have no appointments in the next 7 days.")
        
        if st.button("Manage Appointments"):
            st.switch_page("pages/4_Appointments.py")


with col2:
    with st.container(border=True):
        st.subheader("💊 Active Medications")
        st.metric(label="Total tracked medications", value=active_medications_count)
        
        st.write("Stay on top of your medication schedule.")
        # This is a placeholder; a more detailed list could be added here.
        if active_medications_count > 0:
            st.info("Visit the Medications page to see your full list and schedules.")
        else:
            st.success("You are not currently tracking any medications.")

        if st.button("Manage Medications"):
            st.switch_page("pages/3_Medications.py")


st.divider()

# --- Health Timeline Placeholder ---
st.subheader("🕰️ Your Recent Health Timeline")
st.write("This section will show a chronological view of your recent activities, like uploaded documents and added health logs.")
# This would be built by querying multiple tables (Documents, Vitals, etc.) and sorting by date.
timeline_placeholder = {
    "Oct 26, 2023": "Uploaded 'Blood Test Results.pdf'",
    "Oct 25, 2023": "Appointment added: Annual Check-up",
    "Oct 24, 2023": "Medication added: Vitamin D",
}
for date, event in timeline_placeholder.items():
    st.text(f"[{date}] - {event}")