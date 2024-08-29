import os
import io
import base64
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image
from openai import OpenAI
import fitz  # PyMuPDF
import pdfplumber

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
        content = self.extract_content(self.pdf_path)
        self.convert_to_markdown(content, output_folder)

        messagebox.showinfo("Success", f"Conversion complete. Output saved in {output_folder}")

    def create_output_folder(self):
        base_name = os.path.splitext(os.path.basename(self.pdf_path))[0]
        output_folder = os.path.join(os.getcwd(), base_name)
        os.makedirs(output_folder, exist_ok=True)
        os.makedirs(os.path.join(output_folder, "images"), exist_ok=True)
        return output_folder

    def extract_content(self, pdf_path):
        content = []
        
        # Use PyMuPDF for image extraction
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc[page_num]
            content.append({"type": "text", "content": page.get_text()})
            
            for img in page.get_images():
                try:
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    image = Image.open(io.BytesIO(image_bytes))
                    content.append({
                        "type": "image",
                        "content": image,
                        "page": page_num
                    })
                except Exception as e:
                    print(f"Error extracting image: {e}")
        
        # Use pdfplumber for table extraction
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                tables = page.extract_tables()
                for table in tables:
                    content.append({"type": "table", "content": table, "page": page_num})
        
        # Sort content by page number
        content.sort(key=lambda x: x.get("page", 0))
        
        return content

    def table_to_markdown(self, table):
        markdown_table = []
        for i, row in enumerate(table):
            markdown_row = "| " + " | ".join(str(cell) if cell is not None else "" for cell in row) + " |"
            markdown_table.append(markdown_row)
            if i == 0:
                markdown_table.append("| " + " | ".join(["---"] * len(row)) + " |")
        return "\n".join(markdown_table)

    def get_context(self, content, current_index, word_limit=200):
        context_before = ""
        context_after = ""
        words_before = 0
        words_after = 0

        # Get context before the image
        for i in range(current_index - 1, -1, -1):
            if content[i]["type"] == "text":
                words = content[i]["content"].split()
                if words_before + len(words) > word_limit:
                    context_before = " ".join(words[-(word_limit-words_before):]) + " " + context_before
                    break
                context_before = content[i]["content"] + " " + context_before
                words_before += len(words)
            if words_before >= word_limit:
                break

        # Get context after the image
        for i in range(current_index + 1, len(content)):
            if content[i]["type"] == "text":
                words = content[i]["content"].split()
                if words_after + len(words) > word_limit:
                    context_after += " " + " ".join(words[:word_limit-words_after])
                    break
                context_after += " " + content[i]["content"]
                words_after += len(words)
            if words_after >= word_limit:
                break

        return context_before.strip(), context_after.strip()

    def describe_image_and_context(self, image, context_before, context_after):
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

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

    def convert_to_markdown(self, content, output_folder):
        markdown_content = []
        image_counter = 0
        
        for index, item in enumerate(content):
            if item["type"] == "text":
                markdown_content.append(item["content"])
            elif item["type"] == "table":
                markdown_table = self.table_to_markdown(item["content"])
                markdown_content.append("\n" + markdown_table + "\n")
            elif item["type"] == "image":
                image = item["content"]
                image_path = os.path.join(output_folder, "images", f"image_{image_counter}.png")
                image.save(image_path)
                
                context_before, context_after = self.get_context(content, index)
                
                image_description = self.describe_image_and_context(image, context_before, context_after)
                
                description_path = os.path.join(output_folder, "images", f"image_{image_counter}_description.txt")
                with open(description_path, "w", encoding="utf-8") as f:
                    f.write(image_description)
                
                markdown_content.append(f"\n\n![Image {image_counter}](images/image_{image_counter}.png)\n\n")
                markdown_content.append("---\n")
                markdown_content.append(f"### Image #{image_counter} Description\n\n{image_description}\n")
                markdown_content.append("---\n\n")
                image_counter += 1
        
        markdown_text = "\n".join(markdown_content)
        
        with open(os.path.join(output_folder, "output.md"), "w", encoding="utf-8") as f:
            f.write(markdown_text)

def main():
    root = tk.Tk()
    converter = PDFConverter(root)
    root.mainloop()

if __name__ == "__main__":
    main()