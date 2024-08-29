import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.ttk import Progressbar
import os
import threading
import pymupdf4llm

def convert_pdf_to_markdown(pdf_path, md_path, progress_callback):
    try:
        # Convert PDF to Markdown using PyMuPDF4LLM
        md_text = pymupdf4llm.to_markdown(pdf_path)
        
        # Write the Markdown content to a file
        with open(md_path, "w", encoding="utf-8") as md_file:
            md_file.write(md_text)
        
        progress_callback(100)  # Update progress to 100% after conversion
    except Exception as e:
        print(f"Error converting PDF to Markdown: {e}")
        raise

def select_pdf():
    file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
    if file_path:
        pdf_path_var.set(file_path)

def update_progress(value):
    progress['value'] = value
    root.update_idletasks()

def convert():
    pdf_path = pdf_path_var.get()
    
    if not pdf_path:
        print("Error: Please select a PDF file.")
        return
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_filename = os.path.splitext(os.path.basename(pdf_path))[0]
    md_path = os.path.join(script_dir, output_filename + ".md")
    
    progress.pack(pady=10)
    convert_button['state'] = 'disabled'
    
    def conversion_thread():
        try:
            convert_pdf_to_markdown(pdf_path, md_path, update_progress)
            print(f"Success: Conversion complete. Output saved to:\n{md_path}")
        except Exception as e:
            print(f"Error: An error occurred during conversion:\n{str(e)}")
        finally:
            root.after(0, lambda: progress.pack_forget())
            root.after(0, lambda: convert_button.config(state='normal'))
    
    threading.Thread(target=conversion_thread).start()

# Create main window
root = tk.Tk()
root.title("PDF to Markdown Converter")
root.geometry("400x200")

# Variables
pdf_path_var = tk.StringVar()

# PDF file selection
tk.Label(root, text="Select PDF:").pack(pady=5)
tk.Button(root, text="Browse", command=select_pdf).pack()
tk.Label(root, textvariable=pdf_path_var).pack()

# Progress bar
progress = Progressbar(root, orient=tk.HORIZONTAL, length=300, mode='determinate')

# Convert button
convert_button = tk.Button(root, text="Convert", command=convert)
convert_button.pack(pady=10)

root.mainloop()