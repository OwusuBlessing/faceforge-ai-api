from src.components.image_edit_mask import ImageEditingPipeline, EditSection
import asyncio
import os

pipeline = ImageEditingPipeline()

async def main():
    try:
        # Local image path
        local_image_path = "data/sample_pics/sample.png"
        
        if not os.path.exists(local_image_path):
            raise FileNotFoundError(f"Image file not found at: {local_image_path}")
            
        print(f"Uploading local image: {local_image_path}")
        # First upload the local image to ImageKit
        image_url = await pipeline.upload_to_imagekit(local_image_path)
        print(f"Image uploaded to ImageKit: {image_url}")
        
        # Now process the uploaded image
        print("Processing image with pipeline...")
        result = await pipeline.process_image(
            image_url=image_url,
            section=EditSection.CLOTHES,
            prompt="change hair to green "
        )
        print(f"Final result: {result}")
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        raise


# Run the async function
asyncio.run(main())





