import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image
import imagehash

# Global variables to store hashes of two images
hash1 = None
hash2 = None

# Function to generate different types of hashes
def generate_hash(image, hash_type='phash'):
    if hash_type == 'phash':
        return imagehash.phash(image)
    elif hash_type == 'ahash':
        return imagehash.average_hash(image)
    elif hash_type == 'dhash':
        return imagehash.dhash(image)
    elif hash_type == 'whash':
        return imagehash.whash(image)

# Load and hash the selected image based on hash type
def load_and_hash_image(image_number, hash_type='phash'):
    global hash1, hash2

    # Open a file dialog to select an image
    file_path = filedialog.askopenfilename(
        title="Select an image",
        filetypes=[("Image Files", "*.jpg *.png *.jpeg")]
    )

    if file_path:
        try:
            # Load the image
            img = Image.open(file_path)

            # Generate the selected hash type
            selected_hash = generate_hash(img, hash_type)

            # Store the hash in the appropriate variable
            if image_number == 1:
                hash1 = selected_hash
                hash_label1.config(text=f"Image 1 {hash_type.upper()}: {selected_hash}")
            elif image_number == 2:
                hash2 = selected_hash
                hash_label2.config(text=f"Image 2 {hash_type.upper()}: {selected_hash}")
        except Exception as e:
            messagebox.showerror("Error", f"Error loading image: {e}")
    else:
        messagebox.showinfo("Info", "No file selected.")

# Compare the two hashes and display similarity percentage
def compare_hashes():
    if hash1 is not None and hash2 is not None:
        # Calculate the Hamming distance (number of differing bits)
        hamming_distance = hash1 - hash2
        # Calculate similarity percentage
        total_bits = len(bin(int(str(hash1), 16))) - 2  # total number of bits in the hash
        similarity_percentage = (1 - hamming_distance / total_bits) * 100

        # Display the similarity percentage
        result_label.config(text=f"Similarity: {similarity_percentage:.2f}%")
    else:
        messagebox.showinfo("Info", "Please select both images before comparing.")

# Set up the GUI
root = tk.Tk()
root.title("Image Comparison using Multiple Hashing Methods")

# Hash type selection dropdown menu
hash_type_var = tk.StringVar(value="phash")  # Default value

# Function to update the selected hash type
def update_hash_type(value):
    hash_type_var.set(value)

# Dropdown to select hashing method
hash_type_label = tk.Label(root, text="Select Hashing Method:")
hash_type_label.pack(pady=5)

hash_type_dropdown = tk.OptionMenu(root, hash_type_var, "phash", "ahash", "dhash", "whash", command=update_hash_type)
hash_type_dropdown.pack(pady=10)

# Add buttons to select two images
select_image_button1 = tk.Button(root, text="Select Image 1", command=lambda: load_and_hash_image(1, hash_type_var.get()))
select_image_button1.pack(pady=10)

select_image_button2 = tk.Button(root, text="Select Image 2", command=lambda: load_and_hash_image(2, hash_type_var.get()))
select_image_button2.pack(pady=10)

# Labels to display the hashes of both images
hash_label1 = tk.Label(root, text="Image 1 hash will be displayed here.")
hash_label1.pack(pady=5)

hash_label2 = tk.Label(root, text="Image 2 hash will be displayed here.")
hash_label2.pack(pady=5)

# Button to compare the two images
compare_button = tk.Button(root, text="Compare Images", command=compare_hashes)
compare_button.pack(pady=20)

# Label to display the result of the comparison
result_label = tk.Label(root, text="Comparison result will be displayed here.")
result_label.pack(pady=10)

# Start the GUI event loop
root.geometry("400x400")
root.mainloop()
