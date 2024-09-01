import os
import sys
import time

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

import streamlit as st
from pdf_chat_app.src.pdf_processor import process_pdf
from pdf_chat_app.components.sidebar import render_sidebar
from pdf_chat_app.components.pdf_viewer import render_pdf_viewer
from pdf_chat_app.components.chat_window import render_chat_window
from pdf_chat_app.src.chat_handler import chat_with_assistant

def main():
    # Set page configuration
    st.set_page_config(page_title='PDF Chat App', layout='wide')

    # App title
    st.title("📄 PDF Chat App")

    # Popover for app description with container width set to true
    with st.popover("What is this app?", use_container_width=True):
        st.markdown("""
        **Welcome to the PDF Chat App!** 🎉 

        This application allows you to **upload PDF documents** and interact with their content using a chat interface. 
        The app processes the PDF to extract text and images, providing a seamless way to ask questions and get insights about the document.

        ### Key Features:
        - **Upload a PDF**: Click on the "Choose a PDF file" button to upload your document.
        - **Set Your Preferences**: 
            - Enter your OpenAI API key.
            - Select your preferred chat model (**gpt-4o-mini** or **gpt-4o**) for interacting with the document.
            - Choose the image processing model to analyze visual elements in the PDF.
            - Provide any specific instructions for image descriptions.
            - Adjust the context size for image processing.
        - **Process the PDF**: Click the "Process PDF" button. The app will convert the PDF into a format that can be easily queried.
        - **Interact with the Document**: Once processing is complete, you can ask questions about the document in the chat window.

        ### Why Image Processing? 🤔
        Image processing enhances the understanding of the document by allowing the AI to analyze visual elements such as diagrams, charts, and images. 
        This is crucial for providing accurate descriptions and context, enabling the AI to give more informed responses based on the visual content present in the document.

        **Get started now and unlock the potential of your PDF documents!** 🚀
        """)

    # Render sidebar and capture selected models
    api_key, user_prompt, process_images, process_button, context_size, use_descriptions, reload_chat, chat_model, image_model = render_sidebar()

    # Main area for file upload, PDF viewer, and chat
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

    # Check if a new file has been uploaded
    if 'current_file' not in st.session_state or st.session_state['current_file'] != uploaded_file:
        if uploaded_file:
            st.session_state['current_file'] = uploaded_file
            st.session_state['file_processed'] = False
            if 'chat_history' in st.session_state:
                del st.session_state['chat_history']

    # Handle reload_chat separately
    if reload_chat:
        if 'chat_history' in st.session_state:
            del st.session_state['chat_history']
        st.rerun()

    if uploaded_file is not None:
        # Create two columns for the chat and PDF viewer
        col1, col2 = st.columns([0.5, 0.5])

        with col1:
            # Process the PDF when the sidebar button is clicked
            if process_button:
                st.session_state.processing_status = 'processing'
                st.rerun()

            if st.session_state.processing_status == 'processing':
                # Save the uploaded file with its original name
                save_path = os.path.join("uploads", uploaded_file.name)
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                with open(save_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                try:
                    markdown_text, output_md_path, output_md_with_descriptions_path, image_count = process_pdf(
                        save_path, api_key, user_prompt, process_images, context_size
                    )
                    # Read the content of the file with or without descriptions based on the toggle
                    if use_descriptions:
                        with open(output_md_with_descriptions_path, 'r', encoding='utf-8') as f:
                            markdown_text_to_use = f.read()
                    else:
                        with open(output_md_path, 'r', encoding='utf-8') as f:
                            markdown_text_to_use = f.read()
                    st.session_state['markdown_text'] = markdown_text_to_use
                    st.session_state['output_folder'] = os.path.dirname(output_md_path)
                    st.session_state['conversion_status'] = {
                        'success': True,
                        'output_md_path': output_md_path,
                        'output_md_with_descriptions_path': output_md_with_descriptions_path,
                        'image_count': image_count
                    }
                    st.session_state['file_processed'] = True
                    st.session_state.processing_status = 'completed'
                except Exception as e:
                    st.session_state['markdown_text'] = "Error occurred while processing the PDF."
                    st.session_state['conversion_status'] = {
                        'success': False,
                        'error': str(e)
                    }
                    st.session_state.processing_status = 'error'
                finally:
                    # Remove the temporary file
                    os.remove(save_path)
                
                # Force a rerun to update the sidebar
                st.rerun()

            if st.session_state.get('file_processed', False):
                # Use the appropriate markdown text based on the use_descriptions toggle
                markdown_text = st.session_state.get('markdown_text', '')

                # Render chat window with the selected chat model
                render_chat_window(api_key, markdown_text, chat_model)  # Pass chat_model here
            else:
                st.info("Please process the PDF using the button in the sidebar before starting the chat.")

        with col2:
            # Render PDF viewer
            render_pdf_viewer(uploaded_file)

    else:
        st.info("Please upload a PDF file to begin.")

    # Clear the 'completed' status after a short delay
    if st.session_state.processing_status == 'completed':
        time.sleep(3)
        st.session_state.processing_status = 'idle'
        st.rerun()

if __name__ == "__main__":
    main()