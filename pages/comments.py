import streamlit as st
import pandas as pd
from utils.fb_api import (
    get_account_api, get_page_posts, format_post_data,
    get_post_comments, format_comment_data,
    reply_to_comment, edit_comment, delete_comment
)


def show_comments_page():
    """Display the comments management page"""
    st.header("💬 Comments Management")
    
    # Check if account is selected
    if not st.session_state.get("selected_account"):
        st.info("Please select a Facebook account from the sidebar to manage comments.")
        return
    
    # Get API client for the selected account
    api, account = get_account_api(st.session_state["selected_account"], st.session_state["user_id"])
    
    if not api or not account:
        st.error("Could not connect to the selected Facebook account. Please check your account settings.")
        return
    
    st.subheader(f"Comments for {account.account_name}")
    
    # Step 1: Select a post
    if not st.session_state.get("selected_post"):
        # Fetch and display posts first
        with st.spinner("Loading posts..."):
            posts = get_page_posts(api, account.page_id, limit=25)
            df_posts = format_post_data(posts)
        
        if df_posts.empty:
            st.info("No posts found for this account.")
            return
        
        st.markdown("### Select a Post to View Comments")
        
        # Display the posts in a table
        st.dataframe(
            df_posts[["created_time", "short_message", "comments"]],
            use_container_width=True,
            hide_index=True
        )
        
        # Add functionality to select a post
        post_options = [f"{row['created_time']} - {row['short_message']} ({row['comments']} comments)" for _, row in df_posts.iterrows()]
        post_options.insert(0, "Select a post")
        
        selected_post_option = st.selectbox(
            "Select a post to manage comments",
            options=post_options
        )
        
        if selected_post_option != "Select a post":
            selected_index = post_options.index(selected_post_option) - 1
            selected_post_id = posts[selected_index]["id"]
            st.session_state["selected_post"] = selected_post_id
            st.experimental_rerun()
    
    else:
        # Step 2: Show comments for the selected post
        selected_post_id = st.session_state["selected_post"]
        
        # Add a button to go back to post selection
        if st.button("← Back to Post Selection"):
            st.session_state.pop("selected_post")
            st.experimental_rerun()
        
        # Fetch post details
        try:
            post_details = api.get_object(
                id=selected_post_id,
                fields="message,created_time,permalink_url"
            )
            
            # Display post info
            st.markdown(f"**Post Date:** {post_details.get('created_time')}")
            st.markdown(f"**Post Message:**")
            st.markdown(f"> {post_details.get('message', 'No message')}")
            
            # Add post permalink
            permalink = post_details.get('permalink_url')
            if permalink:
                st.markdown(f"[View Post on Facebook]({permalink})")
        
        except Exception as e:
            st.error(f"Error fetching post details: {str(e)}")
        
        # Add refresh button for comments
        if st.button("🔄 Refresh Comments"):
            st.experimental_rerun()
        
        # Fetch comments
        with st.spinner("Loading comments..."):
            comments = get_post_comments(api, selected_post_id)
            df_comments = format_comment_data(comments)
        
        if df_comments.empty:
            st.info("No comments found for this post.")
            
            # Add a form to add a new comment/reply
            with st.form("add_comment_form"):
                st.subheader("Add a comment")
                comment_message = st.text_area("Your comment", height=100)
                submit = st.form_submit_button("Post Comment")
                
                if submit:
                    if not comment_message:
                        st.error("Please enter a comment message.")
                    else:
                        comment_id, error = reply_to_comment(api, selected_post_id, comment_message)
                        
                        if error:
                            st.error(f"Failed to post comment: {error}")
                        else:
                            st.success("Comment posted successfully!")
                            st.experimental_rerun()
        else:
            # Display comments
            st.subheader(f"Comments ({len(comments)})")
            
            # Show comments in a table
            st.dataframe(
                df_comments[["created_time", "from_name", "short_message", "replies"]],
                use_container_width=True,
                hide_index=True
            )
            
            # Comment management
            st.markdown("### Manage Comments")
            
            # Select a comment
            comment_options = [f"{row['created_time']} - {row['from_name']}: {row['short_message']}" for _, row in df_comments.iterrows()]
            comment_options.insert(0, "Select a comment to manage")
            
            selected_comment_option = st.selectbox(
                "Select a comment",
                options=comment_options
            )
            
            if selected_comment_option != "Select a comment to manage":
                selected_index = comment_options.index(selected_comment_option) - 1
                selected_comment = comments[selected_index]
                selected_comment_id = selected_comment["id"]
                
                # Display comment details
                st.markdown(f"**From:** {selected_comment['from_name']}")
                st.markdown(f"**Date:** {selected_comment['created_time']}")
                st.markdown(f"**Message:**")
                st.markdown(f"> {selected_comment['message']}")
                
                # Comment actions
                st.markdown("### Actions")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("Reply", use_container_width=True):
                        st.session_state["reply_to_comment"] = selected_comment_id
                
                with col2:
                    if st.button("Edit (Admin Only)", use_container_width=True):
                        # Check if it's the page's comment
                        if selected_comment.get("from_id") == account.page_id:
                            st.session_state["edit_comment"] = selected_comment_id
                        else:
                            st.error("You can only edit comments made by your page.")
                
                with col3:
                    if st.button("Delete", use_container_width=True):
                        st.session_state["delete_comment"] = selected_comment_id
                
                # Reply to comment form
                if st.session_state.get("reply_to_comment") == selected_comment_id:
                    st.markdown("### Reply to Comment")
                    
                    with st.form("reply_comment_form"):
                        reply_message = st.text_area("Your reply", height=100)
                        submit = st.form_submit_button("Post Reply")
                        
                        if submit:
                            if not reply_message:
                                st.error("Please enter a reply message.")
                            else:
                                reply_id, error = reply_to_comment(api, selected_comment_id, reply_
