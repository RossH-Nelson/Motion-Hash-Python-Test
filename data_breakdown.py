import os
import cv2
import numpy as np
from PIL import Image
import imagehash
from openpyxl import Workbook
from openpyxl.styles import PatternFill
from openpyxl.utils import get_column_letter

# Function to apply transformations (crops and rotations)
def apply_transformations(img):
    height, width = img.shape[:2]

    mild_crop1 = img[int(0.05 * height):int(0.95 * height), int(0.05 * width):int(0.95 * width)]
    mild_crop2 = img[int(0.1 * height):int(0.9 * height), int(0.1 * width):int(0.9 * width)]
    heavy_crop1 = img[int(0.2 * height):int(0.8 * height), int(0.2 * width):int(0.8 * width)]
    heavy_crop2 = img[int(0.25 * height):int(0.75 * height), int(0.25 * width):int(0.75 * width)]

    mild_rotation1 = rotate_image(img, 10)
    mild_rotation2 = rotate_image(img, 15)
    heavy_rotation1 = rotate_image(img, 45)
    heavy_rotation2 = rotate_image(img, 90)

    return [(mild_crop1, "Mild Crop 1"), (mild_crop2, "Mild Crop 2"),
            (heavy_crop1, "Heavy Crop 1"), (heavy_crop2, "Heavy Crop 2"),
            (mild_rotation1, "Mild Rotation 1"), (mild_rotation2, "Mild Rotation 2"),
            (heavy_rotation1, "Heavy Rotation 1"), (heavy_rotation2, "Heavy Rotation 2")]

# Helper function to rotate an image by a specified angle
def rotate_image(img, angle):
    height, width = img.shape[:2]
    matrix = cv2.getRotationMatrix2D((width / 2, height / 2), angle, 1)
    return cv2.warpAffine(img, matrix, (width, height))

# Function to calculate pHash similarity
def phash_similarity(img1, img2):
    hash1 = imagehash.phash(Image.fromarray(cv2.cvtColor(img1, cv2.COLOR_BGR2RGB)))
    hash2 = imagehash.phash(Image.fromarray(cv2.cvtColor(img2, cv2.COLOR_BGR2RGB)))
    return 1 - (hash1 - hash2) / len(hash1.hash) ** 2

# ORB similarity function that uses keypoint matching
def orb_similarity(img1, img2):
    orb = cv2.ORB_create()

    # Detect ORB keypoints and descriptors for both images
    kp1, des1 = orb.detectAndCompute(img1, None)
    kp2, des2 = orb.detectAndCompute(img2, None)

    # If descriptors are not found, return 0 similarity
    if des1 is None or des2 is None:
        return 0

    # Create a BFMatcher object with Hamming distance
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

    # Match descriptors
    matches = bf.match(des1, des2)

    # If there are no matches, return 0 similarity
    if len(matches) == 0:
        return 0

    # Calculate similarity based on the number of good matches
    good_matches = [m for m in matches if m.distance < 42]  # Using a distance threshold to filter good matches
    similarity_percentage = len(good_matches) / min(len(kp1), len(kp2)) * 100
    return min(similarity_percentage, 100)

# Function to color cells based on percentage
def color_cell_based_on_percentage(cell, percentage):
    color = None
    if 0 <= percentage < 10:
        color = '00FF00'  # Green
    elif 10 <= percentage < 20:
        color = '66FF00'  # Yellow-Green
    elif 20 <= percentage < 30:
        color = 'CCFF00'  # Lime
    elif 30 <= percentage < 40:
        color = 'FFFF00'  # Yellow
    elif 40 <= percentage < 50:
        color = 'FFCC00'  # Light Orange
    elif 50 <= percentage < 60:
        color = 'FF9900'  # Orange
    elif 60 <= percentage < 70:
        color = 'FF6600'  # Light Red
    elif 70 <= percentage < 80:
        color = 'FF3300'  # Red
    elif 80 <= percentage < 90:
        color = 'FF0000'  # Dark Red
    elif 90 <= percentage <= 100:
        color = '990000'  # Very Dark Red
    
    if color:
        fill = PatternFill(start_color=color, end_color=color, fill_type="solid")
        cell.fill = fill

