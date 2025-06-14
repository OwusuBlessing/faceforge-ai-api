import requests
import base64

# Use this function to convert an image file from the filesystem to base64
def image_file_to_base64(image_path):
    with open(image_path, 'rb') as f:
        image_data = f.read()
    return base64.b64encode(image_data).decode('utf-8')

# Use this function to fetch an image from a URL and convert it to base64
def image_url_to_base64(image_url):
    response = requests.get(image_url)
    image_data = response.content
    return base64.b64encode(image_data).decode('utf-8')

# Use this function to convert a list of image URLs to base64
def image_urls_to_base64(image_urls):
    return [image_url_to_base64(url) for url in image_urls]

from config import Config
api_key = Config.SEGMIND_API_KEY
url = "https://api.segmind.com/v1/ideogram-3-replace-background"

# Request payload
data = {
  "prompt": "Add a forest in the background",
  "color_palette": {
  # Either provide a named palette
    "name": "MELON", # required, mutually exclusive with "members"
    # Or provide custom colors
    "members": [ # required, mutually exclusive with "name"
      {
        "color_hex": "", # required if using "members"
        "color_weight": 0 # optional
      }
    ]
  },
  "image": image_url_to_base64("https://ik.imagekit.io/6pxd8st0ugi/default_7ddfe7895a9617c0bf62011f83cd5e47_ARUg4BBrQ.jpg"),  # Or use image_file_to_base64("IMAGE_PATH")
  "rendering_speed": "DEFAULT",
  "magic_prompt": "AUTO",
  "style_codes": [],
  "style_reference_images": []
}

headers = {'x-api-key': api_key}

response = requests.post(url, json=data, headers=headers)
print(response.content)  # The response is the generated image