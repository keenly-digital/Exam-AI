import fitz
import os
from typing import Tuple, List
from supabase_utils import supabase, BUCKET_NAME, SUPABASE_URL

def parse_pdf_and_extract_images(
    pdf_path: str,
    output_txt_path: str = "extracted_text.txt"
) -> Tuple[str, List[str], List[str]]:
    doc = fitz.open(pdf_path)
    lines_with_placeholders = []
    extracted_images = []
    pdf_base_name = os.path.splitext(os.path.basename(pdf_path))[0]

    for page_index in range(1, len(doc)):  # Skip first and last pages
        page = doc[page_index]
        page_dict = page.get_text("dict")
        image_count = 0

        for block in page_dict["blocks"]:
            if "image" in block:
                image_obj = block["image"]
                image_count += 1

                # Handle images as dict (most cases)
                if isinstance(image_obj, dict):
                    xref = image_obj.get("xref")
                    if xref is not None:
                        try:
                            base_image = doc.extract_image(xref)
                            ext = base_image["ext"]
                            img_bytes = base_image["image"]
                            img_filename = f"page_{page_index + 1}_img_{image_count}.{ext}"
                            file_path_in_bucket = f"{pdf_base_name}/{img_filename}"

                            # FIX: Pass raw bytes to .upload() and use "true" for upsert
                            res = supabase.storage.from_(BUCKET_NAME).upload(
                                file_path_in_bucket, img_bytes, {"content-type": f"image/{ext}", "upsert": "true"}
                            )

                            # FIX: The .get("error") check is removed, as errors are now exceptions.
                            
                            public_url = supabase.storage.from_(BUCKET_NAME).get_public_url(file_path_in_bucket)
                            if not public_url:
                                public_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{file_path_in_bucket}"
                            lines_with_placeholders.append(public_url)
                            extracted_images.append(public_url)

                        except Exception as e:
                            print(f"Error extracting image: {e}")
                            lines_with_placeholders.append("<image could not be extracted>")
                    else:
                        lines_with_placeholders.append("<image could not be extracted>")
                
                # Handle images as bytes (rare case)
                elif isinstance(image_obj, bytes):
                    try:
                        img_filename = f"page_{page_index + 1}_img_{image_count}.jpg"
                        file_path_in_bucket = f"{pdf_base_name}/{img_filename}"
                        
                        # FIX: Pass raw bytes to .upload() and use "true" for upsert
                        res = supabase.storage.from_(BUCKET_NAME).upload(
                            file_path_in_bucket, image_obj, {"content-type": "image/jpeg", "upsert": "true"}
                        )
                        
                        # FIX: The .get("error") check is removed.

                        public_url = supabase.storage.from_(BUCKET_NAME).get_public_url(file_path_in_bucket)
                        if not public_url:
                            public_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{file_path_in_bucket}"
                        lines_with_placeholders.append(public_url)
                        extracted_images.append(public_url)

                    except Exception as e:
                        print(f"Error saving image: {e}")
                        lines_with_placeholders.append("<image could not be extracted>")
                else:
                    lines_with_placeholders.append("<image could not be extracted>")

            # Normal text block
            if "lines" in block:
                for line in block["lines"]:
                    text_line = "".join(span["text"] for span in line["spans"]).strip()
                    if text_line:
                        lines_with_placeholders.append(text_line)

    doc.close()
    cleaned_lines = clean_lines(lines_with_placeholders)
    cleaned_lines = remove_qna_pdf_lines(cleaned_lines)

    if output_txt_path:
        with open(output_txt_path, "w", encoding="utf-8") as txt_file:
            for line in cleaned_lines:
                txt_file.write(line + "\n")

    return output_txt_path, cleaned_lines, extracted_images