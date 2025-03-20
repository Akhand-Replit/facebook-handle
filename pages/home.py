import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from utils.db import get_user_accounts
from utils.fb_api import get_account_api, get_page_posts, get_page_insights, format_post_data


def show_home_page():
    """Display the home page (dashboard)"""
    st.header("📊 Dashboard")
    
    # Check if account is selected
    if not st.session_state.get("selected_account"):
        st.info("Please select a Facebook account from the sidebar to view the dashboard.")
        return
    
    # Get API client for the selected account
    api, account = get_account_api(st.session_state["selected_account"], st.session_state["user_id"])
    
    if not api or not account:
        st.error("Could not connect to the selected Facebook account. Please check your account settings.")
        return
    
    # Display page information
    st.subheader(f"Page: {account.account_name}")
    
    # Add date range selector
    col1, col2 = st.columns(2)
    with col1:
        days_options = {"Last 7 days": 7, "Last 14 days": 14, "Last 30 days": 30}
        selected_days = st.selectbox("Time period", options=list(days_options.keys()), index=2)
        days = days_options[selected_days]
    
    with col2:
        period_options = {"Day": "day", "Week": "week", "Days 28": "days_28"}
        selected_period = st.selectbox("Aggregation", options=list(period_options.keys()), index=0)
        period = period_options[selected_period]
    
    # Fetch insights data
    with st.spinner("Loading page insights..."):
        insights = get_page_insights(api, account.page_id, period=period, days=days)
    
    if not insights:
        st.warning("Could not fetch page insights. This might be due to API permissions or rate limits.")
    else:
        # Display key metrics in cards
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Page Fans",
                value=f"{insights.get('page_fans', 0):,}"
            )
        
        with col2:
            st.metric(
                label="New Fans",
                value=f"{insights.get('page_fan_adds', 0):,}"
            )
        
        with col3:
            st.metric(
                label="Impressions",
                value=f"{insights.get('page_impressions', 0):,}"
            )
        
        with col4:
            st.metric(
                label="Engagements",
                value=f"{insights.get('page_post_engagements', 0):,}"
            )
            
        # Create engagement rate
        if insights.get('page_impressions', 0) > 0:
            engagement_rate = (insights.get('page_post_engagements', 0) / insights.get('page_impressions', 0)) * 100
        else:
            engagement_rate = 0
            
        # Create a gauge chart for engagement rate
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=engagement_rate,
            title={"text": "Engagement Rate (%)"},
            gauge={
                "axis": {"range": [0, 10], "tickwidth": 1, "tickcolor": "darkblue"},
                "bar": {"color": "royalblue"},
                "bgcolor": "white",
                "borderwidth": 2,
                "bordercolor": "gray",
                "steps": [
                    {"range": [0, 2], "color": "lightgray"},
                    {"range": [2, 5], "color": "lightblue"},
                    {"range": [5, 10], "color": "lightgreen"}
                ]
            }
        ))
        fig.update_layout(height=250, margin=dict(l=10, r=10, t=30, b=10))
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Display recent posts
    st.subheader("Recent Posts")
    
    with st.spinner("Loading recent posts..."):
        posts = get_page_posts(api, account.page_id, limit=10)
        df_posts = format_post_data(posts)
    
    if df_posts.empty:
        st.info("No posts found for this account.")
    else:
        # Create a bar chart of engagement by post
        if "engagement" in df_posts.columns and "created_time" in df_posts.columns:
            fig = px.bar(
                df_posts,
                x="created_time",
                y="engagement",
                hover_data=["short_message"],
                labels={"created_time": "Date", "engagement": "Total Engagement"},
                title="Engagement by Post"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Display the posts in a table
        st.dataframe(
            df_posts[["created_time", "short_message", "reactions", "comments", "shares", "engagement"]],
            use_container_width=True,
            hide_index=True
        )
        
    # Add a refresh button
    if st.button("🔄 Refresh Dashboard"):
        st.experimental_rerun()
