from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import shutil
import os
import tempfile
import json
import re
import uvicorn

from pdf_content_extraction import parse_pdf_and_extract_images
from parse_pdf_into_json import TopicProcessor, process_content
from remove_duplicate_question import remove_duplicate_questions

# Base directory for consistent file paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
IMAGE_BASE_DIR = os.path.join(STATIC_DIR, "images")

app = FastAPI()

# Mount static directory for image access
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def validate_pdf_file(file: UploadFile):
    """Validate that the uploaded file is a PDF."""
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded")
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400, detail="Invalid file format. Only PDF files are allowed")
    if file.content_type not in ["application/pdf"]:
        raise HTTPException(
            status_code=400, detail="Invalid file type. Only PDF files are allowed")


@app.post("/process-pdf/")
async def process_pdf(file: UploadFile = File(...)):
    validate_pdf_file(file)

    try:
        # Extract filename without extension
        original_filename = os.path.splitext(file.filename)[0]

        # Directory where this PDF's images will be saved
        pdf_image_dir = os.path.join(IMAGE_BASE_DIR, original_filename)

        # Clean or create the image directory
        if os.path.exists(pdf_image_dir):
            shutil.rmtree(pdf_image_dir)
        os.makedirs(pdf_image_dir, exist_ok=True)
        print(f"[INFO] Created image save directory at: {pdf_image_dir}")

        # Create a temporary file for the uploaded PDF
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_pdf_path = os.path.join(temp_dir, file.filename)
            with open(temp_pdf_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            # Process PDF: extract text and images
            _, cleaned_lines, extracted_images = parse_pdf_and_extract_images(
                pdf_path=temp_pdf_path,
                output_img_dir=pdf_image_dir,
                output_txt_path=""
            )

            # Join text content and process it
            text_content = "\n".join(cleaned_lines)
            result = process_content(text_content)

            # Convert to accessible static URLs
            full_image_paths = [
                f"/static/images/{original_filename}/{img}" for img in extracted_images]

            # Replace <img src='images/...'> tags with full paths
            def replace_img_paths(data: dict, images_list: list) -> dict:
                image_map = {os.path.basename(
                    path): path for path in images_list}

                def process_item(item):
                    if isinstance(item, dict):
                        return {k: process_item(v) for k, v in item.items()}
                    elif isinstance(item, list):
                        return [process_item(i) for i in item]
                    elif isinstance(item, str):
                        matches = re.findall(
                            r"<img src='images/([^']+)'>", item)
                        for filename in matches:
                            if filename in image_map:
                                item = item.replace(
                                    f"<img src='images/{filename}'>", image_map[filename])
                        return item
                    return item

                return process_item(data)

            updated_result = replace_img_paths(result, full_image_paths)
            result = {"topics": updated_result}
            de_dup_result = remove_duplicate_questions(result)

            return JSONResponse(content={
                "result": de_dup_result,
                "images": full_image_paths
            })

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"An unexpected error occurred: {str(e)}"}
        )


def start():
    """Run the FastAPI app using Uvicorn programmatically."""
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)


if __name__ == "__main__":
    start()
