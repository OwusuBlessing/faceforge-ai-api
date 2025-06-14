import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    IMAGEKIT_PRIVATE_KEY = os.getenv('IMAGEKIT_PRIVATE_KEY')
    IMAGEKIT_PUBLIC_KEY = os.getenv('IMAGEKIT_PUBLIC_KEY')
    IMAGEKIT_URL_ENDPOINT = os.getenv('IMAGEKIT_URL_ENDPOINT')
    SEGMIND_API_KEY = os.getenv('SEGMIND_API_KEY')
    DEEPAI_API_KEY = os.getenv('DEEPAI_API_KEY')
    HEDRA_API_KEY = os.getenv('HEDRA_API_KEY')
    print(f"HEDRA API KEY: {HEDRA_API_KEY}")
   
        