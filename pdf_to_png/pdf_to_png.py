import fitz  # PyMuPDF
from PIL import Image
import cv2
import numpy as np
import os
import tkinter as tk
from threading import Thread
import itertools
import time

def crop_to_content_opencv(img_path, border=10):
    # Load image using OpenCV
    image = cv2.imread(img_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    
    # Find contours
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Get the bounding box of the largest contour
    max_contour = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(max_contour)
    
    # Add border
    x = max(0, x - border)
    y = max(0, y - border)
    w = min(image.shape[1], x + w + 2 * border) - x
    h = min(image.shape[0], y + h + 2 * border) - y
    
    # Crop the image
    cropped_image = image[y:y+h, x:x+w]
    
    # Convert back to PIL image
    cropped_pil_image = Image.fromarray(cv2.cvtColor(cropped_image, cv2.COLOR_BGR2RGBA))
    
    return cropped_pil_image

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
        
        # Save image to a temporary path
        temp_path = "temp_image.png"
        img.save(temp_path)
        
        # Crop the image to the main content using OpenCV
        cropped_img = crop_to_content_opencv(temp_path)
        
        # Convert white background to transparent
        cropped_img = cropped_img.convert("RGBA")
        datas = cropped_img.getdata()
        
        new_data = []
        for item in datas:
            # Change all white (also shades of whites) to transparent
            if item[0] > 200 and item[1] > 200 and item[2] > 200:
                new_data.append((255, 255, 255, 0))
            else:
                new_data.append(item)
        
        cropped_img.putdata(new_data)
        
        # Save the image
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        output_path = os.path.join(output_folder, f"{base_name}_page_{page_number + 1}.png")
        cropped_img.save(output_path, "PNG")

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
    status_label.config(text="Processing complete. Press any key to close the application.")
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
