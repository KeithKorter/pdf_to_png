import fitz  # PyMuPDF
from PIL import Image
import os
import time
import tkinter as tk
from threading import Thread
import itertools

def convert_pdf_to_transparent_images(pdf_path, output_folder, zoom_factor):
    # Open the PDF
    pdf_document = fitz.open(pdf_path)
    
    for page_number in range(len(pdf_document)):
        page = pdf_document.load_page(page_number)
        
        # Set the zoom factor
        zoom_matrix = fitz.Matrix(zoom_factor, zoom_factor)
        pix = page.get_pixmap(matrix=zoom_matrix)
        
        # Convert to a PIL Image
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        # Convert white background to transparent
        img = img.convert("RGBA")
        datas = img.getdata()
        
        new_data = []
        for item in datas:
            # Change all white (also shades of whites)
            # to transparent
            if item[0] > 200 and item[1] > 200 and item[2] > 200:
                new_data.append((255, 255, 255, 0))
            else:
                new_data.append(item)
        
        img.putdata(new_data)
        
        # Save the image
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        output_path = os.path.join(output_folder, f"{base_name}_page_{page_number + 1}.png")
        img.save(output_path, "PNG")

def process_folder(input_folder, zoom_factor):
    output_folder = os.path.join(input_folder, 'processed')
    
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    for filename in os.listdir(input_folder):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(input_folder, filename)
            convert_pdf_to_transparent_images(pdf_path, output_folder, zoom_factor)

def run_processing(input_folder, zoom_factor, status_label, process_button, root):
    status_label.config(text="Processing Images...")
    process_folder(input_folder, zoom_factor)
    status_label.config(text="Processing complete. You may now close the application.")
    process_button.config(state=tk.DISABLED)

def start_processing(input_folder, zoom_factor, status_label, process_button, root):
    status_label.config(text="Processing Images...")
    process_button.config(state=tk.DISABLED)
    Thread(target=run_processing, args=(input_folder, zoom_factor, status_label, process_button, root)).start()
    animate_processing(status_label, root)

def animate_processing(status_label, root):
    def update_animation():
        for c in itertools.cycle(['|', '/', '-', '\\']):
            if 'complete' in status_label.cget("text"):
                break
            status_label.config(text=f"Processing Images {c}")
            root.update_idletasks()
            time.sleep(0.1)
    Thread(target=update_animation).start()

def create_gui():
    root = tk.Tk()
    root.title("PDF to Transparent PNG Converter")
    
    frame = tk.Frame(root, padx=20, pady=20)
    frame.pack()

    input_label = tk.Label(frame, text="Enter the path to the folder containing the PDF files:")
    input_label.pack()

    input_entry = tk.Entry(frame, width=50)
    input_entry.pack()

    status_label = tk.Label(frame, text="", fg="green")
    status_label.pack(pady=10)
    
    process_button = tk.Button(frame, text="Start Processing", command=lambda: start_processing(input_entry.get(), 5.0, status_label, process_button, root))
    process_button.pack()

    def close_app(event):
        if 'complete' in status_label.cget("text"):
            root.quit()
    
    root.bind("<KeyPress>", close_app)
    root.mainloop()

if __name__ == "__main__":
    create_gui()
