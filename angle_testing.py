import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import imagehash
import cv2
import numpy as np
import os

# ORB detector
orb = cv2.ORB_create()

# GUI class
class ImageComparisonApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Comparison")
        self.root.geometry("800x600")

        # Variables to store the original and comparison images
        self.original_image_cv = None
        self.comparison_images_cv = []
        self.similarity_results = []  # Store similarity results for download

        # Button to upload the original image
        self.upload_original_button = tk.Button(root, text="Upload Original Image", command=self.upload_original_image)
        self.upload_original_button.pack(pady=10)

        # Button to upload 4 comparison images
        self.upload_comparisons_button = tk.Button(root, text="Upload 4 Comparison Images", command=self.upload_comparison_images, state=tk.DISABLED)
        self.upload_comparisons_button.pack(pady=10)

        # Label to display similarity results
        self.results_label = tk.Label(root, text="Similarity Results will be displayed here.")
        self.results_label.pack(pady=5)

        # Button to process images
        self.process_button = tk.Button(root, text="Compare Images", command=self.compare_images, state=tk.DISABLED)
        self.process_button.pack(pady=10)

        # Button to download results
        self.download_button = tk.Button(root, text="Download Results", command=self.download_results, state=tk.DISABLED)
        self.download_button.pack(pady=10)

    def upload_original_image(self):
        file_path = filedialog.askopenfilename(title="Select the Original Image", filetypes=[("Image Files", "*.jpg *.png *.jpeg")])
        if file_path:
            try:
                # Load the original image and convert it to OpenCV format
                self.original_image = Image.open(file_path)
                self.original_image_cv = cv2.cvtColor(np.array(self.original_image), cv2.COLOR_RGB2BGR)
                
                self.upload_comparisons_button.config(state=tk.NORMAL)  # Enable uploading of comparison images
                messagebox.showinfo("Success", "Original image uploaded successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Error loading original image: {e}")

    def upload_comparison_images(self):
        # Allow user to select exactly 4 comparison images
        file_paths = filedialog.askopenfilenames(title="Select 4 Comparison Images", filetypes=[("Image Files", "*.jpg *.png *.jpeg")])
        if len(file_paths) != 4:
            messagebox.showwarning("Warning", "Please select exactly 4 comparison images.")
            return

        try:
            # Load each comparison image and convert to OpenCV format
            self.comparison_images_cv = []
            self.comparison_images = []
            for path in file_paths:
                img = Image.open(path)
                self.comparison_images.append(img)
                self.comparison_images_cv.append(cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR))
            
            self.process_button.config(state=tk.NORMAL)  # Enable the comparison button
            messagebox.showinfo("Success", "4 comparison images uploaded successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Error loading comparison images: {e}")

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

    def compare_images(self):
        if self.original_image_cv is None or len(self.comparison_images_cv) != 4:
            messagebox.showwarning("Warning", "Please ensure that the original image and exactly 4 comparison images are uploaded.")
            return

        self.similarity_results = []  # Reset results for new processing

        # Perform pHash and ORB comparisons between the original and each comparison image
        for i, comp_img_cv in enumerate(self.comparison_images_cv, start=1):
            phash_sim = self.phash_similarity(self.original_image_cv, comp_img_cv) * 100
            orb_sim = self.orb_similarity(self.original_image_cv, comp_img_cv)
            result = f"Image {i} vs Original: pHash {round(phash_sim, 2)}%, ORB {round(orb_sim, 2)}%"
            self.similarity_results.append(result)

        # Display results in the GUI
        result_msg = "\n".join(self.similarity_results)
        self.results_label.config(text=result_msg)
        
        # Enable download button after processing
        self.download_button.config(state=tk.NORMAL)

    def download_results(self):
        save_dir = filedialog.askdirectory(title="Select folder to save results")
        if save_dir:
            results_path = os.path.join(save_dir, "Similarity_Results.txt")
            with open(results_path, "w") as f:
                for result in self.similarity_results:
                    f.write(result + "\n")
            messagebox.showinfo("Download Complete", "Similarity results have been saved as a text file.")

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageComparisonApp(root)
    root.mainloop()