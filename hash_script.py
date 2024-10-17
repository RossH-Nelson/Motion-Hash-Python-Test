import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import imagehash
import random
import firebase_admin
from firebase_admin import credentials, firestore, storage
from google.cloud import vision
import numpy as np
import cv2  
import os
import io

# Initialize Firebase
cred = credentials.Certificate('/Users/rosshartigan/Nelson Development/Motion Ads/pHash-Python-Project/firebase credentials/motion-hash-tester-firebase-adminsdk-qgyxp-2782717ee6.json')
# Update the path to your Firebase credentials
firebase_admin.initialize_app(cred, {
    'storageBucket': 'motion-hash-tester.appspot.com'
})

db = firestore.client()
bucket = storage.bucket()

# Global variables to store the hash, ORB descriptors, and detected objects
hash1 = None
orb_descriptors = None
detected_objects = []
file_path_global = None
original_hash = None

# Global counters for read and write operations
read_count = 0
write_count = 0

# ORB detector
orb = cv2.ORB_create()

def increment_read():
    global read_count
    read_count += 1
    print(f"Total reads: {read_count}")

def increment_write():
    global write_count
    write_count += 1
    print(f"Total writes: {write_count}")

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

# Google Vision AI - Object Detection
def localize_objects(path):
    """Detects objects in a local image."""
    global detected_objects
    client = vision.ImageAnnotatorClient()

    # Read the local image file
    with open(path, "rb") as image_file:
        content = image_file.read()
    image = vision.Image(content=content)

    # Perform object localization (detection)
    objects = client.object_localization(image=image).localized_object_annotations

    detected_objects = []  # Reset detected objects
    print(f"Number of objects found: {len(objects)}")
    for object_ in objects:
        detected_objects.append(f"{object_.name} (confidence: {object_.score:.2f})")
        print(f"\n{object_.name} (confidence: {object_.score:.2f})")
        print("Normalized bounding polygon vertices: ")
        for vertex in object_.bounding_poly.normalized_vertices:
            print(f" - ({vertex.x}, {vertex.y})")

# ORB feature matching
def orb_feature_matching(image1, image2):
    image1_cv = cv2.cvtColor(np.array(image1), cv2.COLOR_RGB2GRAY)
    image2_cv = cv2.cvtColor(np.array(image2), cv2.COLOR_RGB2GRAY)

    kp1, des1 = orb.detectAndCompute(image1_cv, None)
    kp2, des2 = orb.detectAndCompute(image2_cv, None)

    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = bf.match(des1, des2)
    matches = sorted(matches, key=lambda x: x.distance)

    matching_score = len(matches) / min(len(kp1), len(kp2)) * 100
    return matching_score

# Store hash and ORB descriptors in Firestore and upload the image to Firebase Storage
def store_orb_features():
    if hash1 is not None and orb_descriptors is not None and file_path_global is not None:
        try:
            # Convert ORB descriptors to a Firestore-compatible format (store each descriptor as a dictionary)
            orb_descriptors_list = [descriptor.tolist() for descriptor in orb_descriptors]

            # Store the hash and ORB descriptors in Firestore (this is a write operation)
            doc_ref = db.collection('campaign_one').document(document_type_var.get())
            doc_ref.update({
                'hashes': firestore.ArrayUnion([str(hash1)]),
                'orb_descriptors': orb_descriptors_list  # Store ORB descriptors as a list of lists
            })
            increment_write()  # Log the write operation

            # Upload the image to Firebase Storage
            upload_image_to_storage(file_path_global, document_type_var.get(), str(hash1))

            messagebox.showinfo("Info", "Hash, ORB descriptors stored and image uploaded successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Error storing hash, ORB descriptors, and uploading image: {e}")
    else:
        messagebox.showinfo("Info", "Please select an image before storing.")

# Load and hash the selected image based on hash type
def load_and_hash_image(hash_type='phash'):
    global hash1, orb_descriptors, file_path_global

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
            hash1 = generate_hash(img, hash_type)

            # Extract ORB descriptors
            img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)
            _, orb_descriptors = orb.detectAndCompute(img_cv, None)

            # Save the image path to a global variable for future storage
            file_path_global = file_path

            # Perform object detection using Google Vision API
            localize_objects(file_path)

            # Display the generated hash and detected objects
            hash_label1.config(text=f"Image Hash ({hash_type.upper()}): {hash1}")
            object_label.config(text=f"Detected Objects: {', '.join(detected_objects)}")

        except Exception as e:
            messagebox.showerror("Error", f"Error loading image: {e}")
    else:
        messagebox.showinfo("Info", "No file selected.")

# Function to upload an image to Firebase Storage
def upload_image_to_storage(file_path, folder_name, image_hash):
    # Extract the filename from the path
    filename = f"{image_hash}.jpg"

    # Create a path in Firebase Storage with the folder name
    storage_path = f'campaign_one/{folder_name}/{filename}'

    # Upload the image to Firebase Storage
    blob = bucket.blob(storage_path)
    blob.upload_from_filename(file_path)

    print(f"Image uploaded to: {storage_path}")

# Function to download and display the matching image from Firebase Storage
def download_and_display_matching_image(matching_hash):
    try:
        folder_name = document_type_var.get()
        filename = f"{matching_hash}.jpg"
        storage_path = f'campaign_one/{folder_name}/{filename}'

        # Download the image from Firebase Storage
        blob = bucket.blob(storage_path)
        downloaded_image = blob.download_as_bytes()

        # Load the image using PIL
        image = Image.open(io.BytesIO(downloaded_image))

        # Resize the image to fit the display
        image = image.resize((200, 200))
        img = ImageTk.PhotoImage(image)

        # Display the matching image
        matching_image_label.config(image=img)
        matching_image_label.image = img  # Keep a reference to avoid garbage collection
        print(f"Downloaded and displayed matching image from: {storage_path}")
    except Exception as e:
        print(f"Error downloading image: {e}")
        messagebox.showerror("Error", f"Error downloading matching image: {e}")

