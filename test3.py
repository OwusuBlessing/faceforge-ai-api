import requests
from config import Config
from enum import Enum

class ThemeStyle(Enum):
    REALISTIC_PORTRAIT = "realistic portrait"
    ANIME = "anime"
    CYBERPUNK = "cyberpunk"
    TOY = "toy"
    GHIBLI = "ghibli"
    EMOJI = "emoji"

def theme_generation(image_url: str, theme: ThemeStyle, api_key: str = Config.DEEPAI_API_KEY) -> dict:
    """
    Generate a themed version of an image using DeepAI's image editor API.
    
    Args:
        image_url (str): URL of the image to edit
        theme (ThemeStyle): Theme style to apply to the image
        api_key (str): DeepAI API key
        
    Returns:
        dict: API response containing the themed image
    """
    response = requests.post(
        "https://api.deepai.org/api/image-editor",
        data={
            'image': image_url,
            'text': f"change to {theme.value}",
        },
        headers={'api-key': api_key}
    )
    return response.json()

# Example usage:
if __name__ == "__main__":
    # Example with image URL
    result = theme_generation(
        image_url="https://ik.imagekit.io/sz509xr3s/sample.png?updatedAt=1749597377172",
        theme=ThemeStyle.EMOJI
    )
    print(result)
    
    # Example with local file
    # with open('path/to/image.jpg', 'rb') as image_file:
    #     response = requests.post(
    #         "https://api.deepai.org/api/image-editor",
    #         files={'image': image_file},
    #         data={'text': f'change to {ThemeStyle.CYBERPUNK.value}'},
    #         headers={'api-key': 'YOUR_API_KEY'}
    #     )
    #     print(response.json())