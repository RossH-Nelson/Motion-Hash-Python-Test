import os
from PIL import Image
import imagehash
from openpyxl import Workbook

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

            # Log error if both dimensions are smaller than STANDARDIZED_SIZE
            if original_size[0] < STANDARDIZED_SIZE[0] and original_size[1] < STANDARDIZED_SIZE[1]:
                error_log.append(f"Image {file} is smaller than {STANDARDIZED_SIZE[0]}x{STANDARDIZED_SIZE[1]}: {original_size}")
                continue

            # Calculate original pHash
            original_phash = calculate_phash(original_image)

            # Resize and crop image
            standardized_image = resize_and_crop(file_path, STANDARDIZED_SIZE)

            # Calculate standardized pHash directly from the cropped image
            standardized_phash = calculate_phash(standardized_image)

            # Calculate hash similarity percentage
            hash_similarity = calculate_hash_similarity(original_phash, standardized_phash)

            # Append data
            results.append({
                "Image Name": file,
                "Original Size": f"{original_size[0]}x{original_size[1]}",
                "Original pHash": str(original_phash),
                "Standardized pHash": str(standardized_phash),
                "Hash Similarity (%)": round(hash_similarity, 2)  # New column
            })

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
    headers = ["Image Name", "Original Size", "Original pHash", "Standardized pHash", "Hash Similarity (%)"]
    sheet.append(headers)

    # Add data
    for row in data:
        sheet.append([row["Image Name"], row["Original Size"], row["Original pHash"], row["Standardized pHash"], row["Hash Similarity (%)"]])

    # Save workbook
    workbook.save(output_path)
    print(f"Results saved to {output_path}")

# Main execution
if __name__ == "__main__":
    SAMPLE_SIZE = 25  # Process only 25 images
    process_images(image_folder, SAMPLE_SIZE, output_xlsx, log_folder)