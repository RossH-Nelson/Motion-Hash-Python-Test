import os
from PIL import Image
import imagehash
from openpyxl import Workbook
from openpyxl.styles import PatternFill
import numpy as np

# Paths
image_folder = '/Users/rosshartigan/Nelson Development/Motion Ads/Data-Analysis/Flyers'
output_xlsx = '/Users/rosshartigan/Nelson Development/Motion Ads/Data-Analysis/CSV/results.xlsx'
log_folder = '/Users/rosshartigan/Nelson Development/Motion Ads/Data-Analysis/CSV/Logs'

# Global standardized size
STANDARDIZED_SIZE = (720, 720)

# Ensure the log folder exists
os.makedirs(log_folder, exist_ok=True)

# Function to calculate pHash
def calculate_phash(image):
    return imagehash.phash(image)

# Function to calculate hash similarity percentage
def calculate_hash_similarity(hash1, hash2):
    """
    Calculates the percentage similarity between two perceptual hashes.
    """
    hamming_distance = hash1 - hash2
    hash_length = len(hash1.hash) ** 2  # Total number of bits in the hash
    similarity_percentage = (1 - (hamming_distance / hash_length)) * 100
    return similarity_percentage

# Function to calculate black pixel percentage
def calculate_black_pixel_percentage(image):
    """
    Calculates the percentage of black pixels in the image.
    """
    grayscale_image = image.convert("L")  # Convert to grayscale
    image_array = np.array(grayscale_image)  # Convert to numpy array
    black_pixel_count = np.sum(image_array == 0)  # Count pixels with value 0 (black)
    total_pixels = image_array.size
    black_percentage = (black_pixel_count / total_pixels) * 100
    return round(black_percentage, 2)

# Function to apply mild and heavy crops and rotations
def apply_transformations(original_image):
    """
    Applies two mild and two heavy crops and rotations to the original image.
    Returns a dictionary of transformation results.
    """
    width, height = original_image.size
    transformations = {
        "Mild Crop 1": original_image.crop((int(0.05 * width), int(0.05 * height), int(0.95 * width), int(0.95 * height))),
        "Mild Crop 2": original_image.crop((int(0.1 * width), int(0.1 * height), int(0.9 * width), int(0.9 * height))),
        "Heavy Crop 1": original_image.crop((int(0.2 * width), int(0.2 * height), int(0.8 * width), int(0.8 * height))),
        "Heavy Crop 2": original_image.crop((int(0.25 * width), int(0.25 * height), int(0.75 * width), int(0.75 * height))),
        "Mild Rotation 1": original_image.rotate(10, fillcolor="black"),
        "Mild Rotation 2": original_image.rotate(15, fillcolor="black"),
        "Heavy Rotation 1": original_image.rotate(45, fillcolor="black"),
        "Heavy Rotation 2": original_image.rotate(90, fillcolor="black"),
    }
    return transformations

# Function to color cells based on percentage
def color_cell_based_on_percentage(cell, percentage):
    color = None
    if 0 <= percentage < 10:
        color = '00FF00'  # Bright Green
    elif 10 <= percentage < 20:
        color = '66FF00'
    elif 20 <= percentage < 30:
        color = 'CCFF00'
    elif 30 <= percentage < 40:
        color = 'FFFF00'  # Yellow
    elif 40 <= percentage < 50:
        color = 'FFCC00'
    elif 50 <= percentage < 60:
        color = 'FF9900'
    elif 60 <= percentage < 70:
        color = 'FF6600'
    elif 70 <= percentage < 80:
        color = 'FF3300'
    elif 80 <= percentage < 90:
        color = 'FF0000'  # Bright Red
    elif 90 <= percentage <= 100:
        color = '990000'  # Dark Red
    
    if color:
        fill = PatternFill(start_color=color, end_color=color, fill_type="solid")
        cell.fill = fill

# Function to process images and store data
def process_images(image_folder, sample_size, output_xlsx, log_folder):
    files = os.listdir(image_folder)[:sample_size]  # Take only a sample of images
    results = []
    error_log = []  # To log errors for images smaller than the target size

    for file in files:
        file_path = os.path.join(image_folder, file)
        try:
            # Open the original image
            original_image = Image.open(file_path)

            # Get original dimensions
            original_size = original_image.size

            # Calculate original pHash
            original_phash = calculate_phash(original_image)

            # Apply transformations
            transformations = apply_transformations(original_image)

            # Process each transformation
            row = {"Image Name": file, "Original Size": f"{original_size[0]}x{original_size[1]}"}
            for name, transformed_image in transformations.items():
                # Calculate transformed pHash
                transformed_phash = calculate_phash(transformed_image)

                # Calculate similarity and black pixel percentage
                similarity = calculate_hash_similarity(original_phash, transformed_phash)
                black_pixel_percentage = calculate_black_pixel_percentage(transformed_image)

                # Add to row
                row[f"{name} pHash % Similarity"] = round(similarity, 2)
                row[f"{name} % Black Pixels"] = black_pixel_percentage

            # Append row
            results.append(row)

        except Exception as e:
            print(f"Error processing {file}: {e}")
            error_log.append(f"Error processing {file}: {e}")

    # Write results to Excel
    write_to_excel(results, output_xlsx)

    # Write errors to log file in the specified folder
    if error_log:
        error_log_path = os.path.join(log_folder, "error_log.txt")
        with open(error_log_path, "w") as log_file:
            log_file.write("\n".join(error_log))
        print(f"Error log saved to {error_log_path}")

# Function to write results to Excel
def write_to_excel(data, output_path):
    workbook = Workbook()
    sheet = workbook.active

    # Add headers
    headers = ["Image Name", "Original Size"] + [f"{name} pHash % Similarity" for name in [
        "Mild Crop 1", "Mild Crop 2", "Heavy Crop 1", "Heavy Crop 2",
        "Mild Rotation 1", "Mild Rotation 2", "Heavy Rotation 1", "Heavy Rotation 2"
    ]] + [f"{name} % Black Pixels" for name in [
        "Mild Crop 1", "Mild Crop 2", "Heavy Crop 1", "Heavy Crop 2",
        "Mild Rotation 1", "Mild Rotation 2", "Heavy Rotation 1", "Heavy Rotation 2"
    ]]
    sheet.append(headers)

    # Add data
    for row in data:
        sheet.append([row.get(header, "") for header in headers])

    # Apply coloring to relevant columns
    for col_idx in range(3, len(headers) + 1):  # Start from 3rd column
        for cell in sheet.iter_cols(min_col=col_idx, max_col=col_idx, min_row=2, max_row=sheet.max_row):
            for c in cell:
                try:
                    value = float(c.value)
                    color_cell_based_on_percentage(c, value)
                except ValueError:
                    pass

    # Save workbook
    workbook.save(output_path)
    print(f"Results saved to {output_path}")

# Main execution
if __name__ == "__main__":
    SAMPLE_SIZE = 25  # Process only 25 images
    process_images(image_folder, SAMPLE_SIZE, output_xlsx, log_folder)