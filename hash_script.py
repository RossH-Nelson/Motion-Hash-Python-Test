import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image
import imagehash
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase
cred = credentials.Certificate('/Users/rosshartigan/Nelson Development/Motion Ads/pHash-Python-Project/firebase credentials/motion-hash-tester-firebase-adminsdk-qgyxp-2782717ee6.json')
firebase_admin.initialize_app(cred)

db = firestore.client()

# Global variable to store the hash of the selected image
hash1 = None

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
def load_and_hash_image(hash_type='phash'):
    global hash1

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

            # Display the generated hash
            hash_label1.config(text=f"Image Hash ({hash_type.upper()}): {hash1}")
        except Exception as e:
            messagebox.showerror("Error", f"Error loading image: {e}")
    else:
        messagebox.showinfo("Info", "No file selected.")

# Store the hash in Firestore
def store_hash():
    if hash1 is not None:
        try:
            # Store the hash in the Firestore array for the selected document type
            doc_ref = db.collection('campaign_one').document(document_type_var.get())
            doc_ref.update({
                'hashes': firestore.ArrayUnion([str(hash1)])
            })

            messagebox.showinfo("Info", "Hash stored successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Error storing hash: {e}")
    else:
        messagebox.showinfo("Info", "Please select an image before storing the hash.")
        

def compare_hashes():
    if hash1 is not None:
        try:
            #Get document from firestore
            doc_ref = db.collection('campaign_one').document(document_type_var.get())
            doc = doc_ref.get()
            
            if doc.exists:
                stored_hashes = doc.to_dict().get('hashes', [])
                if not stored_hashes:
                    messagebox.showinfo("Info", "No hashes stored for this document type.")
                    return
                
                best_match = None
                best_similarity = 0
                
                #loop through to test hash comparisons
                for stored_hash_str in stored_hashes:
                    stored_hash = imagehash.hex_to_hash(stored_hash_str)
                    hamming_distance = hash1 - stored_hash
                    total_bits = len(bin(int(str(hash1), 16))) - 2
                    similarity_percentage = (1 - hamming_distance / total_bits) * 100
                    
                    if similarity_percentage > best_similarity:
                        best_match = stored_hash_str
                        best_similarity = similarity_percentage
                        
                # Display the best match and its similarity percentage
                result_label.config(text=f"Best match: {best_match}, Similarity: {best_similarity:.2f}%")
            else:
                messagebox.showinfo("Info", "Selected Document does not exist.")
        except Exception as e:
            messagebox.showerror("Error", f"Error comparing hashes: {e}")
    else:
        messagebox.showinfo("Info", "Please select an image before comparing hashes.")
                    

# Set up the GUI
root = tk.Tk()
root.title("Image Hashing and Firestore Storage")

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

# Button to store the hash in Firestore
store_button = tk.Button(root, text="Store Hash in Firestore", command=store_hash)
store_button.pack(pady=20)

#Compare hashes against the ones in firestore document array
compare_button = tk.Button(root, text="Compare Hashes", command=compare_hashes)
compare_button.pack(pady=10)

# Label to display the result of the comparison
result_label = tk.Label(root, text="Comparison result will be displayed here.")
result_label.pack(pady=5)

# Start the GUI event loop
root.geometry("400x500")
root.mainloop()
