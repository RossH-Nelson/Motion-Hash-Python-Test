import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import imagehash
import random
import numpy as np
from skimage.metrics import structural_similarity as ssim
from PIL import ImageOps
import cv2  # OpenCV for ORB feature detection

# Global variables to store the hash and original image
original_hash = None
original_img = None
orb = cv2.ORB_create()  # Initialize ORB detector
orb_descriptors_original = None  # To store the ORB descriptors of the original image
orb_descriptors_second = None  # To store the ORB descriptors of the second image

#np.set_printoptions(threshold=np.inf) 

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
    image2 = ImageOps.fit(image2, image1.size)  # Ensure the same dimensions
    image1 = np.array(image1.convert('L'))  # Convert to grayscale
    image2 = np.array(image2.convert('L'))  # Convert to grayscale
    similarity, _ = ssim(image1, image2, full=True)
    return similarity

# ORB feature matching and logging keypoints/descriptors
def orb_feature_matching(image1, image2):
    global orb_descriptors_original, orb_descriptors_second
    # Convert images to grayscale for ORB
    image1_cv = cv2.cvtColor(np.array(image1), cv2.COLOR_RGB2GRAY)
    image2_cv = cv2.cvtColor(np.array(image2), cv2.COLOR_RGB2GRAY)

    # Detect keypoints and descriptors
    kp1, des1 = orb.detectAndCompute(image1_cv, None)
    kp2, des2 = orb.detectAndCompute(image2_cv, None)

    if des1 is not None:
        print("\nORB Descriptors for Original Image:")
        print(des1)
    if des2 is not None:
        print("\nORB Descriptors for Second Image:")
        print(des2)

    # Store the descriptors for the second image comparison
    orb_descriptors_original = des1
    orb_descriptors_second = des2

    # Match descriptors using the BFMatcher
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = bf.match(des1, des2)

    # Sort matches based on distance (best matches first)
    matches = sorted(matches, key=lambda x: x.distance)

    # Calculate matching percentage based on number of good matches
    matching_score = len(matches) / min(len(kp1), len(kp2)) * 100
    return matching_score

