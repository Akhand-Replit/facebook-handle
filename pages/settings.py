import streamlit as st
from utils.auth import change_password, logout


def show_settings_page():
    """Display the settings page"""
    st.header("⚙️ Settings")
    
    # Create tabs for different settings sections
    tab1, tab2 = st.tabs(["Account Settings", "App Preferences"])
    
    # Account Settings tab
    with tab1:
        st.subheader("Account Information")
        
        # Display current user information
        st.markdown(f"**Username:** {st.session_state['username']}")
        
        # Change password section
        st.markdown("---")
        st.subheader("Change Password")
        
        with st.form("change_password_form"):
            current_password = st.text_input("Current Password", type="password")
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm New Password", type="password")
            
            submit = st.form_submit_button("Change Password")
            
            if submit:
                if not current_password or not new_password or not confirm_password:
                    st.error("Please fill in all password fields.")
                elif new_password != confirm_password:
                    st.error("New passwords do not match.")
                else:
                    success, error = change_password(
                        st.session_state["user_id"],
                        current_password,
                        new_password
                    )
                    
                    if success:
                        st.success("Password changed successfully!")
                        # Force re-login
                        st.info("Please log in again with your new password.")
                        logout()
                        st.experimental_rerun()
                    else:
                        st.error(error)
    
    # App Preferences tab
    with tab2:
        st.subheader("Display Settings")
        
        # Theme selection
        theme = st.selectbox(
            "Theme",
            options=["Default", "Light", "Dark"],
            index=0
        )
        
        # Posts per page setting
        posts_per_page = st.slider(
            "Default posts to load",
            min_value=5,
            max_value=100,
            value=25,
            step=5
        )
        
        # Date format preference
        date_format = st.selectbox(
            "Date format",
            options=["MM/DD/YYYY", "DD/MM/YYYY", "YYYY-MM-DD"],
            index=2
        )
        
        # Save preferences button
        if st.button("Save Preferences"):
            # Store preferences in session state
            st.session_state["preferences"] = {
                "theme": theme,
                "posts_per_page": posts_per_page,
                "date_format": date_format
            }
            st.success("Preferences saved successfully!")
