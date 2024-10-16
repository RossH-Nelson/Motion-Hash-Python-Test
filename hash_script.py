import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import imagehash
import firebase_admin
from firebase_admin import credentials, firestore, storage
from google.cloud import vision
import os
import io
import cv2
import json
import numpy as np

# Initialize Firebase
cred = credentials.Certificate('/Users/rosshartigan/Nelson Development/Motion Ads/pHash-Python-Project/firebase credentials/motion-hash-tester-firebase-adminsdk-qgyxp-2782717ee6.json')
firebase_admin.initialize_app(cred, {
    'storageBucket': 'motion-hash-tester.appspot.com'
})

db = firestore.client()
bucket = storage.bucket()

# Global variables to store the hash of the selected image and detected objects
hash1 = None
detected_objects = []
file_path_global = None

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
    for object_ in objects:
        detected_objects.append(f"{object_.name} (confidence: {object_.score:.2f})")

# Load and hash the selected image based on hash type
def load_and_hash_image(hash_type='phash'):
    global hash1, file_path_global

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

# Store the hash in Firestore and upload the image to Firebase Storage
def store_hash():
    if hash1 is not None and file_path_global is not None:
        try:
            # Generate ORB descriptors for the uploaded image
            img = Image.open(file_path_global)
            orb_keypoints, orb_descriptors = extract_orb_descriptors(img)
            
            # Store ORB descriptors as JSON file in Firebase Storage
            orb_file_path = store_orb_descriptors(orb_descriptors, document_type_var.get(), str(hash1))

            # Store the hash and ORB file link in Firestore
            doc_ref = db.collection('campaign_one').document(document_type_var.get())
            doc_ref.update({
                'hashes': firestore.ArrayUnion([str(hash1)]),
                'orb_links': firestore.ArrayUnion([orb_file_path])
            })

            # Upload the image to Firebase Storage
            upload_image_to_storage(file_path_global, document_type_var.get(), str(hash1))

            messagebox.showinfo("Info", "Hash and ORB descriptors stored and image uploaded successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Error storing hash and ORB descriptors: {e}")
    else:
        messagebox.showinfo("Info", "Please select an image before storing the hash.")

# Extract ORB descriptors from an image
def extract_orb_descriptors(image):
    # Convert the image to grayscale
    image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
    
    # Initialize ORB detector
    orb = cv2.ORB_create()

    # Detect keypoints and descriptors
    keypoints, descriptors = orb.detectAndCompute(image_cv, None)

    return keypoints, descriptors

# Store ORB descriptors as a JSON file in Firebase Storage
def store_orb_descriptors(orb_descriptors, folder_name, image_hash):
    orb_filename = f"{image_hash}_orb.json"

    # Create a path in Firebase Storage with the folder name
    storage_path = f'campaign_one/ORB/{folder_name}/{orb_filename}'

    # Convert the ORB descriptors to a JSON-serializable format
    orb_data = orb_descriptors.tolist()  # Convert numpy array to list

    # Save ORB data to a JSON file locally
    local_orb_file_path = f"/tmp/{orb_filename}"
    with open(local_orb_file_path, 'w') as orb_file:
        json.dump(orb_data, orb_file)

    # Upload the ORB JSON file to Firebase Storage
    blob = bucket.blob(storage_path)
    blob.upload_from_filename(local_orb_file_path)

    return storage_path

# Function to upload an image to Firebase Storage
def upload_image_to_storage(file_path, folder_name, image_hash):
    # Extract the filename from the path
    filename = f"{image_hash}.jpg"

    # Create a path in Firebase Storage with the folder name
    storage_path = f'campaign_one/{folder_name}/{filename}'

    # Upload the image to Firebase Storage
    blob = bucket.blob(storage_path)
    blob.upload_from_filename(file_path)

# Function to download and display the matching image from Firebase Storage
def download_and_display_matching_image(matching_hash):
    try:
        folder_name = document_type_var.get()
        # Using only the hash to fetch the image, no _orb.json suffix
        filename = f"{matching_hash}.jpg"
        storage_path = f'campaign_one/{folder_name}/{filename}'  # Fetch the image based on hash, no ORB

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

    except Exception as e:
        print(f"Error downloading image: {e}")
        messagebox.showerror("Error", f"Error downloading matching image: {e}")

