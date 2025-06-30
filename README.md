# PDF Parser API

This is a FastAPI-based service that provides endpoints for parsing PDF files and extracting their content including text and images.

## Features

- PDF text content extraction
- PDF image extraction
- Content processing and topic organization
- Static file serving for extracted images

## Prerequisites

- Python 3.11 or higher
- pip (Python package installer)

## Installation

1. Create a virtual environment (recommended):
```bash
python -m venv env
source env/bin/activate  # On Windows use: env\Scripts\activate
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Running the Server

3. Start the server using uvicorn:

```bash
python api.py

```

The server will start and listen on `http://localhost:8000`.

## API Endpoints

### Upload and Parse PDF

**Endpoint:** `POST /upload-pdf/`

This endpoint accepts a PDF file upload and returns the parsed content along with any extracted images.

**Request:**
- Method: POST
- Content-Type: multipart/form-data
- Body parameter: `file` (PDF file)

**Response:**
- Status: 200 OK
- Content-Type: application/json
- Body: JSON object containing parsed content and image references

### Static Files

Extracted images are served from the `/static/images/` directory and can be accessed via the URL pattern:
`http://localhost:8000/static/images/{image_filename}`

## Project Structure

- `api.py` - Main FastAPI application and endpoint definitions
- `pdf_content_extraction.py` - PDF parsing and image extraction logic
- `parse_pdf_into_json.py` - Content processing and topic organization
- `static/images/` - Directory for storing extracted images
- `requirements.txt` - Python package dependencies

## Error Handling

The API includes validation for:
- File presence in request
- PDF file format validation
- File processing errors

## Dependencies

- FastAPI (0.104.1) - Web framework for building APIs
- Uvicorn (0.24.0) - ASGI server implementation
- PyMuPDF (1.23.7) - PDF processing library
- Python-multipart (0.0.6) - Multipart form data parsing
- Pydantic (2.5.2) - Data validation
- Starlette (0.27.0) - ASGI framework
- Typing-extensions (4.8.0) - Type hinting support

## Image Handling (Updated)

- Extracted images are uploaded to **Supabase Storage** in the bucket you specify.
- API responses now return the full **Supabase public URL** for each extracted image.
- Example:  
  `https://kxbjsyuhceggsyvxdkof.supabase.co/storage/v1/object/public/file-images/TDA-C01 - Tableau Certified Data Analyst/page_3_img_1.jpg`
- **No local static files are served** from `/static/images/` anymore.