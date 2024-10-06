import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# Specify the URL of the website you want to scrape
url = "https://www.bmwusa.com/build-your-own.html#/studio/ffm7d87n/design"  # Replace with the target website

# Make a request to the website
response = requests.get(url)

# Parse the HTML content
soup = BeautifulSoup(response.text, "html.parser")

# Create a directory to save the images
os.makedirs("downloaded_images", exist_ok=True)

# Find all image tags
img_tags = soup.find_all("img")

# Download and save each image
for img in img_tags:
    img_url = img.get("src")
    if img_url:
        # Make the URL absolute by joining with the base URL
        img_url = urljoin(url, img_url)
        
        # Check if the URL is valid
        parsed = urlparse(img_url)
        if bool(parsed.netloc) and bool(parsed.scheme):
            # Get the image filename from the URL path
            img_name = os.path.basename(parsed.path)
            
            # Create the full path for saving the image
            img_path = os.path.join("downloaded_images", img_name)

            # Download and save the image using requests
            try:
                # Send a GET request to fetch the image content
                img_response = requests.get(img_url, stream=True)

                # Check if the request was successful
                if img_response.status_code == 200:
                    # Open a local file with write-binary mode to save the image
                    with open(img_path, "wb") as f:
                        # Write the content of the image to the file
                        for chunk in img_response.iter_content(1024):
                            f.write(chunk)
                    print(f"Downloaded: {img_url}")
                else:
                    print(f"Failed to download {img_url}. Status code: {img_response.status_code}")
            except Exception as e:
                print(f"Could not download {img_url}. Error: {e}")