# Compare the newly generated hash with the stored ones in Firestore
def compare_hashes():
    if hash1 is not None:
        try:
            # Get the selected document from Firestore
            doc_ref = db.collection('campaign_one').document(document_type_var.get())
            doc = doc_ref.get()

            if doc.exists:
                stored_hashes = doc.to_dict().get('hashes', [])
                orb_links = doc.to_dict().get('orb_links', [])

                if not stored_hashes:
                    messagebox.showinfo("Info", "No hashes stored for this document type.")
                    return

                best_match = None
                best_similarity = 0

                # Compare the newly generated hash with each stored hash
                for stored_hash_str in stored_hashes:
                    stored_hash = imagehash.hex_to_hash(stored_hash_str)
                    hamming_distance = hash1 - stored_hash
                    total_bits = len(bin(int(str(hash1), 16))) - 2
                    similarity_percentage = (1 - hamming_distance / total_bits) * 100

                    if similarity_percentage > best_similarity:
                        best_match = stored_hash_str
                        best_similarity = similarity_percentage

                # If hash similarity is found with > 75% similarity
                if best_similarity > 75:
                    # Use the best match hash to download and display the image
                    download_and_display_matching_image(best_match)
                    display_uploaded_image(file_path_global)
                    result_label.config(text=f"Best match found with {best_similarity:.2f}% similarity : Hash: {best_match}")
                else:
                    # Fall back to ORB comparison if hash similarity < 75%
                    orb_similarity, best_orb_match = compare_orb_with_stored_images(orb_links, file_path_global)

                    if best_orb_match:
                        result_label.config(text=f"Best ORB match found with {orb_similarity:.2f}% similarity.")
                        # Use the best ORB match hash to download and display the image
                        download_and_display_matching_image(best_orb_match)
                    else:
                        result_label.config(text="No close match found using ORB descriptors.")
            else:
                messagebox.showinfo("Info", "Selected document does not exist.")
        except Exception as e:
            messagebox.showerror("Error", f"Error comparing hashes: {e}")
    else:
        messagebox.showinfo("Info", "Please select an image before comparing hashes.")
        
        
# Function to compare ORB descriptors with stored ORB descriptors
def compare_orb_with_stored_images(orb_links, uploaded_image_path):
    best_match = None
    best_similarity = 0

    # Extract ORB descriptors for the newly uploaded image
    uploaded_image = Image.open(uploaded_image_path)
    _, orb_descriptors_new = extract_orb_descriptors(uploaded_image)

    if orb_descriptors_new is None:
        print("No ORB descriptors found in the new image.")
        return None, 0

    # Compare with each ORB link in Firebase Storage
    for orb_link in orb_links:
        try:
            # Download ORB descriptor file from Firebase Storage
            blob = bucket.blob(orb_link)
            downloaded_orb_data = blob.download_as_bytes()
            orb_descriptors_stored = json.loads(downloaded_orb_data)

            # Convert the stored descriptors back to numpy array
            orb_descriptors_stored = np.array(orb_descriptors_stored, dtype=np.uint8)

            # Perform ORB descriptor matching
            bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
            matches = bf.match(orb_descriptors_new, orb_descriptors_stored)

            # Calculate ORB matching percentage
            orb_similarity = len(matches) / min(len(orb_descriptors_new), len(orb_descriptors_stored)) * 100

            if orb_similarity > best_similarity:
                best_similarity = orb_similarity
                # Use the hash (from orb_link) for fetching the image, strip out "_orb.json"
                best_match = orb_link.split('/')[-1].replace('_orb.json', '')

        except Exception as e:
            print(f"Error downloading or comparing ORB descriptors: {e}")

    return best_similarity, best_match


# Function to display the uploaded image
def display_uploaded_image(file_path):
    try:
        uploaded_image = Image.open(file_path)

        # Resize the image to fit the display
        uploaded_image = uploaded_image.resize((200, 200))
        img = ImageTk.PhotoImage(uploaded_image)

        # Display the uploaded image
        uploaded_image_label.config(image=img)
        uploaded_image_label.image = img  # Keep a reference to avoid garbage collection
    except Exception as e:
        print(f"Error displaying uploaded image: {e}")
        messagebox.showerror("Error", f"Error displaying uploaded image: {e}")

# Set up the GUI
root = tk.Tk()
root.title("Image Hashing, Firestore, and Firebase Storage with Vision AI")

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
store_button = tk.Button(root, text="Store Hash and Upload Image", command=store_hash)
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
