"""
This script converts a PDF file to a Markdown file with image descriptions.
It uses PyMuPDF4LLM for PDF to Markdown conversion, PyMuPDF for image extraction, and OpenAI's GPT-4 for image description.
"""

import os
import io
import base64
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image
from openai import OpenAI
import pymupdf4llm
import pymupdf

class PDFConverter:
    def __init__(self, master):
        self.master = master
        master.title("PDF to Markdown Converter")
        master.geometry("400x200")

        self.label = tk.Label(master, text="Select a PDF file to convert:")
        self.label.pack(pady=10)

        self.select_button = tk.Button(master, text="Select PDF", command=self.select_pdf)
        self.select_button.pack(pady=5)

        self.convert_button = tk.Button(master, text="Convert", command=self.convert_pdf, state=tk.DISABLED)
        self.convert_button.pack(pady=5)

        self.status_label = tk.Label(master, text="")
        self.status_label.pack(pady=10)

        self.client = OpenAI()  # Initialize OpenAI client

    def select_pdf(self):
        self.pdf_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if self.pdf_path:
            self.convert_button['state'] = tk.NORMAL
            self.status_label['text'] = f"Selected: {os.path.basename(self.pdf_path)}"

    def convert_pdf(self):
        if not hasattr(self, 'pdf_path'):
            messagebox.showerror("Error", "Please select a PDF file first.")
            return

        output_folder = self.create_output_folder()
        self.convert_to_markdown(self.pdf_path, output_folder)

        messagebox.showinfo("Success", f"Conversion complete. Output saved in {output_folder}")

    def create_output_folder(self):
        base_name = os.path.splitext(os.path.basename(self.pdf_path))[0]
        output_folder = os.path.join(os.getcwd(), base_name)
        os.makedirs(output_folder, exist_ok=True)
        os.makedirs(os.path.join(output_folder, "images"), exist_ok=True)
        return output_folder

    def get_context(self, markdown_text, image_index, word_limit=200):
        lines = markdown_text.split('\n')
        image_line = next((i for i, line in enumerate(lines) if f"![Image {image_index}]" in line), -1)
        
        if image_line == -1:
            return "", ""
        
        context_before = ' '.join(lines[:image_line])
        context_after = ' '.join(lines[image_line+1:])
        
        words_before = context_before.split()[-word_limit:]
        words_after = context_after.split()[:word_limit]
        
        return ' '.join(words_before), ' '.join(words_after)

    def describe_image_and_context(self, image_path, context_before, context_after):
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

        Instructions:
        1. Analyze the image carefully, considering all visual elements.
        2. Provide a detailed description of the image that would be meaningful to someone who cannot see it.
        3. Relate the image content to the surrounding text context where relevant.
        4. Structure your description as follows:
        a. Brief overview 
        b. Detailed description 
        c. Relevance to document context 
        5. Use clear, concise language and avoid making assumptions about information not present in the image or context.
        6. If the image contains text, include it verbatim in your description.
        7. For diagrams, charts, or graphs, explain their type and the information they convey, including any relevant numbers or key data points.
        8. Describe colors, shapes, spatial relationships, and any other visually significant elements.

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
                max_tokens=300
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error in image description: {e}")
            return f"Error in image description: {str(e)}"

    def convert_to_markdown(self, pdf_path, output_folder):
        # Convert PDF to Markdown using PyMuPDF4LLM
        markdown_text = pymupdf4llm.to_markdown(pdf_path)
        
        # Extract images from the PDF
        doc = pymupdf.open(pdf_path)
        image_counter = 0
        extracted_xrefs = set()

        for page_num in range(len(doc)):
            page = doc[page_num]
            image_list = page.get_images(full=True)
            
            for img_index, img in enumerate(image_list):
                xref = img[0]
                if xref in extracted_xrefs:
                    continue  # Skip if we've already extracted this image
                
                extracted_xrefs.add(xref)
                
                try:
                    base_image = doc.extract_image(xref)
                    if base_image:
                        image_bytes = base_image["image"]
                        image_ext = base_image["ext"]
                        image_path = os.path.join(output_folder, "images", f"image_{image_counter}.{image_ext}")
                        
                        with open(image_path, "wb") as image_file:
                            image_file.write(image_bytes)
                        
                        context_before, context_after = self.get_context(markdown_text, image_counter)
                        
                        image_description = self.describe_image_and_context(image_path, context_before, context_after)
                        
                        description_path = os.path.join(output_folder, "images", f"image_{image_counter}_description.txt")
                        with open(description_path, "w", encoding="utf-8") as f:
                            f.write(image_description)
                        
                        # Insert image description into markdown_text
                        image_marker = f"![Image {image_counter}]"
                        image_description_md = f"\n\n---\n### Image #{image_counter} Description\n\n{image_description}\n---\n\n"
                        markdown_text = markdown_text.replace(image_marker, f"{image_marker}{image_description_md}")
                        
                        image_counter += 1
                except Exception as e:
                    print(f"Error processing image on page {page_num + 1}, image {img_index + 1}: {str(e)}")

        # Save the final Markdown file
        with open(os.path.join(output_folder, "output.md"), "w", encoding="utf-8") as f:
            f.write(markdown_text)

def main():
    root = tk.Tk()
    converter = PDFConverter(root)
    root.mainloop()

if __name__ == "__main__":
    main()