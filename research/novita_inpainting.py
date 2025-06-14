import requests
import time
import base64
from PIL import Image
import io

def get_models(api_key, visibility=None, source=None, types=None, is_sdxl=None, 
               query=None, is_inpainting=None, limit=100, cursor=None):
    """
    Get model information from Novita API
    
    Args:
        api_key (str): API key for authentication
        visibility (str, optional): Model types: public or private
        source (str, optional): Source of model (civitai, training, uploading)
        types (str, optional): Model types (checkpoint, lora, vae, etc)
        is_sdxl (bool, optional): Filter for SDXL models
        query (str, optional): Search in sd_name, name, and tags
        is_inpainting (bool, optional): Filter for inpainting checkpoints
        limit (int, optional): Number of models per request (0-100)
        cursor (str, optional): Pagination cursor
        
    Returns:
        dict: API response containing models and pagination info
    """
    url = "https://api.novita.ai/v3/model"
    
    # Build query parameters
    params = {}
    if visibility:
        params['filter.visibility'] = visibility
    if source:
        params['filter.source'] = source
    if types:
        params['filter.types'] = types
    if is_sdxl is not None:
        params['filter.is_sdxl'] = str(is_sdxl).lower()
    if query:
        params['filter.query'] = query
    if is_inpainting is not None:
        params['filter.is_inpainting'] = str(is_inpainting).lower()
    if limit:
        params['pagination.limit'] = str(limit)
    if cursor:
        params['pagination.cursor'] = cursor

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    response = requests.get(url, params=params, headers=headers)
    return response.json()

def image_to_base64(image_path):
    """
    Convert image file to base64 string
    
    Args:
        image_path (str): Path to image file
        
    Returns:
        str: Base64 encoded image string
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def inpainting(api_key, params):
    """
    Perform inpainting using Novita API
    
    Args:
        api_key (str): API key for authentication
        params (dict): Inpainting parameters matching the JS example
        
    Returns:
        dict: API response containing task_id
    """
    url = "https://api.novita.ai/v3/async/inpainting"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "request": params
    }
    
    response = requests.post(url, json=payload, headers=headers)
    return response.json()

def check_progress(api_key, task_id):
    """
    Check progress of an inpainting task using the task-result endpoint
    
    Args:
        api_key (str): API key for authentication
        task_id (str): Task ID from inpainting response
        
    Returns:
        dict: Task result information
    """
    url = "https://api.novita.ai/v3/async/task-result"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    params = {
        "task_id": task_id
    }
    
    response = requests.get(url, params=params, headers=headers)
    return response.json()

# Example usage:

if __name__ == "__main__":
    API_KEY = "sk_JSuuHovaSH_2NlCsgXJtUUCAcyvC_obPngZo7-Rr528"
    image_path = "output.jpg"
    mask_image_path = "/Users/macbook/Desktop/blessing_ai/fritz/mask (1).png"
    
    # Convert images to base64
    image_base64 = image_to_base64(image_path)
    mask_base64 = image_to_base64(mask_image_path)
    
    # Example inpainting parameters matching the JS code
    inpainting_params = {
        "model_name": "realisticVisionV51_v51VAE-inpainting_94324.safetensors",
        "image_base64": f"data:image/jpeg;base64,{image_base64}",
        "mask_image_base64": f"data:image/png;base64,{mask_base64}",
        "prompt": "put face cap",
        "negative_prompt": "",
        "sd_vae": "",
        "loras": [],
        "embeddings": [],
        "image_num": 1,
        "mask_blur": 0,
        "sampler_name": "DPM++ 2M Karras",
        "clip_skip": 1,
        "guidance_scale": 7,
        "steps": 20,
        "strength": 1,
        "seed": -1,
        "inpainting_full_res": 0,
        "inpainting_full_res_padding": 0,
        "inpainting_mask_invert": 0,
        "initial_noise_multiplier": 0
    }
    
    # Start inpainting task
    result = inpainting(API_KEY, inpainting_params)

    print(f"result: {result}")
    
    if result and 'task_id' in result:
        task_id = result['task_id']
        
        # Poll for progress
        while True:
            progress = check_progress(API_KEY, task_id)
            
            if progress['task']['status'] == "TASK_STATUS_SUCCEED":
                print("Finished!", progress.get('images', []))
                break
            elif progress['task']['status'] in ["TASK_STATUS_FAILED", "TASK_STATUS_CANCELLED"]:
                print("Failed!", progress['task'].get('reason'))
                break
            elif progress['task']['status'] == "TASK_STATUS_RUNNING":
                print("Progress:", progress['task'].get('progress_percent'))
            
            time.sleep(1)  # Wait 1 second before next check