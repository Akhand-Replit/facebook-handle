import streamlit as st
import pandas as pd
import os
from pathlib import Path
from utils.auth import show_login_form, show_registration_form, require_auth, logout
from utils.db import init_db, get_user_accounts
from pages.home import show_home_page
from pages.accounts import show_accounts_page
from pages.posts import show_posts_page
from pages.comments import show_comments_page
from pages.settings import show_settings_page
from config import PAGE_TITLE, PAGE_ICON, LAYOUT, INITIAL_SIDEBAR_STATE

# Set page configuration
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout=LAYOUT,
    initial_sidebar_state=INITIAL_SIDEBAR_STATE
)

# Load custom CSS
def load_css():
    css_file = Path(__file__).parent / "static" / "style.css"
    if css_file.exists():
        with open(css_file) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        # Ensure the static directory exists
        static_dir = Path(__file__).parent / "static"
        if not static_dir.exists():
            static_dir.mkdir(parents=True, exist_ok=True)

# Initialize the application
def init_app():
    try:
        # Initialize database
        init_db()
        
        # Initialize session state
        if "page" not in st.session_state:
            st.session_state["page"] = "home"
        
        if "show_register" not in st.session_state:
            st.session_state["show_register"] = False
            
        if "show_forgot_password" not in st.session_state:
            st.session_state["show_forgot_password"] = False
        
        if "selected_account" not in st.session_state:
            st.session_state["selected_account"] = None
            
        if "selected_post" not in st.session_state:
            st.session_state["selected_post"] = None
            
        if "edit_post" not in st.session_state:
            st.session_state["edit_post"] = False
            
        if "delete_post" not in st.session_state:
            st.session_state["delete_post"] = False
            
        if "reply_to_comment" not in st.session_state:
            st.session_state["reply_to_comment"] = None
            
        if "edit_comment" not in st.session_state:
            st.session_state["edit_comment"] = None
            
        if "delete_comment" not in st.session_state:
            st.session_state["delete_comment"] = None
            
        if "preferences" not in st.session_state:
            st.session_state["preferences"] = {
                "theme": "Default",
                "posts_per_page": 25,
                "date_format": "YYYY-MM-DD"
            }
    except Exception as e:
        st.error(f"Error during app initialization: {str(e)}")

# Main function
def main():
    try:
        # Initialize the app
        init_app()
        
        # Load custom CSS
        load_css()
        
        # Show title
        st.title("Facebook Content Manager")
        
        # Check authentication
        if not st.session_state.get("authenticated", False):
            # Show login or registration forms
            if st.session_state.get("show_register", False):
                show_registration_form()
            else:
                show_login_form()
        else:
            # User is logged in, show sidebar navigation
            with st.sidebar:
                st.subheader(f"Welcome, {st.session_state['username']}!")
                
                # Navigation
                st.markdown("## Navigation")
                
                if st.button("📊 Dashboard", use_container_width=True):
                    st.session_state["page"] = "home"
                    st.session_state["selected_account"] = None
                    st.session_state["selected_post"] = None
                    
                if st.button("📱 Accounts", use_container_width=True):
                    st.session_state["page"] = "accounts"
                    st.session_state["selected_account"] = None
                    st.session_state["selected_post"] = None
                    
                if st.button("📝 Posts", use_container_width=True):
                    st.session_state["page"] = "posts"
                    st.session_state["selected_post"] = None
                    
                if st.button("💬 Comments", use_container_width=True):
                    st.session_state["page"] = "comments"
                    
                if st.button("⚙️ Settings", use_container_width=True):
                    st.session_state["page"] = "settings"
                    st.session_state["selected_account"] = None
                    st.session_state["selected_post"] = None
                
                # Account selection
                st.markdown("## Facebook Accounts")
                accounts = get_user_accounts(st.session_state["user_id"])
                
                if accounts:
                    account_options = ["Select an account"] + [f"{account.account_name} ({account.page_id})" for account in accounts]
                    selected_index = 0
                    
                    if st.session_state.get("selected_account"):
                        for i, account in enumerate(accounts):
                            if account.id == st.session_state["selected_account"]:
                                selected_index = i + 1
                                break
                    
                    account_selection = st.selectbox(
                        "Select Account",
                        options=account_options,
                        index=selected_index
                    )
                    
                    if account_selection != "Select an account":
                        selected_index = account_options.index(account_selection) - 1
                        st.session_state["selected_account"] = accounts[selected_index].id
                else:
                    st.info("No accounts added yet. Go to Accounts page to add one.")
                
                # Logout
                st.markdown("---")
                if st.button("🚪 Logout", use_container_width=True):
                    logout()
                    st.experimental_rerun()
            
            # Render the selected page
            try:
                # Verify authentication
                require_auth()
                
                # Show the selected page
                if st.session_state["page"] == "home":
                    show_home_page()
                elif st.session_state["page"] == "accounts":
                    show_accounts_page()
                elif st.session_state["page"] == "posts":
                    show_posts_page()
                elif st.session_state["page"] == "comments":
                    show_comments_page()
                elif st.session_state["page"] == "settings":
                    show_settings_page()
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
    except Exception as e:
        st.error(f"Failed to initialize application: {str(e)}")
        st.warning("Please check your database connection and configuration settings.")


if __name__ == "__main__":
    main()
