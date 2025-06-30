from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import shutil
import os
import tempfile
import json
from pdf_content_extraction import parse_pdf_and_extract_images
from parse_pdf_into_json import TopicProcessor, process_content
import re
import uvicorn
from remove_duplicate_question import remove_duplicate_questions
from supabase_utils import upload_image_to_supabase

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or restrict to ["http://localhost:5173"] for dev only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

image_dir = "static/images"
app.mount("/static", StaticFiles(directory="static"), name="static")

def validate_pdf_file(file: UploadFile):
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded")
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Invalid file format. Only PDF files are allowed"
        )
    if file.content_type not in ["application/pdf"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only PDF files are allowed"
        )

@app.post("/process-pdf/")
async def process_pdf(file: UploadFile = File(...)):
    validate_pdf_file(file)
    try:
        original_filename = os.path.splitext(file.filename)[0]
        pdf_image_dir = os.path.join(image_dir, original_filename)

        if os.path.exists(pdf_image_dir):
            shutil.rmtree(pdf_image_dir)
        os.makedirs(pdf_image_dir)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_pdf_path = os.path.join(temp_dir, file.filename)
            with open(temp_pdf_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            # Step 3: Process PDF
            _, cleaned_lines, extracted_images = parse_pdf_and_extract_images(
                pdf_path=temp_pdf_path,
                output_txt_path=""
            )

            # Step 4: Process content
            text_content = "\n".join(cleaned_lines)
            result = process_content(text_content)

            # Step 5: Upload images to Supabase
            supabase_image_urls = []
            for img_path in extracted_images:
                dest_path = f"{original_filename}/{os.path.basename(img_path)}"
                public_url = upload_image_to_supabase(img_path, bucket="file-images", dest_path=dest_path)
                supabase_image_urls.append(public_url)

            # Step 6: Map filename -> Supabase URL
            supabase_image_map = {}
            for i, img_path in enumerate(extracted_images):
                filename = os.path.basename(img_path)
                supabase_image_map[filename] = supabase_image_urls[i]

            # Step 7: Replace <img src='images/...'> with public URLs
            def replace_img_paths(data: dict) -> dict:
                def process_item(item):
                    if isinstance(item, dict):
                        return {k: process_item(v) for k, v in item.items()}
                    elif isinstance(item, list):
                        return [process_item(i) for i in item]
                    elif isinstance(item, str):
                        matches = re.findall(r"<img src='images/([^']+)'>", item)
                        for filename in matches:
                            if filename in supabase_image_map:
                                item = item.replace(
                                    f"<img src='images/{filename}'>",
                                    supabase_image_map[filename]
                                )
                        return item
                    else:
                        return item
                return process_item(data)

            updated_result = replace_img_paths(result)
            result = {"topics": updated_result}
            de_dup_result = remove_duplicate_questions(result)

            return JSONResponse(content={
                "result": de_dup_result,
                "images": supabase_image_urls
            })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"An unexpected error occurred: {str(e)}"}
        )

def start():
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False
    )

if __name__ == "__main__":
    start()
