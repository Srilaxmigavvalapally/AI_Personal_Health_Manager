# pages/3_Medications.py

import streamlit as st
from datetime import datetime

# Import utility functions and database models
from modules.utils import page_setup, check_login, get_db_session
from modules.database import Medication

page_setup()
check_login()

# Get the current user's database ID
user_id = st.session_state.get("user_db_id")
if not user_id:
    st.error("User not properly logged in. Cannot load medication data.")
    st.stop()

# ==============================================================================
# 3. ADD NEW MEDICATION (CREATE)
# ==============================================================================
st.title("💊 My Medications")
st.write("Keep track of your current and past medications, dosages, and schedules.")

with st.expander("➕ Add a New Medication"):
    with st.form("new_medication_form", clear_on_submit=True):
        st.subheader("New Medication Details")
        med_name = st.text_input("Medication Name", placeholder="e.g., Lisinopril")
        med_dosage = st.text_input("Dosage", placeholder="e.g., 10mg")
        med_schedule = st.text_input("Schedule", placeholder="e.g., Once daily in the morning")
        med_start_date = st.date_input("Start Date", value=datetime.today())
        
        submitted = st.form_submit_button("Save Medication")

        if submitted:
            if not med_name:
                st.warning("Medication name is required.")
            else:
                with get_db_session() as db:
                    new_med = Medication(
                        name=med_name,
                        dosage=med_dosage,
                        schedule=med_schedule,
                        start_date=datetime.combine(med_start_date, datetime.min.time()),
                        owner_id=user_id
                    )
                    db.add(new_med)
                    db.commit()
                st.success(f"'{med_name}' has been added to your list.")
                # No st.rerun() needed here, Streamlit will rerun after the form submission.

# ==============================================================================
# 4. LIST AND MANAGE MEDICATIONS (READ, UPDATE, DELETE)
# ==============================================================================
st.divider()
st.subheader("Your Current Medication List")

with get_db_session() as db:
    user_meds = db.query(Medication).filter(Medication.owner_id == user_id).order_by(Medication.name).all()

if not user_meds:
    st.info("You have not added any medications yet. Use the form above to get started.")
else:
    # Use st.session_state to track which medication is being edited
    if 'editing_med_id' not in st.session_state:
        st.session_state.editing_med_id = None

    for med in user_meds:
        # Check if the current medication is the one being edited
        if st.session_state.editing_med_id == med.id:
            # --- UPDATE VIEW ---
            with st.container(border=True):
                with st.form(key=f"edit_form_{med.id}"):
                    st.markdown(f"**Editing: {med.name}**")
                    new_name = st.text_input("Name", value=med.name, key=f"name_{med.id}")
                    new_dosage = st.text_input("Dosage", value=med.dosage, key=f"dosage_{med.id}")
                    new_schedule = st.text_input("Schedule", value=med.schedule, key=f"schedule_{med.id}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("✅ Save Changes"):
                            with get_db_session() as db_session:
                                med_to_update = db_session.query(Medication).get(med.id)
                                med_to_update.name = new_name
                                med_to_update.dosage = new_dosage
                                med_to_update.schedule = new_schedule
                                db_session.commit()
                            st.session_state.editing_med_id = None
                            st.success("Medication updated successfully.")
                            st.rerun()
                    with col2:
                        if st.form_submit_button("❌ Cancel", type="secondary"):
                            st.session_state.editing_med_id = None
                            st.rerun()
        else:
            # --- READ/DELETE VIEW ---
            with st.container(border=True):
                col1, col2, col3 = st.columns([4, 1, 1])
                with col1:
                    st.markdown(f"**{med.name}**")
                    st.caption(f"Dosage: {med.dosage} | Schedule: {med.schedule}")
                    st.caption(f"Started on: {med.start_date.strftime('%Y-%m-%d')}")
                
                with col2:
                    if st.button("✏️ Edit", key=f"edit_{med.id}"):
                        st.session_state.editing_med_id = med.id
                        st.rerun()

                with col3:
                    if st.button("🗑️ Delete", key=f"delete_{med.id}", type="primary"):
                        with get_db_session() as db_session:
                            med_to_delete = db_session.query(Medication).get(med.id)
                            db_session.delete(med_to_delete)
                            db_session.commit()
                        st.success(f"'{med.name}' deleted successfully.")
                        st.rerun()