import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import imagehash
import random
import numpy as np
from skimage.metrics import structural_similarity as ssim
from PIL import ImageOps
import cv2  # OpenCV for ORB feature detection

# Global variables to store the hash of the original image
original_hash = None
orb = cv2.ORB_create()  # Initialize ORB detector

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

# Calculate SSIM between two images
def calculate_ssim(image1, image2):
    # Resize image2 to match image1's dimensions for SSIM calculation
    image2 = ImageOps.fit(image2, image1.size)  # Ensures the same dimensions
    image1 = np.array(image1.convert('L'))  # Convert to grayscale
    image2 = np.array(image2.convert('L'))  # Convert to grayscale
    similarity, _ = ssim(image1, image2, full=True)
    return similarity

# ORB feature matching
def orb_feature_matching(image1, image2):
    # Convert images to grayscale for ORB
    image1_cv = cv2.cvtColor(np.array(image1), cv2.COLOR_RGB2GRAY)
    image2_cv = cv2.cvtColor(np.array(image2), cv2.COLOR_RGB2GRAY)
    
    # Detect keypoints and descriptors
    kp1, des1 = orb.detectAndCompute(image1_cv, None)
    kp2, des2 = orb.detectAndCompute(image2_cv, None)
    
    # Match descriptors using the BFMatcher
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = bf.match(des1, des2)
    
    # Sort matches based on distance (best matches first)
    matches = sorted(matches, key=lambda x: x.distance)
    
    # Calculate matching percentage based on number of good matches
    matching_score = len(matches) / min(len(kp1), len(kp2)) * 100
    return matching_score

# Apply 5 random crops and 5 random rotations
def apply_transformations(img, hash_type):
    # Store results
    transformed_images = []
    similarity_results = []

    # Original image dimensions
    width, height = img.size

    # Apply 5 random crops
    for _ in range(5):
        left = random.randint(0, width // 4)
        top = random.randint(0, height // 4)
        right = random.randint(3 * width // 4, width)
        bottom = random.randint(3 * height // 4, height)
        cropped_img = img.crop((left, top, right, bottom))
        transformed_images.append(cropped_img)

    # Apply 5 random rotations
    for _ in range(5):
        angle = random.randint(0, 360)
        rotated_img = img.rotate(angle)
        transformed_images.append(rotated_img)

    # Calculate hashes, SSIM, and ORB similarity
    for transformed_img in transformed_images:
        transformed_hash = generate_hash(transformed_img, hash_type)
        hamming_distance = original_hash - transformed_hash
        total_bits = len(bin(int(str(original_hash), 16))) - 2
        hash_similarity_percentage = (1 - hamming_distance / total_bits) * 100

        # Calculate SSIM
        ssim_similarity = calculate_ssim(img, transformed_img)
        
        # Calculate ORB feature matching score
        orb_similarity = orb_feature_matching(img, transformed_img)
        
        similarity_results.append((transformed_img, transformed_hash, hash_similarity_percentage, ssim_similarity, orb_similarity))

    return similarity_results

# Display the transformations, hashes, SSIM, and ORB similarity
def display_transformations(original_img, similarity_results, container):
    # Display the original image
    original_img = original_img.resize((300, 300))
    img_tk = ImageTk.PhotoImage(original_img)
    label = tk.Label(container, image=img_tk)
    label.image = img_tk  # Keep a reference to avoid garbage collection
    label.grid(row=1, column=0, columnspan=2, pady=10)
    
    original_hash_label = tk.Label(container, text=f"Original Hash: {original_hash}")
    original_hash_label.grid(row=2, column=0, columnspan=2)

    # Display the transformed images, hashes, SSIM, and ORB similarity
    for i, (img, img_hash, hash_similarity, ssim_similarity, orb_similarity) in enumerate(similarity_results):
        img = img.resize((200, 200))  # Larger size for better visibility
        img_tk = ImageTk.PhotoImage(img)

        # Display the image
        label = tk.Label(container, image=img_tk)
        label.image = img_tk  # Keep a reference to avoid garbage collection
        label.grid(row=(i // 2) + 3, column=(i % 2) * 2)

        # Display the hash, hash similarity, SSIM, and ORB similarity
        hash_label = tk.Label(container, text=f"Hash: {img_hash}\nHash Sim: {hash_similarity:.2f}%\nSSIM: {ssim_similarity:.2f}\nORB Sim: {orb_similarity:.2f}%")
        hash_label.grid(row=(i // 2) + 3, column=(i % 2) * 2 + 1)

# Load and transform the selected image
def load_and_transform_image(hash_type='phash'):
    global original_hash

    # Open a file dialog to select an image
    file_path = filedialog.askopenfilename(
        title="Select an image",
        filetypes=[("Image Files", "*.jpg *.png *.jpeg")]
    )

    if file_path:
        try:
            # Load the image
            img = Image.open(file_path)

            # Generate the original image hash
            original_hash = generate_hash(img, hash_type)

            # Apply transformations and calculate similarity
            similarity_results = apply_transformations(img, hash_type)

            # Clear the container before displaying new images
            for widget in canvas_frame.winfo_children():
                widget.destroy()

            # Display the original image, transformations, hashes, SSIM, and ORB
            display_transformations(img, similarity_results, canvas_frame)

            # Update scroll region
            canvas_frame.update_idletasks()
            canvas.config(scrollregion=canvas.bbox("all"))

        except Exception as e:
            messagebox.showerror("Error", f"Error loading image: {e}")
    else:
        messagebox.showinfo("Info", "No file selected.")

# Set up the GUI
root = tk.Tk()
root.title("Image Transformations, Hash, SSIM, and ORB Similarity")

# Create a canvas for scrolling
canvas = tk.Canvas(root)
canvas.pack(side="left", fill="both", expand=True)

# Add a scrollbar
scrollbar = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
scrollbar.pack(side="right", fill="y")

canvas.configure(yscrollcommand=scrollbar.set)

# Create a frame inside the canvas
canvas_frame = tk.Frame(canvas)
canvas.create_window((0, 0), window=canvas_frame, anchor="nw")

# Button to select an image and apply transformations
select_image_button = tk.Button(canvas_frame, text="Select and Transform Image", command=lambda: load_and_transform_image('phash'))
select_image_button.grid(row=0, column=0, pady=10)

# Update the canvas scrollable area dynamically
canvas_frame.update_idletasks()
canvas.config(scrollregion=canvas.bbox("all"))

root.geometry("1000x1500")
root.mainloop()
