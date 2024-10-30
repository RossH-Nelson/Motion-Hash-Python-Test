import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image
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
            # Get metadata
            image = Image.open(file_path)
            metadata = image.info  # Metadata from PIL

            # Get Unix timestamp for created, modified, accessed times
            created_time = os.path.getctime(file_path)
            modified_time = os.path.getmtime(file_path)
            accessed_time = os.path.getatime(file_path)

            # Format metadata info
            metadata_text = f"File Path: {file_path}\n"
            metadata_text += f"Created: {datetime.fromtimestamp(created_time)}\n"
            metadata_text += f"Modified: {datetime.fromtimestamp(modified_time)}\n"
            metadata_text += f"Accessed: {datetime.fromtimestamp(accessed_time)}\n"
            metadata_text += "\nImage Metadata:\n"
            for key, value in metadata.items():
                metadata_text += f"{key}: {value}\n"

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
root.geometry("750x500")
root.mainloop()
