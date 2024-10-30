import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ExifTags
import os
from datetime import datetime

# Function to load image and log metadata
def load_and_log_image():
    # Open file dialog to select an image
    file_path = filedialog.askopenfilename(
        title="Select an Image",
        filetypes=[("Image Files", "*.jpg *.jpeg *.png *.bmp *.gif")]
    )

    if file_path:
        try:
            # Get Unix metadata
            created_time = os.path.getctime(file_path)
            modified_time = os.path.getmtime(file_path)
            accessed_time = os.path.getatime(file_path)
            
            # Format metadata info
            metadata_text = f"File Path: {file_path}\n"
            metadata_text += f"Created: {datetime.fromtimestamp(created_time)}\n"
            metadata_text += f"Modified: {datetime.fromtimestamp(modified_time)}\n"
            metadata_text += f"Accessed: {datetime.fromtimestamp(accessed_time)}\n"

            # Load image and get EXIF data
            img = Image.open(file_path)
            exif_data = img._getexif()  # Retrieve EXIF data

            metadata_text += "\nEXIF Data:\n"
            if exif_data:
                for tag, value in exif_data.items():
                    tag_name = ExifTags.TAGS.get(tag, tag)
                    metadata_text += f"{tag_name}: {value}\n"
            else:
                metadata_text += "No EXIF data available.\n"

            # Display metadata in the GUI
            metadata_label.config(text=metadata_text)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image metadata: {e}")

# Set up GUI
root = tk.Tk()
root.title("Image Metadata Logger")

# Button to upload an image
upload_button = tk.Button(root, text="Upload Image", command=load_and_log_image)
upload_button.pack(pady=10)

# Label to display the metadata
metadata_label = tk.Label(root, text="Image metadata will be displayed here.", justify="left")
metadata_label.pack(pady=10)

# Set window dimensions
root.geometry("1000x750")
root.mainloop()
