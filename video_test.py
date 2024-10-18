import tkinter as tk
from tkinter import filedialog, messagebox
import cv2
from PIL import Image
import imagehash
import os
import time

# Function to extract every nth frame and hash them
def video_to_hashes(video_path, hash_type='phash', frame_interval=360, max_frames=10):
    # Open the video file
    cap = cv2.VideoCapture(video_path)
    hashes = []
    
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))  # Get the total number of frames
    frame_count = 0
    processed_frames = 0
    start_time = time.time()

    while processed_frames < max_frames and frame_count < total_frames:
        # Jump to every nth frame
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count)
        
        success, frame = cap.read()
        
        if success:
            # Log frame read success and frame count
            print(f"Processing frame {frame_count} (every {frame_interval}th frame)")
            
            # Resize frame for faster processing (reduce resolution)
            frame = cv2.resize(frame, (320, 240))  # Resize to 320x240 pixels
            print(f"Frame {frame_count} resized")

            # Convert frame to PIL Image
            pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            print(f"Frame {frame_count} converted to PIL Image")

            # Generate hash for the frame
            if hash_type == 'phash':
                hash_value = imagehash.phash(pil_image)
            elif hash_type == 'ahash':
                hash_value = imagehash.average_hash(pil_image)
            elif hash_type == 'dhash':
                hash_value = imagehash.dhash(pil_image)
            elif hash_type == 'whash':
                hash_value = imagehash.whash(pil_image)
            
            hashes.append(hash_value)
            processed_frames += 1  # Count the number of processed frames
            
            # Log hashing success
            print(f"Hashed frame {frame_count} (processed frames: {processed_frames})")
        
        frame_count += frame_interval  # Jump to the next nth frame
    
    cap.release()
    end_time = time.time()
    print(f"Total time for hashing: {end_time - start_time} seconds")
    print(f"Total frames processed: {processed_frames}")
    
    return hashes

# Function to calculate the similarity between two sets of hashes
def calculate_similarity(hashes1, hashes2):
    if not hashes1 or not hashes2:
        return 0
    
    total = 0
    count = min(len(hashes1), len(hashes2))  # Compare only the number of frames that both videos share
    for h1, h2 in zip(hashes1, hashes2):
        total += (1 - (h1 - h2) / len(h1.hash) ** 2)
    
    return (total / count) * 100  # Return as percentage similarity

# GUI setup
class VideoHasherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Hashing and Similarity")

        # Buttons to upload videos
        self.btn_upload_video1 = tk.Button(root, text="Upload Video 1", command=self.upload_video1)
        self.btn_upload_video1.pack(pady=10)
        
        self.btn_upload_video2 = tk.Button(root, text="Upload Video 2", command=self.upload_video2)
        self.btn_upload_video2.pack(pady=10)
        
        # Label to display similarity score
        self.similarity_label = tk.Label(root, text="Similarity Score: N/A")
        self.similarity_label.pack(pady=20)

        # Button to compute similarity
        self.btn_calculate_similarity = tk.Button(root, text="Calculate Similarity", command=self.calculate_similarity)
        self.btn_calculate_similarity.pack(pady=10)

        # Paths to the uploaded videos
        self.video1_path = None
        self.video2_path = None

    def upload_video1(self):
        self.video1_path = filedialog.askopenfilename(title="Select Video 1", filetypes=[("Video Files", "*.mp4 *.avi *.mov")])
        if self.video1_path:
            messagebox.showinfo("Success", "Video 1 uploaded successfully!")

    def upload_video2(self):
        self.video2_path = filedialog.askopenfilename(title="Select Video 2", filetypes=[("Video Files", "*.mp4 *.avi *.mov")])
        if self.video2_path:
            messagebox.showinfo("Success", "Video 2 uploaded successfully!")

    def calculate_similarity(self):
        if not self.video1_path or not self.video2_path:
            messagebox.showwarning("Error", "Please upload both videos before calculating similarity.")
            return
        
        # Extract hashes from both videos (logging progress)
        print("Starting to process Video 1")
        hashes1 = video_to_hashes(self.video1_path, frame_interval=360, max_frames=10)  # Process every 120th frame
        print("Finished processing Video 1")
        
        print("Starting to process Video 2")
        hashes2 = video_to_hashes(self.video2_path, frame_interval=360, max_frames=10)
        print("Finished processing Video 2")
        
        # Calculate the similarity score
        similarity_score = calculate_similarity(hashes1, hashes2)
        
        # Display the similarity score in the label
        self.similarity_label.config(text=f"Similarity Score: {similarity_score:.2f}%")

# Run the GUI
if __name__ == "__main__":
    root = tk.Tk()
    app = VideoHasherApp(root)
    root.mainloop()
