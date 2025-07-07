# Home.py (Definitive version with robust login handling)

import streamlit as st
from modules.auth import load_authenticator, save_config
from modules.utils import page_setup, get_user_id

# Initialize authenticator and config globally so they are accessible throughout the file
authenticator, config = load_authenticator()

def main():
    """
    The main function that runs the logic for the Home page.
    """
    page_setup()

    # --- Primary Logic: Check for existing login status first ---
    if st.session_state.get("authentication_status"):
        # If the user is already logged in, show the main welcome/success view.
        authenticator.logout('🔓 Logout', 'sidebar')
        st.sidebar.title(f"Welcome, {st.session_state.get('name')}!")
        
        st.title(f"Welcome back, {st.session_state.get('name')}! 👋")
        st.success("You are successfully logged in.")
        st.info("Navigate to any page using the sidebar to manage your health.")

        if 'user_db_id' not in st.session_state or st.session_state.get('user_db_id') is None:
            st.session_state['user_db_id'] = get_user_id(st.session_state.get('username'))

    else:
        # If the user is NOT logged in, display the login and sign-up UI.
        st.title("Welcome to the AI_Personal_Health_Manager ❤️‍🩹")
        st.write("Your secure and intelligent platform to track and manage your health.")
        
        # --- THIS IS THE KEY FIX ---
        # The login widget is rendered here. Its main job is to update st.session_state.
        authenticator.login()
        
        if st.session_state.get("authentication_status") is False:
            st.error('Username/password is incorrect.')
        
        # We don't need a check for 'None' because the form is simply waiting for input.
        
# --- Sign Up Expander ---
with st.expander("Don't have an account? Sign Up"):
    try:
        if authenticator.register_user(location='main'):
            st.success('User registered successfully! Please log in above to continue.')
            save_config(config)
    except Exception as e:
        st.error(e)

# --- Footer ---
st.markdown("---")
st.caption("Built with ❤️ by Team AI Health Manager")

if __name__ == "__main__":
    main()