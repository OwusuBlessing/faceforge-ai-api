import requests

api_key = "SG_28b00087ea064e64"
url = "https://api.segmind.com/v1/flux-fill-pro"

# Prepare data and files
data = {}
files = {}

# For parameter "mask", you can send a raw file or a URI:
# files['mask'] = open('IMAGE_PATH', 'rb')  # To send a file
data['mask'] = 'https://ik.imagekit.io/sz509xr3s/eyes_mask.png?updatedAt=1749597383340'  # To send a URI
data['seed'] = 965222
# For parameter "image", you can send a raw file or a URI:
# files['image'] = open('IMAGE_PATH', 'rb')  # To send a file
data['image'] = 'https://ik.imagekit.io/sz509xr3s/sample.png?updatedAt=1749597377172' # To send a URI
data['steps'] = 50
data['prompt'] = "red shirt with necklace"
data['guidance'] = 3
data['output_format'] = "jpg"
data['safety_tolerance'] = 2
data['prompt_upsampling'] = False

headers = {'x-api-key': api_key}

# If no files, send as JSON
if files:
    response = requests.post(url, data=data, files=files, headers=headers)
else:
    response = requests.post(url, json=data, headers=headers)
# Save the response content to a file
with open("generated_image.jpg", "wb") as f:
    f.write(response.content)
print("✅ Image saved as generated_image.jpg")