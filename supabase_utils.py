from supabase import create_client, Client
import os

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://kxbjsyuhceggsyvxdkof.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt4YmpzeXVoY2VnZ3N5dnhka29mIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MTIwODk5NiwiZXhwIjoyMDY2Nzg0OTk2fQ.uNALBmMDiFQat6CKjGmFYRFXfw4ovb2hTRmd3rK1RaI")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def upload_image_to_supabase(local_file_path, bucket="file-images", dest_path=None):
    """
    Upload a file to Supabase Storage and return its public URL.
    """
    if dest_path is None:
        dest_path = os.path.basename(local_file_path)
    with open(local_file_path, "rb") as f:
        res = supabase.storage.from_(bucket).upload(dest_path, f)
    if res.get("error"):
        raise Exception(res["error"]["message"])
    # Get public URL
    public_url = supabase.storage.from_(bucket).get_public_url(dest_path)
    return public_url
