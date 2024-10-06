from PIL import Image
import os

def convert_to_webp(input_directory, output_directory):
    """
    Convert all .jpg and .png images in the input directory to .webp format.

    Parameters:
    input_directory (str): Directory containing .jpg or .png images to convert.
    output_directory (str): Directory to save converted .webp images.
    """
    # Ensure output directory exists
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    # Loop through files in the input directory
    for filename in os.listdir(input_directory):
        if filename.endswith('.jpg') or filename.endswith('.png'):
            input_path = os.path.join(input_directory, filename)
            output_path = os.path.join(output_directory, os.path.splitext(filename)[0] + '.webp')
            
            # Open image and convert to .webp
            try:
                with Image.open(input_path) as img:
                    img.save(output_path, 'webp')
                    print(f"Converted {filename} to {output_path}")
            except Exception as e:
                print(f"Failed to convert {filename}: {e}")

if __name__ == "__main__":
    input_dir = "static\images\cars\BMW\X7\Blue\Steel"  # Replace with your input directory path
    output_dir = "static\images\cars\BMW\X7\Blue\Steel"  # Replace with your output directory path
    convert_to_webp(input_dir, output_dir)