# Function to process images from the folder and generate results
def process_images(image_folder, random_image_folder, output_xlsx):
    image_files = [f for f in os.listdir(image_folder) if f.endswith(('.png', '.jpg', '.jpeg'))]
    random_image_files = [f for f in os.listdir(random_image_folder) if f.endswith(('.png', '.jpg', '.jpeg'))]

    # Limit to 5 random images
    random_image_files = random_image_files[:5]

    # Create an Excel workbook and sheet
    wb = Workbook()
    ws = wb.active
    ws.title = "Image Similarities"

    # Write the header
    header = ["Original Image", 
              "Mild Crop 1 pHash %", "Mild Crop 1 ORB %", 
              "Mild Crop 2 pHash %", "Mild Crop 2 ORB %", 
              "Heavy Crop 1 pHash %", "Heavy Crop 1 ORB %", 
              "Heavy Crop 2 pHash %", "Heavy Crop 2 ORB %", 
              "Mild Rotation 1 pHash %", "Mild Rotation 1 ORB %", 
              "Mild Rotation 2 pHash %", "Mild Rotation 2 ORB %", 
              "Heavy Rotation 1 pHash %", "Heavy Rotation 1 ORB %", 
              "Heavy Rotation 2 pHash %", "Heavy Rotation 2 ORB %", 
              "Random Image 1 pHash %", "Random Image 1 ORB %", 
              "Random Image 2 pHash %", "Random Image 2 ORB %", 
              "Random Image 3 pHash %", "Random Image 3 ORB %",
              "Random Image 4 pHash %", "Random Image 4 ORB %",
              "Random Image 5 pHash %", "Random Image 5 ORB %"]

    ws.append(header)
    
    # Process each image in the folder
    for image_file in image_files:
        img_path = os.path.join(image_folder, image_file)
        img = cv2.imread(img_path)
        
        if img is None:
            continue
        
        # Apply transformations
        transformations = apply_transformations(img)
        
        # Collect results for a single row
        row = [image_file]
        
        for transformed_img, _ in transformations:
            # Calculate pHash similarity
            phash_sim = phash_similarity(img, transformed_img)
            
            # Calculate ORB similarity using keypoint matching
            orb_sim = orb_similarity(img, transformed_img)
            
            # Append results to the row (just the numbers now)
            row.extend([round(phash_sim * 100, 2), round(orb_sim, 2)])

        # Add comparisons with each random image
        for random_image_file in random_image_files:
            random_img_path = os.path.join(random_image_folder, random_image_file)
            random_img = cv2.imread(random_img_path)
            
            if random_img is None:
                continue
            
            phash_random_sim = phash_similarity(img, random_img)
            orb_random_sim = orb_similarity(img, random_img)
            row.extend([round(phash_random_sim * 100, 2), round(orb_random_sim, 2)])
        
        # Append the row to the sheet
        ws.append(row)
    
    # Apply color formatting to all percentage cells
    for row in ws.iter_rows(min_row=2, min_col=2, max_row=ws.max_row, max_col=ws.max_column):
        for cell in row:
            try:
                value = float(cell.value)
                color_cell_based_on_percentage(cell, value)
            except ValueError:
                pass  # Ignore non-numeric cells
    
    # Save the workbook as an Excel file
    wb.save(output_xlsx)

if __name__ == "__main__":
    # Define the folder paths and output file
    image_folder = '/Users/rosshartigan/Nelson Development/Motion Ads/Data-Analysis/Flyers'  # Folder with original 1000 images
    random_image_folder = '/Users/rosshartigan/Nelson Development/Motion Ads/Data-Analysis/Random'  # Folder with random images
    output_xlsx = '/Users/rosshartigan/Nelson Development/Motion Ads/Data-Analysis/CSV/results.xlsx'  # Path to save the Excel file
    
    # Process images
    process_images(image_folder, random_image_folder, output_xlsx)
