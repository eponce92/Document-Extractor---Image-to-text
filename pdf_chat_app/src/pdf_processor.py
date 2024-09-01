import os
import logging
import pymupdf4llm
import fitz  # PyMuPDF
import shutil
from pdf_chat_app.src.converter import PDFConverter
from pdf_chat_app.config.config import CONTEXT_SIZE_WORDS

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def process_pdf(pdf_path, api_key, user_prompt, process_images=True, context_size=CONTEXT_SIZE_WORDS):
    logging.info(f"Starting conversion of PDF: {pdf_path}")
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    script_dir = os.path.dirname(os.path.abspath(__file__))
    pdf_output_folder = os.path.join(script_dir, "..", "pdf_output")
    output_folder = os.path.join(pdf_output_folder, base_name)
    os.makedirs(output_folder, exist_ok=True)
    output_md_path = os.path.join(output_folder, f"{base_name}.md")
    
    try:
        logging.info("Converting PDF to Markdown")
        markdown_text = pymupdf4llm.to_markdown(pdf_path, write_images=True)
        
        logging.info("Moving generated images")
        for file in os.listdir():
            if file.endswith(".png") and file.startswith(base_name):
                src_path = os.path.join(os.getcwd(), file)
                dst_path = os.path.join(output_folder, file)
                shutil.move(src_path, dst_path)
                logging.info(f"Moved image: {src_path} -> {dst_path}")
        
        with open(output_md_path, "w", encoding="utf-8") as f:
            f.write(markdown_text)
        
        logging.info(f"Initial Markdown file saved to: {output_md_path}")
        
    except Exception as e:
        logging.error(f"Error during PDF to Markdown conversion: {e}")
        raise

    image_count = 0
    if process_images:
        logging.info("Processing images")
        converter = PDFConverter(api_key)
        lines = markdown_text.split('\n')
        new_lines = []
        context_before = []

        for line in lines:
            new_lines.append(line)
            if line.strip().startswith('![]'):
                image_filename = line.strip()[4:-1]
                image_path = os.path.join(output_folder, image_filename)
                
                if os.path.exists(image_path):
                    logging.info(f"Processing image: {image_path}")
                    context_before_text = '\n'.join(context_before[-context_size:])
                    context_after_index = lines.index(line) + 1
                    context_after_text = '\n'.join(lines[context_after_index:context_after_index+context_size])
                    
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
                else:
                    logging.warning(f"Image file not found: {image_path}")
            
            context_before.append(line)
            if len(context_before) > context_size * 2:
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