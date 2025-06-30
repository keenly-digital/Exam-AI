from supabase import create_client, Client
import os

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://kxbjsyuhceggsyvxdkof.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "your-key")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def upload_image_bytes_to_supabase(img_bytes, dest_path, bucket="file-images"):
    """
    Upload image bytes to Supabase Storage and return the public URL.
    - img_bytes: image bytes (not a filename!)
    - dest_path: destination path in the bucket (e.g., 'pdf1/page_1_img_1.png')
    """
    res = supabase.storage.from_(bucket).upload(dest_path, img_bytes)
    if res.get("error"):
        raise Exception(res["error"]["message"])
    # Get public URL
    public_url = supabase.storage.from_(bucket).get_public_url(dest_path)
    return public_url
