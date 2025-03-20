import streamlit as st
import jwt
import bcrypt
import datetime
from utils.db import get_user_by_username, create_user, update_password
from config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRATION


def create_jwt_token(user_id, username):
    """Create a JWT token for the authenticated user"""
    try:
        payload = {
            "user_id": user_id,
            "username": username,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(seconds=JWT_EXPIRATION)
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        return token
    except Exception as e:
        st.error(f"Error creating JWT token: {str(e)}")
        return None


def verify_jwt_token(token):
    """Verify the JWT token and return the payload if valid"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    except Exception as e:
        st.error(f"Error verifying JWT token: {str(e)}")
        return None


def login(username, password):
    """Authenticate the user and create a session"""
    user = get_user_by_username(username)
    
    if not user:
        return False, "Invalid username or password"
    
    # Verify password
    try:
        if not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            return False, "Invalid username or password"
    except Exception as e:
        return False, f"Authentication error: {str(e)}"
    
    # Create JWT token
    token = create_jwt_token(user.id, user.username)
    
    if not token:
        return False, "Failed to create authentication token"
    
    # Store in session state
    st.session_state["authenticated"] = True
    st.session_state["user_id"] = user.id
    st.session_state["username"] = user.username
    st.session_state["token"] = token
    
    return True, None


def logout():
    """Clear the user session"""
    for key in ["authenticated", "user_id", "username", "token"]:
        if key in st.session_state:
            del st.session_state[key]


def require_auth():
    """Require authentication to access a page"""
    # Check if the user is authenticated
    if not st.session_state.get("authenticated", False):
        st.warning("Please log in to access this page")
        st.stop()
        
    # Verify the token
    token = st.session_state.get("token")
    if not token:
        logout()
        st.warning("Session information is missing. Please log in again.")
        st.stop()
        
    payload = verify_jwt_token(token)
    
    if not payload:
        logout()
        st.warning("Your session has expired. Please log in again.")
        st.stop()
        
    return payload


def register_user(username, password, email):
    """Register a new user"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    # Create the user in the database
    user, error = create_user(username, password, email)
    
    if error:
        return False, error
    
    # Create JWT token and store in session
    token = create_jwt_token(user.id, user.username)
    
    if not token:
        return False, "User created but failed to generate authentication token"
    
    st.session_state["authenticated"] = True
    st.session_state["user_id"] = user.id
    st.session_state["username"] = user.username
    st.session_state["token"] = token
    
    return True, None


def change_password(user_id, current_password, new_password):
    """Change user password"""
    user = get_user_by_username(st.session_state["username"])
    
    # Verify current password
    try:
        if not bcrypt.checkpw(current_password.encode('utf-8'), user.password_hash.encode('utf-8')):
            return False, "Current password is incorrect"
    except Exception as e:
        return False, f"Password verification error: {str(e)}"
    
    if len(new_password) < 8:
        return False, "New password must be at least 8 characters long"
    
    # Update the password
    success, error = update_password(user_id, new_password)
    
    if not success:
        return False, error
    
    return True, None


def show_login_form():
    """Show the login form and handle login logic"""
    st.title("Login")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            if not username or not password:
                st.error("Please provide both username and password")
            else:
                success, error = login(username, password)
                if not success:
                    st.error(error)
                else:
                    st.success("Login successful")
                    st.experimental_rerun()
    
    # Registration link
    st.markdown("---")
    if st.button("Create New Account"):
        st.session_state["show_register"] = True
    
    # Forgot password link
    if st.button("Forgot Password?"):
        st.session_state["show_forgot_password"] = True


def show_registration_form():
    """Show the registration form and handle registration logic"""
    st.title("Create New Account")
    
    with st.form("register_form"):
        username = st.text_input("Username")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        submit = st.form_submit_button("Register")
        
        if submit:
            if not username or not email or not password or not confirm_password:
                st.error("Please fill in all fields")
            elif password != confirm_password:
                st.error("Passwords do not match")
            else:
                success, error = register_user(username, password, email)
                if not success:
                    st.error(error)
                else:
                    st.success("Registration successful")
                    st.experimental_rerun()
    
    # Back to login link
    if st.button("Back to Login"):
        st.session_state["show_register"] = False
