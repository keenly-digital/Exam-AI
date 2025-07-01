from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import shutil
import os
import tempfile
import uvicorn
from pdf_content_extraction import parse_pdf_and_extract_images
from parse_pdf_into_json import process_content
from remove_duplicate_question import remove_duplicate_questions

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        # Create a temporary directory to store the uploaded PDF
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_pdf_path = os.path.join(temp_dir, file.filename)
            with open(temp_pdf_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            # Step 1: Process the PDF. This single function now handles text extraction
            # and image uploading, returning final, public Supabase URLs.
            _, cleaned_lines, supabase_image_urls = parse_pdf_and_extract_images(
                pdf_path=temp_pdf_path,
                output_txt_path=""
            )

            # Step 2: Process the cleaned text (which includes the final image URLs).
            text_content = "\n".join(cleaned_lines)
            result = process_content(text_content)
            
            # Step 3: De-duplicate questions.
            result_with_topics = {"topics": result}
            de_dup_result = remove_duplicate_questions(result_with_topics)

            # Step 4: Return the final result. No more processing is needed.
            return JSONResponse(content={
                "result": de_dup_result,
                "images": supabase_image_urls
            })
            
    except Exception as e:
        import traceback
        traceback.print_exc()
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