# modules/auth.py (Corrected for new version)

import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

def load_authenticator():
    """
    Loads the authenticator object from the config.yaml file.
    """
    with open('config.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)

    # --- THIS IS THE PART THAT IS FIXED ---
    # The 'preauthorized' argument has been removed from this class initialization.
    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days']
    )

    return authenticator, config

def save_config(config):
    """
    Saves the updated configuration dictionary back to the config.yaml file.
    """
    with open('config.yaml', 'w') as file:
        yaml.dump(config, file, default_flow_style=False)