import fitz
import os  # Needed for os.path functions
from typing import Tuple, List
from supabase_utils import supabase, BUCKET_NAME, SUPABASE_URL


# You must initialize these somewhere globally!
# from supabase import create_client, Client
# supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
# BUCKET_NAME = "file-images"
# SUPABASE_URL = "https://kxbjsyuhceggsyvxdkof.supabase.co"


def clean_lines(lines):
    """
    Refined logic:
    - Match lines with '.COM' or 'CERT MAGE'
    - Remove those lines and intelligently decide how many surrounding lines to remove
    """
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
    """
    Removes lines containing 'Questions and Answers PDF' and the next line.
    """
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
    """
    Parse PDF, upload images to Supabase, and store ONLY public URLs in output.
    """

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

                            # Save img_bytes temporarily to upload (Supabase Python SDK requires a file-like object)
                            # We'll use io.BytesIO for in-memory upload
                            import io
                            file_like = io.BytesIO(img_bytes)

                            # Upload to Supabase Storage (overwrite if exists)
                            res = supabase.storage.from_(BUCKET_NAME).upload(
                                file_path_in_bucket, file_like, {"content-type": f"image/{ext}", "upsert": True}
                            )
                            if res.get("error"):
                                raise Exception(res["error"]["message"])

                            # Get public URL (best practice is to use the SDK method)
                            public_url = supabase.storage.from_(BUCKET_NAME).get_public_url(file_path_in_bucket)
                            # Fallback: manually build if above doesn't work
                            if not public_url:
                                public_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{file_path_in_bucket}"

                            # **This is the ONLY thing you should store for the frontend/UI**
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

                        import io
                        file_like = io.BytesIO(image_obj)
                        res = supabase.storage.from_(BUCKET_NAME).upload(
                            file_path_in_bucket, file_like, {"content-type": "image/jpeg", "upsert": True}
                        )
                        if res.get("error"):
                            raise Exception(res["error"]["message"])

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

    # Clean the lines as usual (this step is unchanged)
    cleaned_lines = clean_lines(lines_with_placeholders)
    cleaned_lines = remove_qna_pdf_lines(cleaned_lines)

    # Save cleaned text if needed
    if output_txt_path:
        with open(output_txt_path, "w", encoding="utf-8") as txt_file:
            for line in cleaned_lines:
                txt_file.write(line + "\n")

    return output_txt_path, cleaned_lines, extracted_images




# if __name__ == "__main__":
#     pdf_file = "/Users/dev/Documents/pdf_parser_final/docs/Cert-Empire-CISSP-Exam-Demo-PDF.pdf"
#     output_path, lines, images = parse_pdf_and_extract_images(
#         pdf_file,
#         output_img_dir="static/images",
#         output_txt_path="cleaned_text_CISSP.txt"
#     )
#     print(f"Processed {len(images)} images")
#     print(f"Text saved to: {output_path}")
