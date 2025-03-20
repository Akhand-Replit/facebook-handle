import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "facebook_manager")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# JWT configuration
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION = 24 * 60 * 60  # 24 hours in seconds

# Streamlit configuration
PAGE_TITLE = "FB Content Manager"
PAGE_ICON = "📱"
LAYOUT = "wide"
INITIAL_SIDEBAR_STATE = "expanded"

# Facebook API configuration
FACEBOOK_API_VERSION = "v18.0"
