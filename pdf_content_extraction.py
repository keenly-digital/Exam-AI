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
            to_remove.add(i)
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

def parse_pdf_and_extract_images(pdf_path: str, output_txt_path: str = "") -> Tuple[List[str], dict]:
    """
    Parses PDF, uploads images to Supabase, and returns text with placeholders and a map of placeholders to URLs.
    """
    doc = fitz.open(pdf_path)
    lines_with_placeholders = []
    placeholder_map = {}
    image_placeholder_counter = 0
    pdf_base_name = os.path.splitext(os.path.basename(pdf_path))[0].replace(" ", "_")

    for page_index in range(1, len(doc)):
        page = doc[page_index]
        page_dict = page.get_text("dict")
        
        for block in page_dict["blocks"]:
            if "image" in block:
                try:
                    img_bytes, ext = None, "jpg"
                    if isinstance(block["image"], dict) and block["image"].get("xref"):
                        base_image = doc.extract_image(block["image"]["xref"])
                        img_bytes, ext = base_image["image"], base_image["ext"]
                    elif isinstance(block["image"], bytes):
                        img_bytes = block["image"]

                    if img_bytes:
                        placeholder = f"%%IMAGE_{image_placeholder_counter}%%"
                        img_filename = f"page_{page_index + 1}_img_{image_placeholder_counter}.{ext}"
                        file_path_in_bucket = f"{pdf_base_name}/{img_filename}"
                        
                        supabase.storage.from_(BUCKET_NAME).upload(
                            file_path_in_bucket, img_bytes, {"content-type": f"image/{ext}", "upsert": "true"}
                        )
                        
                        public_url = supabase.storage.from_(BUCKET_NAME).get_public_url(file_path_in_bucket)
                        placeholder_map[placeholder] = public_url
                        lines_with_placeholders.append(placeholder)
                        image_placeholder_counter += 1
                    else:
                        lines_with_placeholders.append("<image could not be extracted>")
                except Exception as e:
                    print(f"Error processing image: {e}")
                    lines_with_placeholders.append("<image could not be extracted>")

            elif "lines" in block:
                for line in block["lines"]:
                    text_line = "".join(span["text"] for span in line["spans"]).strip()
                    if text_line:
                        lines_with_placeholders.append(text_line)

    doc.close()
    cleaned_lines = clean_lines(lines_with_placeholders)
    cleaned_lines = remove_qna_pdf_lines(cleaned_lines)
    return cleaned_lines, placeholder_map