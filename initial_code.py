# This file contains the initial implementation of the PDF Chat App.
# It is kept for reference purposes and is not used in the current version of the application.

import os
import base64
import pymupdf4llm
import streamlit as st
import shutil
from openai import OpenAI
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants
CONTEXT_SIZE_WORDS = 100  # Number of words for context before and after the image

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
models = client.models.list()
model_options = [model.id for model in models.data]

class PDFConverter:
    def __init__(self, api_key, model="gpt-4o-mini"):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def describe_image_and_context(self, image_path, context_before, context_after, user_prompt):
        with open(image_path, "rb") as image_file:
            img_str = base64.b64encode(image_file.read()).decode()

        prompt = f"""
        You are an AI assistant helping to convert documents with images into accessible text formats. 
        Your task is to describe an image in detail, considering its context within the document.

        Document Context:
        1. Text before the image:
        {context_before}

        2. Text after the image:
        {context_after}

        User-provided context and preferences:
        {user_prompt}

        Instructions:
        1. Analyze the image carefully, considering all visual elements.
        2. Provide a detailed description of the image that would be meaningful to someone who cannot see it.
        3. Relate the image content to the surrounding text context where relevant.
        4. Consider the user-provided context and preferences when describing the image.
        5. Structure your description as follows:
        a. Brief overview 
        b. Detailed description 
        c. Relevance to document context 
        6. Use clear, concise language and avoid making assumptions about information not present in the image or context.
        7. If the image contains text, include it verbatim in your description.
        8. For diagrams, charts, or graphs, explain their type and the information they convey, including any relevant numbers or key data points.
        9. Describe colors, shapes, spatial relationships, and any other visually significant elements.

        Your description should enable a person who cannot see the image to understand its content and significance within the document.
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{img_str}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            logging.error(f"Error in image description: {e}")
            return f"Error in image description: {str(e)}"

def convert_pdf_to_markdown(pdf_path, api_key, user_prompt, process_images=True):
    logging.info(f"Starting conversion of PDF: {pdf_path}")
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_folder = os.path.join(script_dir, f"{base_name}_output")
    os.makedirs(output_folder, exist_ok=True)
    output_md_path = os.path.join(output_folder, f"{base_name}.md")
    
    try:
        markdown_text = pymupdf4llm.to_markdown(pdf_path, write_images=True)
        
        if process_images:
            for file in os.listdir():
                if file.endswith(".png"):
                    shutil.move(file, os.path.join(output_folder, file))
        
        with open(output_md_path, "w", encoding="utf-8") as f:
            f.write(markdown_text)
        
        logging.info(f"Initial Markdown file saved to: {output_md_path}")
        
    except Exception as e:
        logging.error(f"Error during PDF to Markdown conversion: {e}")
        raise

    if process_images:
        converter = PDFConverter(api_key)
        lines = markdown_text.split('\n')
        new_lines = []
        context_before = []
        image_count = 0

        for line in lines:
            new_lines.append(line)
            if line.strip().startswith('![]'):
                image_filename = line.strip()[4:-1]
                image_path = os.path.join(output_folder, image_filename)
                
                if not os.path.exists(image_path):
                    logging.warning(f"Image file not found: {image_path}")
                    continue
                
                context_before_text = '\n'.join(context_before[-CONTEXT_SIZE_WORDS:])
                context_after_index = lines.index(line) + 1
                context_after_text = '\n'.join(lines[context_after_index:context_after_index+CONTEXT_SIZE_WORDS])
                
                description = converter.describe_image_and_context(image_path, context_before_text, context_after_text, user_prompt)
                
                new_lines.extend(['', '**Image Description:**', description, ''])
                
                image_count += 1
                description_filename = f"image_description_{image_count}.txt"
                description_path = os.path.join(output_folder, description_filename)
                with open(description_path, "w", encoding="utf-8") as desc_file:
                    desc_file.write(f"Context before:\n{context_before_text}\n\n")
                    desc_file.write(f"Context after:\n{context_after_text}\n\n")
                    desc_file.write(f"Image Description:\n{description}\n")
                
                logging.info(f"Saved image description to: {description_path}")
            
            context_before.append(line)
            if len(context_before) > CONTEXT_SIZE_WORDS * 2:
                context_before.pop(0)
        
        markdown_text_with_descriptions = '\n'.join(new_lines)
        
        output_md_with_descriptions_path = os.path.join(output_folder, f"{base_name}_with_descriptions.md")
        with open(output_md_with_descriptions_path, "w", encoding="utf-8") as f:
            f.write(markdown_text_with_descriptions)
        
        logging.info(f"Markdown file with descriptions saved to: {output_md_with_descriptions_path}")
        logging.info(f"Total images processed: {image_count}") 
        
        return markdown_text, output_md_path, output_md_with_descriptions_path, image_count
    else:
        logging.info("Image processing skipped.")
        return markdown_text, output_md_path, None, 0

def main():
    st.title("PDF to Markdown Converter")

    # Sidebar for settings
    st.sidebar.header("Settings")
    api_key = st.sidebar.text_input("Enter your OpenAI API key", type="password")
    user_prompt = st.sidebar.text_area("Enter additional context for image descriptions", max_chars=500)
    model = st.sidebar.selectbox("Select Model", model_options, index=model_options.index("gpt-4o-mini"))
    process_images = st.sidebar.checkbox("Process Images", value=True)

    # Main area for file upload and conversion
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

    if uploaded_file is not None:
        if st.button("Convert PDF"):
            if process_images and not api_key:
                st.error("Please enter your OpenAI API key to process images.")
            else:
                try:
                    with st.spinner("Converting PDF..."):
                        # Save the uploaded file temporarily
                        with open("temp.pdf", "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        
                        markdown_text, output_path, output_with_descriptions_path, image_count = convert_pdf_to_markdown("temp.pdf", api_key, user_prompt, process_images)
                        
                        if not markdown_text:
                            raise ValueError("No content was generated during conversion.")

                        st.success("Conversion complete!")
                        st.markdown(f"Initial Markdown saved in: {output_path}")
                        if output_with_descriptions_path:
                            st.markdown(f"Markdown with descriptions saved in: {output_with_descriptions_path}")
                        st.markdown(f"Images processed: {image_count}")

                        # Display the converted Markdown inside a popover
                        with st.popover("View Converted Markdown"):
                            st.markdown("### Converted Markdown:")
                            st.markdown(markdown_text)

                        # Offer download options
                        st.download_button(
                            label="Download Markdown File",
                            data=markdown_text,
                            file_name="converted_markdown.md",
                            mime="text/markdown"
                        )

                except Exception as e:
                    st.error(f"An error occurred during conversion: {str(e)}")

                finally:
                    # Clean up the temporary file
                    if os.path.exists("temp.pdf"):
                        os.remove("temp.pdf")

if __name__ == "__main__":
    main()