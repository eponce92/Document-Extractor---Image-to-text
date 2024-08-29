import os
import io
import base64
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image
import markdown
from openai import OpenAI

# Import all PDF libraries (you'll need to install these)
from pypdf import PdfReader
import fitz  # PyMuPDF
import pdfplumber

class PDFConverter:
    def __init__(self, master):
        self.master = master
        master.title("PDF to Markdown Converter")

        self.label = tk.Label(master, text="Select a PDF file to convert:")
        self.label.pack()

        self.select_button = tk.Button(master, text="Select PDF", command=self.select_pdf)
        self.select_button.pack()

        self.library_label = tk.Label(master, text="Select PDF processing library:")
        self.library_label.pack()

        self.library_var = tk.StringVar(value="pypdf")
        self.library_menu = ttk.Combobox(master, textvariable=self.library_var)
        self.library_menu['values'] = ('pypdf', 'pymupdf', 'pdfplumber')
        self.library_menu.pack()

        self.convert_button = tk.Button(master, text="Convert", command=self.convert_pdf, state=tk.DISABLED)
        self.convert_button.pack()

        self.status_label = tk.Label(master, text="")
        self.status_label.pack()

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
        text_content, images = self.extract_text_and_images(self.pdf_path)
        self.convert_to_markdown(text_content, images, output_folder)

        messagebox.showinfo("Success", f"Conversion complete. Output saved in {output_folder}")

    def create_output_folder(self):
        base_name = os.path.splitext(os.path.basename(self.pdf_path))[0]
        output_folder = os.path.join(os.getcwd(), base_name)
        os.makedirs(output_folder, exist_ok=True)
        os.makedirs(os.path.join(output_folder, "images"), exist_ok=True)
        return output_folder

    def extract_text_and_images(self, pdf_path):
        library = self.library_var.get()
        if library == 'pypdf':
            return self.extract_with_pypdf(pdf_path)
        elif library == 'pymupdf':
            return self.extract_with_pymupdf(pdf_path)
        elif library == 'pdfplumber':
            return self.extract_with_pdfplumber(pdf_path)

    def extract_with_pypdf(self, pdf_path):
        reader = PdfReader(pdf_path)
        text_content = []
        images = []
        
        for page in reader.pages:
            text = page.extract_text()
            text_content.append(text)
            
            for image in page.images:
                image_object = Image.open(io.BytesIO(image.data))
                images.append({
                    "image": image_object,
                    "before_text": text_content[-1],
                    "after_text": ""
                })
        
        # Update the after_text for each image
        for i in range(len(images) - 1):
            images[i]["after_text"] = text_content[i + 1]
        
        return text_content, images

    def extract_with_pymupdf(self, pdf_path):
        doc = fitz.open(pdf_path)
        text_content = []
        images = []

        for page in doc:
            text = page.get_text()
            text_content.append(text)

            for img in page.get_images():
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_object = Image.open(io.BytesIO(image_bytes))
                images.append({
                    "image": image_object,
                    "before_text": text_content[-1],
                    "after_text": ""
                })

        # Update the after_text for each image
        for i in range(len(images) - 1):
            images[i]["after_text"] = text_content[i + 1]

        return text_content, images

    def extract_with_pdfplumber(self, pdf_path):
        with pdfplumber.open(pdf_path) as pdf:
            text_content = []
            images = []

            for page in pdf.pages:
                text = page.extract_text()
                text_content.append(text)

                for image in page.images:
                    image_object = Image.open(io.BytesIO(image['stream'].get_data()))
                    images.append({
                        "image": image_object,
                        "before_text": text_content[-1],
                        "after_text": ""
                    })

            # Update the after_text for each image
            for i in range(len(images) - 1):
                images[i]["after_text"] = text_content[i + 1]

            return text_content, images

    def describe_image(self, image):
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        try:
            response = self.client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Describe this image in detail."},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{img_str}"
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
            return "Error in image description"

    def convert_to_markdown(self, text_content, images, output_folder):
        markdown_content = []
        
        for i, text in enumerate(text_content):
            markdown_content.append(text)
            
            if i < len(images):
                image = images[i]
                image_path = os.path.join(output_folder, "images", f"image_{i}.png")
                image["image"].save(image_path)
                
                image_description = self.describe_image(image["image"])
                markdown_content.append(f"\n\n![Image {i}]({image_path})\n\n{image_description}\n\n")
        
        markdown_text = "\n".join(markdown_content)
        
        with open(os.path.join(output_folder, "output.md"), "w", encoding="utf-8") as f:
            f.write(markdown_text)

root = tk.Tk()
converter = PDFConverter(root)
root.mainloop()