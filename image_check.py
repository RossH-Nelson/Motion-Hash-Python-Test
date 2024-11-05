import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import imagehash
import cv2
import numpy as np
import os

# Global variables
hash1 = None
orb_descriptors = None
altered_images = {}

# ORB detector
orb = cv2.ORB_create()

# GUI class
class ImageProcessorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Processor")
        self.root.geometry("800x600")

        # Image upload button
        self.upload_button = tk.Button(root, text="Upload Image", command=self.upload_image)
        self.upload_button.pack(pady=10)

        # Label to display the uploaded image
        self.uploaded_image_label = tk.Label(root, text="Uploaded Image will be displayed here.")
        self.uploaded_image_label.pack(pady=5)

        # Label for similarity results
        self.similarity_results_label = tk.Label(root, text="Similarity Results will be displayed here.")
        self.similarity_results_label.pack(pady=5)

        # Button to process image
        self.process_button = tk.Button(root, text="Process Image", command=self.process_image, state=tk.DISABLED)
        self.process_button.pack(pady=10)

        # Button to download altered images
        self.download_button = tk.Button(root, text="Download Altered Images", command=self.download_images, state=tk.DISABLED)
        self.download_button.pack(pady=10)

    def upload_image(self):
        file_path = filedialog.askopenfilename(title="Select an image", filetypes=[("Image Files", "*.jpg *.png *.jpeg")])
        if file_path:
            try:
                # Load the image with PIL and display it
                self.original_image = Image.open(file_path)
                self.original_image_cv = cv2.cvtColor(np.array(self.original_image), cv2.COLOR_RGB2BGR)
                self.display_image(self.original_image, self.uploaded_image_label)
                
                self.process_button.config(state=tk.NORMAL)
                messagebox.showinfo("Success", "Image uploaded successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Error loading image: {e}")

    def display_image(self, image, label):
        # Display image in the specified Tkinter label
        image.thumbnail((200, 200))
        img_tk = ImageTk.PhotoImage(image)
        label.config(image=img_tk)
        label.image = img_tk

    def apply_transformations(self, img):
        height, width = img.shape[:2]

        transformations = {
            "Mild Crop 1": img[int(0.05 * height):int(0.95 * height), int(0.05 * width):int(0.95 * width)],
            "Mild Crop 2": img[int(0.1 * height):int(0.9 * height), int(0.1 * width):int(0.9 * width)],
            "Heavy Crop 1": img[int(0.2 * height):int(0.8 * height), int(0.2 * width):int(0.8 * width)],
            "Heavy Crop 2": img[int(0.25 * height):int(0.75 * height), int(0.25 * width):int(0.75 * width)],
            "Mild Rotation 1": self.rotate_image(img, 10),
            "Mild Rotation 2": self.rotate_image(img, 15),
            "Heavy Rotation 1": self.rotate_image(img, 45),
            "Heavy Rotation 2": self.rotate_image(img, 90)
        }
        return transformations

    def rotate_image(self, img, angle):
        height, width = img.shape[:2]
        matrix = cv2.getRotationMatrix2D((width / 2, height / 2), angle, 1)
        return cv2.warpAffine(img, matrix, (width, height))

    def phash_similarity(self, img1, img2):
        hash1 = imagehash.phash(Image.fromarray(cv2.cvtColor(img1, cv2.COLOR_BGR2RGB)))
        hash2 = imagehash.phash(Image.fromarray(cv2.cvtColor(img2, cv2.COLOR_BGR2RGB)))
        return 1 - (hash1 - hash2) / len(hash1.hash) ** 2

    def orb_similarity(self, img1, img2):
        kp1, des1 = orb.detectAndCompute(img1, None)
        kp2, des2 = orb.detectAndCompute(img2, None)
        
        if des1 is None or des2 is None:
            return 0

        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        matches = bf.match(des1, des2)
        good_matches = [m for m in matches if m.distance < 42]
        similarity_percentage = len(good_matches) / min(len(kp1), len(kp2)) * 100
        return min(similarity_percentage, 100)

    def process_image(self):
        # Apply transformations to the original image
        transformations = self.apply_transformations(self.original_image_cv)
        self.altered_images = transformations  # Save for download

        results = []
        for name, transformed_img in transformations.items():
            phash_sim = self.phash_similarity(self.original_image_cv, transformed_img) * 100
            orb_sim = self.orb_similarity(self.original_image_cv, transformed_img)
            results.append(f"{name}: pHash {round(phash_sim, 2)}%, ORB {round(orb_sim, 2)}%")

        # Display results
        result_msg = "\n".join(results)
        self.similarity_results_label.config(text=result_msg)
        self.download_button.config(state=tk.NORMAL)

    def download_images(self):
        save_dir = filedialog.askdirectory(title="Select folder to save altered images")
        if save_dir:
            # Save original image
            original_save_path = os.path.join(save_dir, "Original_Image.png")
            self.original_image.save(original_save_path)
            
            # Save altered images
            for name, img in self.altered_images.items():
                save_path = os.path.join(save_dir, f"{name}.png")
                cv2.imwrite(save_path, img)
            
            messagebox.showinfo("Download Complete", "Original and altered images have been saved.")

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageProcessorApp(root)
    root.mainloop()