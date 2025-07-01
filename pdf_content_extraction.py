import fitz
import os
from typing import Tuple, List
from supabase_utils import supabase, BUCKET_NAME, SUPABASE_URL

def clean_lines(lines):
    """Removes header/footer lines from the document."""
    to_remove = set()
    n = len(lines)
    def is_integer(s):
        try:
            return str(int(s)) == s
        except ValueError:
            return False
    for i, line in enumerate(lines):
        if line.endswith(".COM") or "CERT MAGE" in line:
            match_idx = i
            to_remove.add(match_idx)
            prev = lines[i - 1] if i - 1 >= 0 else ""
            next_ = lines[i + 1] if i + 1 < n else ""
            next2 = lines[i + 2] if i + 2 < n else ""
            if is_integer(prev):
                to_remove.update(range(max(0, i - 3), i))
            elif is_integer(next_):
                if not is_integer(next2) and "Exam Dumps" not in next2:
                    to_remove.update([i + 1, i + 2])
                else:
                    to_remove.update(range(i + 1, min(n, i + 4)))
            elif "Exam Dumps" in prev:
                to_remove.update(range(max(0, i - 2), i))
            elif "Exam Dumps" in next_:
                to_remove.update(range(i + 1, min(n, i + 3)))
    return [line for idx, line in enumerate(lines) if idx not in to_remove]

def remove_qna_pdf_lines(lines):
    """Removes 'Questions and Answers PDF' lines."""
    filtered_lines = []
    skip_next = False
    for line in lines:
        if skip_next:
            skip_next = False
            continue
        if 'Questions and Answers PDF' in line:
            skip_next = True
            continue
        filtered_lines.append(line)
    return filtered_lines

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

                if isinstance(image_obj, dict):
                    xref = image_obj.get("xref")
                    if xref is not None:
                        try:
                            base_image = doc.extract_image(xref)
                            ext = base_image["ext"]
                            img_bytes = base_image["image"]
                            img_filename = f"page_{page_index + 1}_img_{image_count}.{ext}"
                            file_path_in_bucket = f"{pdf_base_name}/{img_filename}"
                            
                            res = supabase.storage.from_(BUCKET_NAME).upload(
                                file_path_in_bucket, img_bytes, {"content-type": f"image/{ext}", "upsert": "true"}
                            )
                            
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
                
                elif isinstance(image_obj, bytes):
                    try:
                        img_filename = f"page_{page_index + 1}_img_{image_count}.jpg"
                        file_path_in_bucket = f"{pdf_base_name}/{img_filename}"
                        
                        res = supabase.storage.from_(BUCKET_NAME).upload(
                            file_path_in_bucket, image_obj, {"content-type": "image/jpeg", "upsert": "true"}
                        )
                        
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

            if "lines" in block:
                for line in block["lines"]:
                    text_line = "".join(span["text"] for span in line["spans"]).strip()
                    if text_line:
                        lines_with_placeholders.append(text_line)

    doc.close()

    # The helper functions are now defined above, so these calls will work.
    cleaned_lines = clean_lines(lines_with_placeholders)
    cleaned_lines = remove_qna_pdf_lines(cleaned_lines)

    if output_txt_path:
        with open(output_txt_path, "w", encoding="utf-8") as txt_file:
            for line in cleaned_lines:
                txt_file.write(line + "\n")

    return output_txt_path, cleaned_lines, extracted_images