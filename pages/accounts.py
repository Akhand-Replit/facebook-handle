import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils.db import get_user_accounts, add_facebook_account, update_facebook_account, delete_facebook_account
from utils.fb_api import get_facebook_api


def show_accounts_page():
    """Display the accounts management page"""
    st.header("📱 Facebook Accounts")
    
    # Get user accounts
    accounts = get_user_accounts(st.session_state["user_id"])
    
    # Create tabs for accounts list and add new account
    tab1, tab2 = st.tabs(["My Accounts", "Add New Account"])
    
    # Accounts list tab
    with tab1:
        if not accounts:
            st.info("You don't have any Facebook accounts added yet. Go to the 'Add New Account' tab to add one.")
        else:
            # Display accounts in a table
            accounts_data = []
            for account in accounts:
                # Format expires_at date
                expires_at = account.expires_at.strftime("%Y-%m-%d") if account.expires_at else "Never"
                
                # Check if token is expired
                is_expired = False
                if account.expires_at and account.expires_at < datetime.now():
                    is_expired = True
                
                accounts_data.append({
                    "id": account.id,
                    "name": account.account_name,
                    "page_id": account.page_id,
                    "token_status": "Expired" if is_expired else "Active",
                    "expires_at": expires_at
                })
            
            df_accounts = pd.DataFrame(accounts_data)
            
            if not df_accounts.empty:
                # Use Streamlit's built-in data editor for a better UX
                st.dataframe(
                    df_accounts[["name", "page_id", "token_status", "expires_at"]],
                    use_container_width=True,
                    hide_index=True
                )
                
                # Account management
                st.subheader("Manage Selected Account")
                
                # Account selection for management
                account_names = [f"{account.account_name} ({account.page_id})" for account in accounts]
                selected_account_name = st.selectbox(
                    "Select Account to Manage",
                    options=account_names
                )
                
                # Find the selected account
                selected_index = account_names.index(selected_account_name)
                selected_account = accounts[selected_index]
                
                # Show account management options
                col1, col2 = st.columns(2)
                
                with col1:
                    # Edit account
                    with st.expander("Edit Account"):
                        with st.form("edit_account_form"):
                            account_name = st.text_input("Account Name", value=selected_account.account_name)
                            access_token = st.text_input("Access Token (leave blank to keep current)", value="", type="password")
                            token_expiry = st.date_input(
                                "Token Expiry Date (leave blank for never)",
                                value=selected_account.expires_at if selected_account.expires_at else None,
                                min_value=datetime.now().date()
                            )
                            
                            submit = st.form_submit_button("Update Account")
                            
                            if submit:
                                # Convert expiry date to datetime or None
                                expires_at = datetime.combine(token_expiry, datetime.min.time()) if token_expiry else None
                                
                                # Update the account
                                success, error = update_facebook_account(
                                    selected_account.id,
                                    account_name=account_name,
                                    access_token=access_token if access_token else None,
                                    expires_at=expires_at
                                )
                                
                                if success:
                                    st.success("Account updated successfully!")
                                    st.experimental_rerun()
                                else:
                                    st.error(f"Failed to update account: {error}")
                
                with col2:
                    # Test connection
                    with st.expander("Test Connection"):
                        if st.button("Test Facebook API Connection"):
                            try:
                                api = get_facebook_api(selected_account.access_token)
                                page_info = api.get_object(id=selected_account.page_id, fields="name,fan_count")
                                
                                st.success(f"Connection successful!")
                                st.write(f"Page Name: {page_info.get('name')}")
                                st.write(f"Fan Count: {page_info.get('fan_count', 0)}")
                            except Exception as e:
                                st.error(f"Connection failed: {str(e)}")
                    
                    # Delete account
                    with st.expander("Delete Account"):
                        st.warning("This action cannot be undone!")
                        delete_confirmation = st.text_input(
                            f"Type '{selected_account.account_name}' to confirm deletion",
                            key="delete_confirmation"
                        )
                        
                        if st.button("Delete Account"):
                            if delete_confirmation == selected_account.account_name:
                                success, error = delete_facebook_account(selected_account.id)
                                
                                if success:
                                    st.success("Account deleted successfully!")
                                    st.session_state["selected_account"] = None
                                    st.experimental_rerun()
                                else:
                                    st.error(f"Failed to delete account: {error}")
                            else:
                                st.error("Confirmation text does not match account name.")
    
    # Add new account tab
    with tab2:
        with st.form("add_account_form"):
            st.subheader("Add New Facebook Account")
            
            # Form fields
            account_name = st.text_input("Account Name (for your reference)")
            page_id = st.text_input("Facebook Page ID")
            access_token = st.text_input("Facebook Access Token", type="password")
            
            # Token expiration
            has_expiry = st.checkbox("Token has expiration date")
            expiry_date = None
            
            if has_expiry:
                expiry_date = st.date_input(
                    "Token Expiry Date",
                    value=datetime.now().date() + timedelta(days=60),
                    min_value=datetime.now().date()
                )
            
            # Help text
            st.markdown("""
            ### How to get your Facebook Access Token:
            1. Go to [Facebook for Developers](https://developers.facebook.com)
            2. Create or use an existing app
            3. Add the "Pages" product to your app
            4. Generate a user token with `pages_manage_posts`, `pages_read_engagement`, and `pages_show_list` permissions
            5. Use the Access Token Tool to generate a Page Access Token
            
            ### Find your Page ID:
            - Go to your Facebook Page
            - Your Page ID is in the URL: `facebook.com/your_page_name/` or in the Page Info section
            """)
            
            # Submit button
            submit = st.form_submit_button("Add Account")
            
            if submit:
                if not account_name or not page_id or not access_token:
                    st.error("Please fill in all required fields.")
                else:
                    # Convert expiry date to datetime or None
                    expires_at = datetime.combine(expiry_date, datetime.min.time()) if expiry_date else None
                    
                    # Test the connection before adding
                    try:
                        # Validate the token by making a test request
                        api = get_facebook_api(access_token)
                        page_info = api.get_object(id=page_id, fields="name")
                        
                        # Add the account to the database
                        account, error = add_facebook_account(
                            st.session_state["user_id"],
                            account_name,
                            page_id,
                            access_token,
                            expires_at
                        )
                        
                        if error:
                            st.error(f"Failed to add account: {error}")
                        else:
                            st.success(f"Account '{account_name}' added successfully!")
                            st.session_state["selected_account"] = account.id
                            st.experimental_rerun()
                            
                    except Exception as e:
                        st.error(f"Failed to validate Facebook access token: {str(e)}")
