import facebook
import streamlit as st
import pandas as pd
import datetime
from utils.db import get_user_accounts
import re

# Create a cache for Facebook API clients to avoid recreating them
@st.cache_resource(ttl=3600)  # Cache for 1 hour
def get_facebook_api(access_token):
    """Get a Facebook Graph API client with the given access token"""
    try:
        return facebook.GraphAPI(access_token=access_token, version="v18.0")
    except Exception as e:
        st.error(f"Error initializing Facebook API: {str(e)}")
        return None


def get_account_api(account_id, user_id):
    """Get a Facebook Graph API client for a specific account"""
    accounts = get_user_accounts(user_id)
    
    for account in accounts:
        if account.id == account_id:
            return get_facebook_api(account.access_token), account
    
    return None, None


def get_page_posts(api, page_id, limit=25):
    """Get posts from a Facebook page"""
    try:
        posts = api.get_connections(
            id=page_id,
            connection_name="posts",
            fields="id,message,created_time,permalink_url,shares,reactions.summary(true),comments.summary(true)",
            limit=limit
        )
        
        post_list = []
        while posts:
            for post in posts["data"]:
                post_data = {
                    "id": post.get("id"),
                    "message": post.get("message", ""),
                    "created_time": post.get("created_time"),
                    "permalink_url": post.get("permalink_url"),
                    "shares": post.get("shares", {}).get("count", 0) if post.get("shares") else 0,
                    "reactions": post.get("reactions", {}).get("summary", {}).get("total_count", 0) if post.get("reactions") else 0,
                    "comments": post.get("comments", {}).get("summary", {}).get("total_count", 0) if post.get("comments") else 0
                }
                post_list.append(post_data)
            
            # Get next page if available
            if "paging" in posts and "next" in posts["paging"]:
                posts = api.get_object(posts["paging"]["next"])
            else:
                break
                
        return post_list
    except facebook.GraphAPIError as e:
        st.error(f"Facebook API Error: {e}")
        return []


def format_post_data(posts):
    """Format post data for display in a DataFrame"""
    if not posts:
        return pd.DataFrame()
    
    df = pd.DataFrame(posts)
    
    # Convert created_time to datetime and format
    if "created_time" in df.columns and not df.empty:
        df["created_time"] = pd.to_datetime(df["created_time"]).dt.strftime("%Y-%m-%d %H:%M")
    
    # Add a shortened message column for display
    if "message" in df.columns and not df.empty:
        df["short_message"] = df["message"].str[:50] + "..."
    
    # Calculate engagement rate
    df["engagement"] = df["reactions"] + df["comments"] + df["shares"]
    
    return df


def create_post(api, page_id, message, link=None):
    """Create a new post on a Facebook page"""
    try:
        post_data = {"message": message}
        
        if link:
            post_data["link"] = link
            
        response = api.put_object(
            parent_object=page_id, 
            connection_name="feed",
            **post_data
        )
        
        return response.get("id"), None
    except facebook.GraphAPIError as e:
        return None, str(e)


def edit_post(api, post_id, message):
    """Edit an existing Facebook post"""
    try:
        api.put_object(
            parent_object=post_id,
            connection_name="",
            message=message
        )
        return True, None
    except facebook.GraphAPIError as e:
        return False, str(e)


def delete_post(api, post_id):
    """Delete a Facebook post"""
    try:
        api.delete_object(post_id)
        return True, None
    except facebook.GraphAPIError as e:
        return False, str(e)


def get_post_comments(api, post_id, limit=100):
    """Get comments for a specific post"""
    try:
        comments = api.get_connections(
            id=post_id,
            connection_name="comments",
            fields="id,message,created_time,from,comment_count,attachment",
            limit=limit
        )
        
        comment_list = []
        while comments:
            for comment in comments["data"]:
                comment_data = {
                    "id": comment.get("id"),
                    "message": comment.get("message", ""),
                    "created_time": comment.get("created_time"),
                    "from_name": comment.get("from", {}).get("name", "Unknown") if comment.get("from") else "Unknown",
                    "from_id": comment.get("from", {}).get("id", "") if comment.get("from") else "",
                    "replies": comment.get("comment_count", 0),
                    "has_attachment": "attachment" in comment
                }
                comment_list.append(comment_data)
            
            # Get next page if available
            if "paging" in comments and "next" in comments["paging"]:
                comments = api.get_object(comments["paging"]["next"])
            else:
                break
                
        return comment_list
    except facebook.GraphAPIError as e:
        st.error(f"Facebook API Error: {e}")
        return []


def format_comment_data(comments):
    """Format comment data for display in a DataFrame"""
    if not comments:
        return pd.DataFrame()
    
    df = pd.DataFrame(comments)
    
    # Convert created_time to datetime and format
    if "created_time" in df.columns and not df.empty:
        df["created_time"] = pd.to_datetime(df["created_time"]).dt.strftime("%Y-%m-%d %H:%M")
    
    # Add a shortened message column for display
    if "message" in df.columns and not df.empty:
        df["short_message"] = df["message"].apply(lambda x: str(x)[:50] + "..." if isinstance(x, str) and len(str(x)) > 50 else str(x))
    
    return df


def reply_to_comment(api, comment_id, message):
    """Reply to a Facebook comment"""
    try:
        response = api.put_object(
            parent_object=comment_id,
            connection_name="comments",
            message=message
        )
        return response.get("id"), None
    except facebook.GraphAPIError as e:
        return None, str(e)


def edit_comment(api, comment_id, message):
    """Edit a Facebook comment"""
    try:
        api.put_object(
            parent_object=comment_id,
            connection_name="",
            message=message
        )
        return True, None
    except facebook.GraphAPIError as e:
        return False, str(e)


def delete_comment(api, comment_id):
    """Delete a Facebook comment"""
    try:
        api.delete_object(comment_id)
        return True, None
    except facebook.GraphAPIError as e:
        return False, str(e)


def get_page_insights(api, page_id, period="day", days=30):
    """Get page insights for the specified period"""
    try:
        # Define the metrics to retrieve
        metrics = [
            "page_impressions",
            "page_impressions_unique",
            "page_engaged_users",
            "page_post_engagements",
            "page_fans",
            "page_fan_adds",
            "page_fan_removes"
        ]
        
        # Get the insights
        insights = api.get_connections(
            id=page_id,
            connection_name="insights",
            metric=",".join(metrics),
            period=period,
            date_preset="last_30d" if days == 30 else f"last_{days}d"
        )
        
        # Process the insights data
        insights_data = {}
        
        for metric in insights["data"]:
            metric_name = metric["name"]
            values = [point["value"] for point in metric["values"]]
            
            # For total metrics like page_fans, take the latest value
            if metric_name == "page_fans":
                insights_data[metric_name] = values[-1] if values else 0
            else:
                # For trend metrics, take the sum
                insights_data[metric_name] = sum(values) if values else 0
        
        return insights_data
    except facebook.GraphAPIError as e:
        st.error(f"Facebook API Error: {e}")
        return {}
