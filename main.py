import os
import pymupdf4llm
import tkinter as tk
from tkinter import filedialog, messagebox
import shutil

def convert_pdf_to_markdown(pdf_path):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    output_folder = os.path.join(script_dir, f"{base_name}_output")
    os.makedirs(output_folder, exist_ok=True)
    output_md_path = os.path.join(output_folder, f"{base_name}.md")
    
    # Use pymupdf4llm for conversion, including image extraction
    markdown_text = pymupdf4llm.to_markdown(pdf_path, write_images=True)
    
    # Move generated images to the output folder
    for file in os.listdir(script_dir):
        if file.startswith("image_") and file.endswith(".png"):
            shutil.move(os.path.join(script_dir, file), os.path.join(output_folder, file))
    
    # Write the Markdown content to a file
    with open(output_md_path, "w", encoding="utf-8") as f:
        f.write(markdown_text)
    
    # Count the number of images
    image_count = len([f for f in os.listdir(output_folder) if f.startswith("image_") and f.endswith(".png")])
    
    print(f"Markdown file saved to: {output_md_path}")
    print(f"Markdown length: {len(markdown_text)}")
    print(f"Total images extracted: {image_count}")
    
    return markdown_text, output_md_path, image_count

def select_pdf_and_convert():
    pdf_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
    if pdf_path:
        try:
            markdown_text, output_path, image_count = convert_pdf_to_markdown(pdf_path)
            messagebox.showinfo("Conversion Complete", 
                                f"PDF converted to Markdown.\n"
                                f"Saved in: {os.path.dirname(output_path)}\n"
                                f"Images extracted: {image_count}")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during conversion:\n{str(e)}")

# GUI setup
root = tk.Tk()
root.title("PDF to Markdown Converter")

# Set window size and position
window_width = 300
window_height = 100
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
center_x = int(screen_width/2 - window_width/2)
center_y = int(screen_height/2 - window_height/2)
root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')

# Add a label
label = tk.Label(root, text="Click the button to select a PDF and convert it to Markdown")
label.pack(pady=10)

# Add the conversion button
select_button = tk.Button(root, text="Select PDF and Convert", command=select_pdf_and_convert)
select_button.pack(pady=10)

# Start the GUI event loop
root.mainloop()
