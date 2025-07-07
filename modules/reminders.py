# modules/reminders.py

"""
This script runs as a separate, continuous background process.
Its purpose is to:
1. Periodically query the database for upcoming appointments and medication schedules.
2. Send email notifications to users for these events.
"""

# ==============================================================================
# 1. IMPORTS
# ==============================================================================
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
from datetime import datetime, timedelta

from apscheduler.schedulers.blocking import BlockingScheduler
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import the database models from our main application
from modules.database import Base, User, Appointment, Medication

# ==============================================================================
# 2. CONFIGURATION AND SETUP
# ==============================================================================

# --- Email Configuration ---
# Load credentials from environment variables for security
SENDER_EMAIL = os.environ.get("EMAIL_SENDER")
SENDER_PASSWORD = os.environ.get("EMAIL_PASSWORD")
SMTP_SERVER = "smtp.gmail.com"  # Using Gmail as an example
SMTP_PORT = 465  # For SSL

# --- Database Connection ---
# Must be the exact same DATABASE_URL as your main Streamlit app
DATABASE_URL = "sqlite:///./health_manager.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ==============================================================================
# 3. NOTIFICATION LOGIC
# ==============================================================================

def send_email_reminder(recipient_email, subject, body):
    """Sends an email using SMTP."""
    if not all([SENDER_EMAIL, SENDER_PASSWORD]):
        print("ERROR: Email credentials not set in environment variables. Cannot send email.")
        return

    message = MIMEMultipart()
    message["From"] = SENDER_EMAIL
    message["To"] = recipient_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    try:
        print(f"Attempting to send email to {recipient_email}...")
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, recipient_email, message.as_string())
        print(f"Email sent successfully to {recipient_email}!")
    except Exception as e:
        print(f"Failed to send email to {recipient_email}. Error: {e}")

# ==============================================================================
# 4. THE MAIN REMINDER JOB
# ==============================================================================

def check_for_reminders():
    """The main job that queries the DB and triggers notifications."""
    print(f"--- Running reminder check at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")
    db = SessionLocal()
    try:
        # --- Check for upcoming appointments (e.g., within the next 24 hours) ---
        now = datetime.utcnow()
        reminder_window_end = now + timedelta(hours=24)
        
        upcoming_appointments = (
            db.query(Appointment, User)
            .join(User, Appointment.owner_id == User.id)
            .filter(Appointment.appointment_datetime.between(now, reminder_window_end))
            .all()
        )

        for appointment, user in upcoming_appointments:
            subject = "Upcoming Appointment Reminder"
            body = (
                f"Hi {user.name},\n\n"
                f"This is a reminder for your upcoming appointment:\n"
                f"Doctor: {appointment.doctor_name} ({appointment.specialty})\n"
                f"Date & Time: {appointment.appointment_datetime.strftime('%A, %B %d, %Y at %I:%M %p')}\n"
                f"Location: {appointment.location}\n\n"
                f"Have a great day!\nYour Personal Health Manager"
            )
            send_email_reminder(user.email, subject, body)
            # NOTE: In a real app, you'd mark this reminder as 'sent' in the DB
            # to avoid sending it again on the next check.

        # --- Check for medication reminders (a simplified approach) ---
        # This simple check triggers for medications scheduled on the current hour.
        # A real-world app would need a more robust schedule parsing logic.
        current_hour_str = datetime.now().strftime("%H:00")
        
        meds_due = (
            db.query(Medication, User)
            .join(User, Medication.owner_id == User.id)
            .filter(Medication.schedule.like(f"%{current_hour_str}%")) # Simple text match
            .all()
        )

        for medication, user in meds_due:
             subject = "Medication Reminder"
             body = (
                f"Hi {user.name},\n\n"
                f"It's time to take your medication:\n"
                f"Medication: {medication.name}\n"
                f"Dosage: {medication.dosage}\n"
                f"Schedule Info: {medication.schedule}\n\n"
                f"Stay healthy!\nYour Personal Health Manager"
            )
             send_email_reminder(user.email, subject, body)

    finally:
        db.close()
    print("--- Reminder check finished ---")

# ==============================================================================
# 5. SCHEDULER EXECUTION
# ==============================================================================

if __name__ == "__main__":
    print("Starting Reminder Service...")
    # The 'BlockingScheduler' will run in the foreground and block the terminal.
    scheduler = BlockingScheduler()
    
    # Schedule the 'check_for_reminders' job to run every 10 minutes.
    # For testing, you can change 'minutes' to 'seconds=30'
    scheduler.add_job(check_for_reminders, 'interval', minutes=10)
    
    # Run the check once immediately on startup
    check_for_reminders()

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        # Allows you to shut down the scheduler cleanly with Ctrl+C
        print("Reminder service stopped.")