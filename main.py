import os
import base64
import pymupdf4llm
import tkinter as tk
from tkinter import filedialog, messagebox
import shutil
from openai import OpenAI
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants
CONTEXT_SIZE_WORDS = 100  # Number of words for context before and after the image

class PDFConverter:
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key)

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
                model="gpt-4o-mini",
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

def convert_pdf_to_markdown(pdf_path, api_key, user_prompt):
    logging.info(f"Starting conversion of PDF: {pdf_path}")
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_folder = os.path.join(script_dir, f"{base_name}_output")
    os.makedirs(output_folder, exist_ok=True)
    output_md_path = os.path.join(output_folder, f"{base_name}.md")
    
    # Use pymupdf4llm for conversion, including image extraction
    try:
        markdown_text = pymupdf4llm.to_markdown(pdf_path, write_images=True)
        
        # Move images to the output folder
        for file in os.listdir():
            if file.endswith(".png"):
                shutil.move(file, os.path.join(output_folder, file))
        
    except Exception as e:
        logging.error(f"Error during PDF to Markdown conversion: {e}")
        raise

    # Process images and add descriptions
    converter = PDFConverter(api_key)
    words = markdown_text.split()
    new_words = []
    context_before = []
    image_count = 0

    for i, word in enumerate(words):
        new_words.append(word)
        if word.startswith('![]'):
            image_filename = word[4:-1]
            image_path = os.path.join(output_folder, image_filename)
            
            if not os.path.exists(image_path):
                logging.warning(f"Image file not found: {image_path}")
                continue
            
            # Get context after the image
            context_after = ' '.join(words[i+1:i+1+CONTEXT_SIZE_WORDS])
            
            # Get image description
            description = converter.describe_image_and_context(image_path, ' '.join(context_before), context_after, user_prompt)
            
            # Add description after the image tag in markdown
            new_words.extend(["\n\n**Image Description:**", description, "\n"])
            
            # Save image description to a separate text file
            image_count += 1
            description_filename = f"image_description_{image_count}.txt"
            description_path = os.path.join(output_folder, description_filename)
            with open(description_path, "w", encoding="utf-8") as desc_file:
                desc_file.write(f"Context before:\n{' '.join(context_before)}\n\n")
                desc_file.write(f"Context after:\n{context_after}\n\n")
                desc_file.write(f"Image Description:\n{description}\n")
            
            logging.info(f"Saved image description to: {description_path}")
        
        # Update context before
        context_before.append(word)
        if len(context_before) > CONTEXT_SIZE_WORDS:
            context_before.pop(0)
    
    # Join the words back into a single string
    markdown_text = ' '.join(new_words)
    
    # Write the Markdown content to a file
    with open(output_md_path, "w", encoding="utf-8") as f:
        f.write(markdown_text)
    
    logging.info(f"Markdown file saved to: {output_md_path}")
    logging.info(f"Markdown length: {len(markdown_text)}")
    logging.info(f"Total images processed: {image_count}") 
    
    return markdown_text, output_md_path, image_count

def select_pdf_and_convert(api_key_var, user_prompt_var):
    pdf_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
    if pdf_path:
        api_key = api_key_var.get()
        user_prompt = user_prompt_var.get()
        if not api_key:
            logging.error("OpenAI API key not provided")
            messagebox.showerror("Error", "Please enter your OpenAI API key.")
            return
        try:
            markdown_text, output_path, image_count = convert_pdf_to_markdown(pdf_path, api_key, user_prompt)
            logging.info(f"Conversion completed successfully. Output path: {output_path}, Images processed: {image_count}")
            messagebox.showinfo("Conversion Complete", 
                                f"PDF converted to Markdown.\n"
                                f"Saved in: {os.path.dirname(output_path)}\n"
                                f"Images processed: {image_count}")
        except Exception as e:
            logging.error(f"An error occurred during conversion: {e}")
            messagebox.showerror("Error", f"An error occurred during conversion:\n{str(e)}")

# GUI setup
root = tk.Tk()
root.title("PDF to Markdown Converter")

# Set window size and position
window_width = 500
window_height = 350
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
center_x = int(screen_width/2 - window_width/2)
center_y = int(screen_height/2 - window_height/2)
root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')

# Add a label and entry for API key
api_key_label = tk.Label(root, text="Enter your OpenAI API key:")
api_key_label.pack(pady=5)
api_key_var = tk.StringVar()
api_key_entry = tk.Entry(root, textvariable=api_key_var, width=40, show="*")
api_key_entry.pack(pady=5)

# Add a label and text area for user prompt
user_prompt_label = tk.Label(root, text="Enter additional context or preferences for image descriptions:")
user_prompt_label.pack(pady=5)
user_prompt_var = tk.StringVar()
user_prompt_entry = tk.Text(root, height=5, width=40)
user_prompt_entry.pack(pady=5)

# Add a label
label = tk.Label(root, text="Click the button to select a PDF and convert it to Markdown")
label.pack(pady=10)

# Add the conversion button
select_button = tk.Button(root, text="Select PDF and Convert", command=lambda: select_pdf_and_convert(api_key_var, user_prompt_var))
select_button.pack(pady=10)

# Start the GUI event loop
root.mainloop()
