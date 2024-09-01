import streamlit as st
from pdf_chat_app.config.config import CONTEXT_SIZE_WORDS

def render_sidebar():
    with st.sidebar:
        st.title("PDF Chat App")
        
        st.subheader("1. API Setup")
        api_key = st.text_input("Enter your OpenAI API key", type="password")

        st.divider()

        st.subheader("2. PDF Processing Settings")
        process_images = st.checkbox("Process images", value=True)
        if process_images:
            context_size = st.number_input(
                "Context size (words before/after image)", 
                min_value=10, 
                max_value=500, 
                value=CONTEXT_SIZE_WORDS
            )
            user_prompt = st.text_area("Image description instructions (optional)")
        else:
            context_size = CONTEXT_SIZE_WORDS
            user_prompt = ""
        
        use_descriptions = st.toggle("Use document with image descriptions", value=True)
        
        st.divider()

        st.subheader("3. Process PDF")
        process_button = st.button("Process PDF", use_container_width=True, type="primary")
        
        # Processing status
        if 'processing_status' not in st.session_state:
            st.session_state.processing_status = 'idle'
        
        status_container = st.empty()
        
        if st.session_state.processing_status == 'processing':
            status_container.progress(50, "Processing...")
            st.info("PDF is being processed. This may take a moment.")
        elif st.session_state.processing_status == 'completed':
            status_container.progress(100)
            st.success("PDF processed successfully!")
        elif st.session_state.processing_status == 'error':
            status_container.empty()
            st.error("An error occurred while processing the PDF.")
        else:
            status_container.empty()

        st.divider()

        st.subheader("4. Chat Options")
        reload_chat = st.button("Reload Chat", use_container_width=True)
        st.caption("This will clear the chat history and start over.")

        st.divider()
        
        st.caption("PDF Chat App v1.0")
        st.caption("Created with ❤️ by Ernesto Ponce")

    return api_key, user_prompt, process_images, process_button, context_size, use_descriptions, reload_chat