from supabase import create_client, Client
import os

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://kxbjsyuhceggsyvxdkof.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt4YmpzeXVoY2VnZ3N5dnhka29mIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MTIwODk5NiwiZXhwIjoyMDY2Nzg0OTk2fQ.uNALBmMDiFQat6CKjGmFYRFXfw4ovb2hTRmd3rK1RaI")

# THIS LINE MAKES BUCKET_NAME AVAILABLE TO IMPORT
BUCKET_NAME = "file-images"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def upload_image_bytes_to_supabase(img_bytes, dest_path, bucket=BUCKET_NAME):
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

# For compatibility with older import usage
upload_image_to_supabase = upload_image_bytes_to_supabase
