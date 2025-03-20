import streamlit as st

# Database configuration - using PostgreSQL URL directly
DATABASE_URL = st.secrets["postgres"]["url"]

# JWT configuration
JWT_SECRET = st.secrets["jwt"]["secret"]
JWT_ALGORITHM = st.secrets["jwt"]["algorithm"]
JWT_EXPIRATION = st.secrets["jwt"]["expiration"]

# Streamlit configuration
PAGE_TITLE = "FB Content Manager"
PAGE_ICON = "📱"
LAYOUT = "wide"
INITIAL_SIDEBAR_STATE = "expanded"

# Facebook API configuration
FACEBOOK_API_VERSION = st.secrets["facebook"]["api_version"]

# Function to get fallback values for local development
def get_secret(section, key, default_value=None):
    """Get a secret from streamlit secrets or use default value"""
    try:
        return st.secrets[section][key]
    except (KeyError, FileNotFoundError):
        if default_value is not None:
            return default_value
        raise
