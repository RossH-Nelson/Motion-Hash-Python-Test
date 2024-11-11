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

# Function to resize and crop image to standardized size
def resize_and_crop(image_path, size=(720, 720)):
    """
    Resizes the image to cover the target size and then crops it to exactly 720x720.
    """
    image = Image.open(image_path)
    original_width, original_height = image.size
    target_width, target_height = size

    # Calculate the scale to ensure the resized image covers the target size
    scale = max(target_width / original_width, target_height / original_height)
    new_width = int(original_width * scale)
    new_height = int(original_height * scale)

    # Resize the image
    image_resized = image.resize((new_width, new_height), Image.LANCZOS)

    # Calculate cropping coordinates to center the image
    left = (new_width - target_width) // 2
    top = (new_height - target_height) // 2
    right = left + target_width
    bottom = top + target_height

    # Crop the image
    image_cropped = image_resized.crop((left, top, right, bottom))

    return image_cropped

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

    for idx, file in enumerate(files, start=1):
        print(f"Processing image {idx} of {len(files)}: {file}")
        file_path = os.path.join(image_folder, file)
        try:
            # Open the original image
            original_image = Image.open(file_path)

            # Get original dimensions
            original_size = original_image.size

            # Calculate original pHash
            original_phash = calculate_phash(original_image)

            # Resize and crop to standardized size and calculate pHash
            standardized_image = resize_and_crop(file_path, STANDARDIZED_SIZE)
            standardized_phash = calculate_phash(standardized_image)

            # Apply transformations
            transformations = apply_transformations(original_image)

            # Process each transformation
            row = {"Image Name": file, "Original Size": f"{original_size[0]}x{original_size[1]}"}
            for name, transformed_image in transformations.items():
                # Calculate transformed pHash
                transformed_phash = calculate_phash(transformed_image)

                # Calculate similarity and black pixel percentage
                similarity_to_original = calculate_hash_similarity(original_phash, transformed_phash)
                similarity_to_standardized = calculate_hash_similarity(standardized_phash, transformed_phash)
                black_pixel_percentage = calculate_black_pixel_percentage(transformed_image)

                # Get transformed image size
                transformed_size = f"{transformed_image.size[0]}x{transformed_image.size[1]}"

                # Add to row
                row[f"{name} pHash % Similarity to Original"] = round(similarity_to_original, 2)
                row[f"{name} pHash % Similarity to Standardized"] = round(similarity_to_standardized, 2)
                row[f"{name} % Black Pixels"] = black_pixel_percentage
                row[f"{name} New Size"] = transformed_size

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
    headers = ["Image Name", "Original Size"] + [f"{name} pHash % Similarity to Original" for name in [
        "Mild Crop 1", "Mild Crop 2", "Heavy Crop 1", "Heavy Crop 2",
        "Mild Rotation 1", "Mild Rotation 2", "Heavy Rotation 1", "Heavy Rotation 2"
    ]] + [f"{name} pHash % Similarity to Standardized" for name in [
        "Mild Crop 1", "Mild Crop 2", "Heavy Crop 1", "Heavy Crop 2",
        "Mild Rotation 1", "Mild Rotation 2", "Heavy Rotation 1", "Heavy Rotation 2"
    ]] + [f"{name} % Black Pixels" for name in [
        "Mild Crop 1", "Mild Crop 2", "Heavy Crop 1", "Heavy Crop 2",
        "Mild Rotation 1", "Mild Rotation 2", "Heavy Rotation 1", "Heavy Rotation 2"
    ]] + [f"{name} New Size" for name in [
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
    SAMPLE_SIZE = 1000  # Process all 1000 images
    process_images(image_folder, SAMPLE_SIZE, output_xlsx, log_folder)