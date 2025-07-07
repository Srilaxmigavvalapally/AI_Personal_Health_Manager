# modules/utils.py

"""
This module contains utility functions that are used across multiple pages
of the Streamlit application. This helps to avoid code duplication and
keep the page scripts cleaner.

Functions:
- page_setup(): Configures the basic Streamlit page settings like title, icon, and layout.
- check_login(): A security check to ensure a user is logged in before accessing a page.
- get_db_session(): A context manager to handle database sessions reliably.
- get_user_id(username): Fetches the user's database ID based on their username.
"""

# ==============================================================================
# 1. IMPORTS
# ==============================================================================

import streamlit as st
from PIL import Image
from contextlib import contextmanager

# Import database components needed for utility functions
from .database import SessionLocal, User

# ==============================================================================
# 2. PAGE AND UI UTILITIES
# ==============================================================================

def page_setup():
    """
    Sets up the Streamlit page configuration, logo, and title.
    This should be called at the very start of each page script.
    """
    # Set the page configuration for a consistent look and feel
    st.set_page_config(
        page_title="Personal Health Manager",
        page_icon="❤️‍🩹",  # You can use an emoji or a path to a .ico file
        layout="wide"     # 'centered' or 'wide'
    )
    
    # Add a logo to the sidebar.
    # The 'try-except' block prevents the app from crashing if the logo file is not found.
    try:
        logo = Image.open('assets/logo.png')
        st.sidebar.image(logo, width=150)
    except FileNotFoundError:
        st.sidebar.warning("Logo file 'assets/logo.png' not found.")


def check_login():
    """
    Checks if the user is authenticated by looking at the session state.

    If the user is not authenticated (i.e., 'authentication_status' is not True),
    it displays a warning and stops the execution of the rest of the page script.
    This function is crucial for protecting pages that should only be accessible
    to logged-in users.
    """
    if st.session_state.get("authentication_status") is not True:
        st.warning("Please log in to access this page.")
        st.stop()  # Halts the script's execution immediately.

# ==============================================================================
# 3. DATABASE UTILITIES
# ==============================================================================

@contextmanager
def get_db_session():
    """
    A context manager for safely handling database sessions.
    It ensures that the database session is always closed, even if errors occur.

    Yields:
        db (Session): The SQLAlchemy database session.

    Example Usage:
        with get_db_session() as db:
            # Perform database operations
            user = db.query(User).first()
            print(user.name)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_user_id(username: str):
    """
    Fetches the database ID for a given username.

    This function is critical for linking data (like medications or documents)
    to the correct user in the database. It also handles the creation of a new
    user record in our database if one doesn't exist for the logged-in user.

    Args:
        username (str): The username from st.session_state['username'].

    Returns:
        int or None: The integer ID of the user, or None if the user cannot be found or created.
    """
    if not username:
        return None

    with get_db_session() as db:
        user = db.query(User).filter(User.username == username).first()
        
        # If the user exists in our DB, return their ID
        if user:
            return user.id
        else:
            # If user exists in authenticator but not in our DB (e.g., first login after DB reset)
            # we should create a record for them.
            st.info("First-time login detected. Creating your user profile in the database.")
            
            # We get the user details from session_state, which is populated by the authenticator
            try:
                new_user = User(
                    username=st.session_state["username"],
                    name=st.session_state["name"],
                    email=st.session_state["email"] # Assumes email is returned by authenticator
                )
                db.add(new_user)
                db.commit()
                db.refresh(new_user) # Refresh to get the newly created ID
                st.success("User profile created successfully.")
                return new_user.id
            except Exception as e:
                st.error(f"Error creating user profile in database: {e}")
                db.rollback() # Rollback changes if an error occurs
                return None