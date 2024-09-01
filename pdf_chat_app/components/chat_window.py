import streamlit as st
from pdf_chat_app.src.chat_handler import initialize_thread, chat_with_assistant, stream_string

def render_chat_window(api_key, pdf_content):
    if not api_key:
        st.warning("Please enter your OpenAI API key in the sidebar to use the chat feature.")
        return

    # Initialize chat history
    if 'chat_history' not in st.session_state:
        st.session_state['chat_history'] = initialize_thread(pdf_content)

    # Create a container for the entire chat interface
    chat_container = st.container()

    # Chat history container
    chat_history_container = chat_container.container(height=600)

    # Display chat messages from history
    with chat_history_container:
        for message in st.session_state['chat_history'][2:]:  # Skip the system message and initial PDF content
            with st.chat_message(message["role"]):
                st.write(message["content"])

    # Chat input at the bottom
    user_input = st.chat_input("Ask a question about the PDF document...")
    if user_input:
        handle_user_input(api_key, user_input, chat_history_container)

def handle_user_input(api_key, user_input, chat_history_container):
    # Add user message to chat history and display it
    st.session_state['chat_history'].append({"role": "user", "content": user_input})
    with chat_history_container:
        with st.chat_message("user"):
            st.write(user_input)

    # Get assistant response
    with chat_history_container:
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            with st.status("Processing...", expanded=False):
                try:
                    responses = chat_with_assistant(api_key, st.session_state['chat_history'], user_input)
                    for response in responses:
                        if response[0] == 'assistant':
                            for chunk in stream_string(response[1]):
                                full_response += chunk
                                message_placeholder.markdown(full_response + "▌")
                            message_placeholder.markdown(full_response)
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")

    # Append assistant's response to chat history
    st.session_state['chat_history'].append({"role": "assistant", "content": full_response})