from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import shutil
import os
import tempfile
from pdf_content_extraction import parse_pdf_and_extract_images
from parse_pdf_into_json import TopicProcessor, process_content
import re
import uvicorn

app = FastAPI()

image_dir = "static/images"

# Mount the static directory (FastAPI serves images from here)
app.mount("/static", StaticFiles(directory="static"), name="static")

def validate_pdf_file(file: UploadFile):
    """Validate that the uploaded file is a PDF."""
    # Check if file was uploaded
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded")
    
    # Check file extension
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Invalid file format. Only PDF files are allowed"
        )
    
    # Check content type (MIME type)
    if file.content_type not in ["application/pdf"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only PDF files are allowed"
        )

@app.post("/process-pdf/")
async def process_pdf(file: UploadFile = File(...)):
    # ✅ Let FastAPI handle HTTPExceptions naturally
    validate_pdf_file(file)

    try:
        # ✅ Step 1: Clean image directory
        if os.path.exists(image_dir):
            shutil.rmtree(image_dir)
        os.makedirs(image_dir)

        # ✅ Step 2: Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_pdf_path = os.path.join(temp_dir, file.filename)
            with open(temp_pdf_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # ✅ Step 3: Process PDF
            _, cleaned_lines, extracted_images = parse_pdf_and_extract_images(
                pdf_path=temp_pdf_path,
                output_img_dir=image_dir,
                output_txt_path=""
            )

            # ✅ Step 4: Process content
            text_content = "\n".join(cleaned_lines)
            result = process_content(text_content)

            return JSONResponse(content={
                "topics": result,
                "images": [f"/static/images/{img}" for img in extracted_images]
            })

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"An unexpected error occurred: {str(e)}"}
        )

# Remove the `if __name__ == "__main__":` block and replace with:
def start():
    """Run the FastAPI app using Uvicorn programmatically."""
    port = int(os.getenv("PORT", 8000))  # Default to 8000 if PORT not set
    uvicorn.run(
        "api:app",  # Replace "main" with your filename if different
        host="0.0.0.0",
        port=port,
        reload=False  # Disable auto-reload in production
    )

if __name__ == "__main__":
    start()