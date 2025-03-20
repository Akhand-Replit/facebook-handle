import streamlit as st
import pandas as pd
from utils.fb_api import get_account_api, get_page_posts, format_post_data, create_post, edit_post, delete_post


def show_posts_page():
    """Display the posts management page"""
    st.header("📝 Posts Management")
    
    # Check if account is selected
    if not st.session_state.get("selected_account"):
        st.info("Please select a Facebook account from the sidebar to manage posts.")
        return
    
    # Get API client for the selected account
    api, account = get_account_api(st.session_state["selected_account"], st.session_state["user_id"])
    
    if not api or not account:
        st.error("Could not connect to the selected Facebook account. Please check your account settings.")
        return
    
    # Create tabs for posts and create new post
    tab1, tab2 = st.tabs(["View Posts", "Create New Post"])
    
    # View posts tab
    with tab1:
        st.subheader(f"Posts for {account.account_name}")
        
        # Add filter and reload controls
        col1, col2 = st.columns([3, 1])
        
        with col1:
            post_limit = st.slider("Number of posts to load", min_value=5, max_value=100, value=25, step=5)
        
        with col2:
            if st.button("🔄 Refresh Posts", use_container_width=True):
                st.experimental_rerun()
        
        # Fetch and display posts
        with st.spinner("Loading posts..."):
            posts = get_page_posts(api, account.page_id, limit=post_limit)
            df_posts = format_post_data(posts)
        
        if df_posts.empty:
            st.info("No posts found for this account.")
        else:
            # Display the posts in a table
            st.dataframe(
                df_posts[["created_time", "short_message", "reactions", "comments", "shares", "engagement"]],
                use_container_width=True,
                hide_index=True
            )
            
            # Add functionality to select a post for more details
            post_options = [f"{row['created_time']} - {row['short_message']}" for _, row in df_posts.iterrows()]
            post_options.insert(0, "Select a post to view details")
            
            selected_post_option = st.selectbox(
                "Select a post to view or manage",
                options=post_options
            )
            
            if selected_post_option != "Select a post to view details":
                selected_index = post_options.index(selected_post_option) - 1
                selected_post_id = posts[selected_index]["id"]
                st.session_state["selected_post"] = selected_post_id
                
                # Display post details
                selected_post = posts[selected_index]
                
                st.markdown("### Post Details")
                
                # Display post content
                st.markdown(f"**Posted on:** {selected_post['created_time']}")
                st.markdown(f"**Message:**")
                st.markdown(f"> {selected_post['message']}")
                
                # Display post stats
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Reactions", selected_post["reactions"])
                with col2:
                    st.metric("Comments", selected_post["comments"])
                with col3:
                    st.metric("Shares", selected_post["shares"])
                
                # Post view/edit/delete options
                st.markdown("### Post Actions")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("View on Facebook", use_container_width=True):
                        permalink_url = selected_post.get("permalink_url", "")
                        if permalink_url:
                            st.markdown(f"[Open Post on Facebook]({permalink_url})")
                        else:
                            st.error("Permalink not available")
                
                with col2:
                    if st.button("Edit Post", use_container_width=True):
                        st.session_state["edit_post"] = True
                
                with col3:
                    if st.button("Delete Post", use_container_width=True):
                        st.session_state["delete_post"] = True
                
                # Edit post form
                if st.session_state.get("edit_post", False):
                    st.markdown("### Edit Post")
                    
                    with st.form("edit_post_form"):
                        edited_message = st.text_area("Edit Message", value=selected_post["message"], height=150)
                        submit = st.form_submit_button("Update Post")
                        
                        if submit:
                            success, error = edit_post(api, selected_post_id, edited_message)
                            
                            if success:
                                st.success("Post updated successfully!")
                                st.session_state.pop("edit_post", None)
                                st.experimental_rerun()
                            else:
                                st.error(f"Failed to update post: {error}")
                
                # Delete post confirmation
                if st.session_state.get("delete_post", False):
                    st.markdown("### Delete Post")
                    st.warning("Are you sure you want to delete this post? This action cannot be undone.")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("Yes, Delete Post", use_container_width=True):
                            success, error = delete_post(api, selected_post_id)
                            
                            if success:
                                st.success("Post deleted successfully!")
                                st.session_state.pop("delete_post", None)
                                st.session_state.pop("selected_post", None)
                                st.experimental_rerun()
                            else:
                                st.error(f"Failed to delete post: {error}")
                    
                    with col2:
                        if st.button("Cancel", use_container_width=True):
                            st.session_state.pop("delete_post", None)
                            st.experimental_rerun()
    
    # Create new post tab
    with tab2:
        st.subheader(f"Create New Post for {account.account_name}")
        
        with st.form("create_post_form"):
            post_message = st.text_area("Post Message", height=200, placeholder="What's on your mind?")
            post_link = st.text_input("Link (optional)", placeholder="https://example.com")
            
            # Submit button
            submit = st.form_submit_button("Create Post")
            
            if submit:
                if not post_message:
                    st.error("Please enter a message for your post.")
                else:
                    # Create the post
                    post_id, error = create_post(
                        api,
                        account.page_id,
                        post_message,
                        link=post_link if post_link else None
                    )
                    
                    if error:
                        st.error(f"Failed to create post: {error}")
                    else:
                        st.success("Post created successfully!")
                        st.session_state["selected_post"] = post_id
                        st.experimental_rerun()
