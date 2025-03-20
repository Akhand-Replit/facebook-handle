import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
import pandas as pd
import streamlit as st
from config import DATABASE_URL
import bcrypt
import datetime

Base = declarative_base()

# Create database engine and session with better error handling
try:
    # Connect to database using the URL from config
    engine = sa.create_engine(DATABASE_URL)
    SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
except Exception as e:
    st.error(f"Database connection error: {e}")
    # We'll handle this during app initialization


# Database Models
class User(Base):
    __tablename__ = "users"

    id = sa.Column(sa.Integer, primary_key=True, index=True)
    username = sa.Column(sa.String, unique=True, index=True)
    password_hash = sa.Column(sa.String)
    email = sa.Column(sa.String, unique=True, index=True)
    created_at = sa.Column(sa.DateTime, server_default=sa.func.now())
    updated_at = sa.Column(sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now())


class FacebookAccount(Base):
    __tablename__ = "facebook_accounts"

    id = sa.Column(sa.Integer, primary_key=True, index=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey("users.id"))
    account_name = sa.Column(sa.String)
    page_id = sa.Column(sa.String)
    access_token = sa.Column(sa.String)
    expires_at = sa.Column(sa.DateTime, nullable=True)
    created_at = sa.Column(sa.DateTime, server_default=sa.func.now())
    updated_at = sa.Column(sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now())


# Database initialization function
def init_db():
    try:
        Base.metadata.create_all(bind=engine)
        return True
    except Exception as e:
        st.error(f"Failed to initialize database: {e}")
        return False


# Helper functions for database operations
def get_user_by_username(username):
    db = SessionLocal()
    try:
        return db.query(User).filter(User.username == username).first()
    finally:
        db.close()


def get_user_by_id(user_id):
    db = SessionLocal()
    try:
        return db.query(User).filter(User.id == user_id).first()
    finally:
        db.close()


def create_user(username, password, email):
    db = SessionLocal()
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing_user:
            return None, "Username or email already exists"
        
        # Hash the password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Create new user
        new_user = User(username=username, password_hash=password_hash, email=email)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user, None
    except Exception as e:
        db.rollback()
        return None, str(e)
    finally:
        db.close()


def update_password(user_id, new_password):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, "User not found"
        
        # Hash the new password
        password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        user.password_hash = password_hash
        db.commit()
        return True, None
    except Exception as e:
        db.rollback()
        return False, str(e)
    finally:
        db.close()


def get_user_accounts(user_id):
    db = SessionLocal()
    try:
        accounts = db.query(FacebookAccount).filter(FacebookAccount.user_id == user_id).all()
        return accounts
    finally:
        db.close()


def add_facebook_account(user_id, account_name, page_id, access_token, expires_at=None):
    db = SessionLocal()
    try:
        # Check if account already exists
        existing_account = db.query(FacebookAccount).filter(
            (FacebookAccount.user_id == user_id) & 
            (FacebookAccount.page_id == page_id)
        ).first()
        
        if existing_account:
            return None, "Account already exists"
        
        # Create new account
        new_account = FacebookAccount(
            user_id=user_id,
            account_name=account_name,
            page_id=page_id,
            access_token=access_token,
            expires_at=expires_at
        )
        
        db.add(new_account)
        db.commit()
        db.refresh(new_account)
        return new_account, None
    except Exception as e:
        db.rollback()
        return None, str(e)
    finally:
        db.close()


def update_facebook_account(account_id, account_name=None, access_token=None, expires_at=None):
    db = SessionLocal()
    try:
        account = db.query(FacebookAccount).filter(FacebookAccount.id == account_id).first()
        
        if not account:
            return False, "Account not found"
        
        if account_name:
            account.account_name = account_name
        
        if access_token:
            account.access_token = access_token
            
        if expires_at:
            account.expires_at = expires_at
            
        db.commit()
        return True, None
    except Exception as e:
        db.rollback()
        return False, str(e)
    finally:
        db.close()


def delete_facebook_account(account_id):
    db = SessionLocal()
    try:
        account = db.query(FacebookAccount).filter(FacebookAccount.id == account_id).first()
        
        if not account:
            return False, "Account not found"
        
        db.delete(account)
        db.commit()
        return True, None
    except Exception as e:
        db.rollback()
        return False, str(e)
    finally:
        db.close()


# Cache the database connection in the Streamlit session
@st.cache_resource
def get_db_connection():
    return engine
