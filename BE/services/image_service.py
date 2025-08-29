import cloudinary
import cloudinary.uploader
from fastapi import UploadFile
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

async def upload_image(file: UploadFile) -> str:
    """Upload image to Cloudinary and return URL"""
    
    try:
        # Read file content
        file_content = await file.read()
        
        # Upload to Cloudinary
        upload_result = cloudinary.uploader.upload(
            file_content,
            folder="restaurant_payments",
            resource_type="image",
            quality="auto",
            fetch_format="auto"
        )
        
        return upload_result["secure_url"]
        
    except Exception as e:
        raise Exception(f"Image upload failed: {str(e)}")