# pages/4_Appointments.py


import streamlit as st
from datetime import datetime, time

# Import utility functions and database models
from modules.utils import page_setup, check_login, get_db_session
from modules.database import Appointment

# ==============================================================================
# 2. PAGE SETUP AND AUTHENTICATION CHECK
# ==============================================================================
page_setup()
check_login()

# Get the current user's database ID
user_id = st.session_state.get("user_db_id")
if not user_id:
    st.error("User not properly logged in. Cannot load appointment data.")
    st.stop()

# ==============================================================================
# 3. ADD NEW APPOINTMENT (CREATE)
# ==============================================================================
st.title("🗓️ My Appointments")
st.write("Schedule and track your upcoming and past doctor appointments.")

with st.expander("➕ Add a New Appointment"):
    with st.form("new_appointment_form", clear_on_submit=True):
        st.subheader("New Appointment Details")
        
        col1, col2 = st.columns(2)
        with col1:
            appt_doctor = st.text_input("Doctor's Name", placeholder="e.g., Dr. Jane Smith")
            appt_date = st.date_input("Date", value=datetime.today())
        with col2:
            appt_specialty = st.text_input("Specialty", placeholder="e.g., General Practitioner")
            appt_time = st.time_input("Time", value=time(9, 00))
            
        appt_location = st.text_input("Location", placeholder="e.g., 123 Health St, Medical City")
        appt_notes = st.text_area("Notes", placeholder="e.g., Annual check-up, ask about blood test results.")
        
        submitted = st.form_submit_button("Save Appointment")

        if submitted:
            if not appt_doctor:
                st.warning("Doctor's name is required.")
            else:
                # Combine date and time into a single datetime object
                appointment_datetime = datetime.combine(appt_date, appt_time)
                with get_db_session() as db:
                    new_appt = Appointment(
                        doctor_name=appt_doctor,
                        specialty=appt_specialty,
                        appointment_datetime=appointment_datetime,
                        location=appt_location,
                        notes=appt_notes,
                        owner_id=user_id
                    )
                    db.add(new_appt)
                    db.commit()
                st.success(f"Appointment with {appt_doctor} has been saved.")
                
# ==============================================================================
# 4. LIST AND MANAGE APPOINTMENTS (READ, UPDATE, DELETE)
# ==============================================================================
st.divider()

# Fetch all appointments and categorize them
with get_db_session() as db:
    all_appts = db.query(Appointment).filter(Appointment.owner_id == user_id).order_by(Appointment.appointment_datetime.desc()).all()

now = datetime.now()
upcoming_appts = [a for a in all_appts if a.appointment_datetime >= now]
past_appts = [a for a in all_appts if a.appointment_datetime < now]

# --- Display appointments using tabs ---
tab1, tab2 = st.tabs([f"Upcoming ({len(upcoming_appts)})", f"Past ({len(past_appts)})"])

def display_appointments(appointments):
    """Helper function to display a list of appointments."""
    if not appointments:
        st.info("No appointments in this category.")
        return

    # Use session state to track which appointment is being edited
    if 'editing_appt_id' not in st.session_state:
        st.session_state.editing_appt_id = None

    for appt in appointments:
        if st.session_state.editing_appt_id == appt.id:
            # --- UPDATE VIEW ---
            with st.container(border=True):
                with st.form(key=f"edit_form_{appt.id}"):
                    st.markdown(f"**Editing Appointment with: {appt.doctor_name}**")
                    new_doctor = st.text_input("Doctor's Name", value=appt.doctor_name, key=f"doc_{appt.id}")
                    new_specialty = st.text_input("Specialty", value=appt.specialty, key=f"spec_{appt.id}")
                    new_date = st.date_input("Date", value=appt.appointment_datetime.date(), key=f"date_{appt.id}")
                    new_time = st.time_input("Time", value=appt.appointment_datetime.time(), key=f"time_{appt.id}")
                    new_notes = st.text_area("Notes", value=appt.notes, key=f"notes_{appt.id}")

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("✅ Save Changes"):
                            with get_db_session() as db_session:
                                appt_to_update = db_session.query(Appointment).get(appt.id)
                                appt_to_update.doctor_name = new_doctor
                                appt_to_update.specialty = new_specialty
                                appt_to_update.appointment_datetime = datetime.combine(new_date, new_time)
                                appt_to_update.notes = new_notes
                                db_session.commit()
                            st.session_state.editing_appt_id = None
                            st.success("Appointment updated successfully.")
                            st.rerun()
                    with col2:
                        if st.form_submit_button("❌ Cancel"):
                            st.session_state.editing_appt_id = None
                            st.rerun()
        else:
            # --- READ/DELETE VIEW ---
            with st.container(border=True):
                col1, col2, col3 = st.columns([4, 1, 1])
                with col1:
                    st.markdown(f"**{appt.doctor_name}** ({appt.specialty})")
                    st.markdown(f"**When:** {appt.appointment_datetime.strftime('%A, %B %d, %Y at %I:%M %p')}")
                    st.caption(f"Location: {appt.location}" if appt.location else "No location specified")
                    if appt.notes:
                        with st.expander("View Notes"):
                            st.write(appt.notes)
                
                with col2:
                    if st.button("✏️ Edit", key=f"edit_{appt.id}"):
                        st.session_state.editing_appt_id = appt.id
                        st.rerun()
                
                with col3:
                    if st.button("🗑️ Delete", key=f"delete_{appt.id}", type="primary"):
                        with get_db_session() as db_session:
                            appt_to_delete = db_session.query(Appointment).get(appt.id)
                            db_session.delete(appt_to_delete)
                            db_session.commit()
                        st.success(f"Appointment with {appt.doctor_name} deleted.")
                        st.rerun()

# Call the display function for each tab
with tab1:
    st.subheader("Your Upcoming Appointments")
    display_appointments(upcoming_appts)

with tab2:
    st.subheader("Your Past Appointments")
    display_appointments(past_appts)