# Function to compare ORB descriptors using FLANN-based matching
def compare_orb_descriptors(new_descriptors, stored_descriptors):
    # FLANN-based matching parameters
    index_params = dict(algorithm=6, table_number=6, key_size=12, multi_probe_level=1)
    search_params = dict(checks=50)
    flann = cv2.FlannBasedMatcher(index_params, search_params)

    matches = flann.knnMatch(new_descriptors, stored_descriptors, k=2)
    good_matches = []

    for m, n in matches:
        if m.distance < 0.7 * n.distance:
            good_matches.append(m)

    matching_score = len(good_matches) / len(new_descriptors) * 100
    return matching_score

# Function to convert stored ORB descriptors back to numpy array for comparison
def get_orb_descriptors_from_firestore(stored_descriptors_list):
    return np.array(stored_descriptors_list, dtype=np.uint8)

# Modify the function where you perform Firestore reads
def compare_hashes():
    global read_count
    if hash1 is not None:
        try:
            # Get the selected document from Firestore (this is a read operation)
            doc_ref = db.collection('campaign_one').document(document_type_var.get())
            doc = doc_ref.get()
            increment_read()  # Log the read operation

            if doc.exists:
                stored_hashes = doc.to_dict().get('hashes', [])
                stored_orb_descriptors_list = doc.to_dict().get('orb_descriptors', [])
                if not stored_hashes:
                    messagebox.showinfo("Info", "No hashes stored for this document type.")
                    return

                best_match = None
                best_similarity = 0
                best_orb_similarity = 0

                # Compare the newly generated hash with each stored hash
                for stored_hash_str in stored_hashes:
                    stored_hash = imagehash.hex_to_hash(stored_hash_str)
                    hamming_distance = hash1 - stored_hash
                    total_bits = len(bin(int(str(hash1), 16))) - 2
                    similarity_percentage = (1 - hamming_distance / total_bits) * 100

                    if similarity_percentage > best_similarity:
                        best_match = stored_hash_str
                        best_similarity = similarity_percentage

                # Compare ORB descriptors using FLANN
                stored_orb_descriptors = get_orb_descriptors_from_firestore(stored_orb_descriptors_list)
                orb_similarity = compare_orb_descriptors(orb_descriptors, stored_orb_descriptors)

                if orb_similarity > best_orb_similarity:
                    best_orb_similarity = orb_similarity

                # Display the result of comparison
                download_and_display_matching_image(best_match)
                display_uploaded_image(file_path_global)
                result_label.config(text=f"Best match: Hash {best_similarity:.2f}%, ORB {best_orb_similarity:.2f}%")
            else:
                messagebox.showinfo("Info", "Selected document does not exist.")
        except Exception as e:
            messagebox.showerror("Error", f"Error comparing hashes: {e}")
    else:
        messagebox.showinfo("Info", "Please select an image before comparing hashes.")

# Set up the GUI
root = tk.Tk()
root.title("Image Hashing, Firestore, and Firebase Storage with Vision AI and ORB")

# Hash type selection dropdown menu
hash_type_var = tk.StringVar(value="phash")  # Default value
document_type_var = tk.StringVar(value="flyers")  # Default value for Firestore document

# Function to update the selected hash type
def update_hash_type(value):
    hash_type_var.set(value)

# Function to update the selected document type
def update_document_type(value):
    document_type_var.set(value)

# Dropdown to select hashing method
hash_type_label = tk.Label(root, text="Select Hashing Method:")
hash_type_label.pack(pady=5)

hash_type_dropdown = tk.OptionMenu(root, hash_type_var, "phash", "ahash", "dhash", "whash", command=update_hash_type)
hash_type_dropdown.pack(pady=10)

# Dropdown to select document type (bikes, boxes, flyers)
document_type_label = tk.Label(root, text="Select the document type:")
document_type_label.pack(pady=5)

document_type_dropdown = tk.OptionMenu(root, document_type_var, "bikes", "boxes", "flyers", command=update_document_type)
document_type_dropdown.pack(pady=10)

# Button to select an image and generate its hash
select_image_button = tk.Button(root, text="Select and Hash Image", command=lambda: load_and_hash_image(hash_type_var.get()))
select_image_button.pack(pady=10)

# Label to display the generated hash
hash_label1 = tk.Label(root, text="Image hash will be displayed here.")
hash_label1.pack(pady=5)

# Label to display detected objects using Vision AI
object_label = tk.Label(root, text="Detected Objects will be displayed here.")
object_label.pack(pady=5)

# Label to display the uploaded image
uploaded_image_label = tk.Label(root, text="Uploaded Image will be displayed here.")
uploaded_image_label.pack(pady=5)

# Label to display the matching image from Firebase Storage
matching_image_label = tk.Label(root, text="Matching Image will be displayed here.")
matching_image_label.pack(pady=5)

# Button to store the hash in Firestore and upload the image to Storage
store_button = tk.Button(root, text="Store Hash and Upload Image", command=store_orb_features)
store_button.pack(pady=20)

# Button to compare the new hash with stored hashes
compare_button = tk.Button(root, text="Compare Hashes", command=compare_hashes)
compare_button.pack(pady=10)

# Label to display the result of the comparison
result_label = tk.Label(root, text="Comparison result will be displayed here.")
result_label.pack(pady=5)

# Start the GUI event loop
root.geometry("750x1000")
root.mainloop()