# Apply 4 random crops and 4 random rotations (2 mild, 2 extensive for each)
def apply_transformations(img, hash_type):
    transformed_images = []
    similarity_results = []
    width, height = img.size

    # Apply 2 mild and 2 extensive random crops
    for _ in range(2):
        left = random.randint(width // 8, width // 4)
        top = random.randint(height // 8, height // 4)
        right = random.randint(3 * width // 4, 7 * width // 8)
        bottom = random.randint(3 * height // 4, 7 * height // 8)
        cropped_img = img.crop((left, top, right, bottom))
        transformed_images.append(cropped_img)

    for _ in range(2):
        left = random.randint(0, width // 4)
        top = random.randint(0, height // 4)
        right = random.randint(3 * width // 4, width)
        bottom = random.randint(3 * height // 4, height)
        cropped_img = img.crop((left, top, right, bottom))
        transformed_images.append(cropped_img)

    # Apply 2 mild and 2 extensive random rotations
    for _ in range(2):
        angle = random.randint(0, 45)
        rotated_img = img.rotate(angle)
        transformed_images.append(rotated_img)

    for _ in range(2):
        angle = random.randint(45, 360)
        rotated_img = img.rotate(angle)
        transformed_images.append(rotated_img)

    # Calculate hashes and SSIM for the transformations
    for transformed_img in transformed_images:
        transformed_hash = generate_hash(transformed_img, hash_type)
        hamming_distance = original_hash - transformed_hash
        total_bits = len(bin(int(str(original_hash), 16))) - 2
        hash_similarity_percentage = (1 - hamming_distance / total_bits) * 100

        ssim_similarity = calculate_ssim(img, transformed_img)

        similarity_results.append((transformed_img, transformed_hash, hash_similarity_percentage, ssim_similarity))

    return similarity_results

# Display transformations and log similarities (no ORB for transformations)
def display_transformations(original_img, similarity_results, container):
    original_img = original_img.resize((300, 300))
    img_tk = ImageTk.PhotoImage(original_img)
    label = tk.Label(container, image=img_tk)
    label.image = img_tk
    label.grid(row=1, column=0, columnspan=2, pady=10)

    original_hash_label = tk.Label(container, text=f"Original Hash: {original_hash}")
    original_hash_label.grid(row=2, column=0, columnspan=2)

    # Display the transformed images and log similarities (no ORB for transformations)
    for i, (img, img_hash, hash_similarity, ssim_similarity) in enumerate(similarity_results):
        img = img.resize((200, 200))
        img_tk = ImageTk.PhotoImage(img)

        label = tk.Label(container, image=img_tk)
        label.image = img_tk
        label.grid(row=(i // 2) + 3, column=(i % 2) * 2)

        hash_label = tk.Label(container, text=f"Hash: {img_hash}\nHash Sim: {hash_similarity:.2f}%\nSSIM: {ssim_similarity:.2f}")
        hash_label.grid(row=(i // 2) + 3, column=(i % 2) * 2 + 1)

# Load and transform the selected image
def load_and_transform_image(hash_type='phash'):
    global original_hash, original_img

    file_path = filedialog.askopenfilename(title="Select an image", filetypes=[("Image Files", "*.jpg *.png *.jpeg")])

    if file_path:
        try:
            original_img = Image.open(file_path)
            original_hash = generate_hash(original_img, hash_type)

            similarity_results = apply_transformations(original_img, hash_type)

            for widget in canvas_frame.winfo_children():
                if isinstance(widget, tk.Button) or isinstance(widget, tk.Label) and widget == result_label:
                    continue
                widget.destroy()

            display_transformations(original_img, similarity_results, canvas_frame)
            canvas_frame.update_idletasks()
            canvas.config(scrollregion=canvas.bbox("all"))

            compare_image_button.grid(row=0, column=2, pady=10)

        except Exception as e:
            messagebox.showerror("Error", f"Error loading image: {e}")
    else:
        messagebox.showinfo("Info", "No file selected.")

# Upload and compare second image and log ORB data
def upload_and_compare_second_image():
    global original_img, orb_descriptors_second

    if original_img is None:
        messagebox.showinfo("Info", "Please upload the first image first.")
        return

    second_image_path = filedialog.askopenfilename(title="Select a second image", filetypes=[("Image Files", "*.jpg *.png *.jpeg")])

    if second_image_path:
        try:
            second_img = Image.open(second_image_path)
            ssim_similarity = calculate_ssim(original_img, second_img)
            orb_similarity = orb_feature_matching(original_img, second_img)

            result_label.config(text=f"Second Image: SSIM: {ssim_similarity:.2f}, ORB Sim: {orb_similarity:.2f}%")

        except Exception as e:
            messagebox.showerror("Error", f"Error comparing images: {e}")
    else:
        messagebox.showinfo("Info", "No second image selected.")

# Set up the GUI
root = tk.Tk()
root.title("Image Transformations, Hash, SSIM, and ORB Similarity")

canvas = tk.Canvas(root)
canvas.pack(side="left", fill="both", expand=True)
scrollbar = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
scrollbar.pack(side="right", fill="y")
canvas.configure(yscrollcommand=scrollbar.set)

canvas_frame = tk.Frame(canvas)
canvas.create_window((0, 0), window=canvas_frame, anchor="nw")

select_image_button = tk.Button(canvas_frame, text="Select and Transform First Image", command=lambda: load_and_transform_image('phash'))
select_image_button.grid(row=0, column=0, pady=10)

compare_image_button = tk.Button(canvas_frame, text="Upload and Compare Second Image", command=upload_and_compare_second_image)
compare_image_button.grid(row=0, column=2, pady=10)

result_label = tk.Label(canvas_frame, text="Comparison result will be displayed here.")
result_label.grid(row=1, column=2, pady=10)

canvas_frame.update_idletasks()
canvas.config(scrollregion=canvas.bbox("all"))

root.geometry("1000x1500")
root.mainloop()
