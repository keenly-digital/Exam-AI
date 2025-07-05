import fitz
import os
from typing import Tuple, List, Dict


def is_integer(s: str) -> bool:
    try:
        return str(int(s)) == s
    except ValueError:
        return False


def clean_lines(lines: List[str]) -> List[str]:
    to_remove = set()
    n = len(lines)
    for i, line in enumerate(lines):
        if line.endswith(".COM") or "CERT MAGE" in line or "CERTEMPIRE.com" in line:
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


def remove_qna_pdf_lines(lines: List[str]) -> List[str]:
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


def ensure_directory_exists(directory: str) -> None:
    if not os.path.exists(directory):
        os.makedirs(directory)


def parse_pdf_and_extract_images(
    pdf_path: str,
    output_img_dir: str = "static/images",
    output_txt_path: str = "output.txt"
) -> Tuple[str, List[str], List[str]]:
    # Get base filename without extension
    base_filename = os.path.splitext(os.path.basename(pdf_path))[0]
    output_img_dir = os.path.join(output_img_dir, base_filename)
    ensure_directory_exists(output_img_dir)
    if not os.path.isabs(output_img_dir):
        ensure_directory_exists("static")

    doc = fitz.open(pdf_path)
    lines_with_placeholders = []
    extracted_images = []
    written_xrefs: Dict[int, str] = {}  # xref → filename mapping

    for page_index in range(len(doc)):
        page = doc[page_index]
        page_dict = page.get_text("dict")
        image_count = 0

        blocks = page_dict.get("blocks", [])
        blocks_sorted = sorted(
            blocks, key=lambda b: b.get("bbox", [0, 0, 0, 0])[1])

        for block in blocks_sorted:
            if "image" in block:
                image_obj = block["image"]
                image_count += 1
                # If dict, use xref and page-position-based filename
                if isinstance(image_obj, dict):
                    xref = image_obj.get("xref")
                    if xref is not None:
                        if xref not in written_xrefs:
                            try:
                                base_image = doc.extract_image(xref)
                                ext = base_image["ext"]
                                img_bytes = base_image["image"]
                                img_filename = f"page_{page_index + 1}_img_{image_count}.{ext}"
                                full_path = os.path.join(
                                    output_img_dir, img_filename)
                                with open(full_path, "wb") as f:
                                    f.write(img_bytes)
                                written_xrefs[xref] = img_filename
                                extracted_images.append(
                                    f"/static/images/{base_filename}/{img_filename}")
                            except Exception as e:
                                print(f"Error extracting image: {e}")
                                lines_with_placeholders.append(
                                    "<image could not be extracted>")
                                continue
                        img_filename = written_xrefs[xref]
                        lines_with_placeholders.append(
                            f"\n/static/images/{base_filename}/{img_filename}\n")
                    else:
                        lines_with_placeholders.append(
                            "<image could not be extracted>")
                elif isinstance(image_obj, bytes):
                    try:
                        img_filename = f"page_{page_index + 1}_img_{image_count}.jpg"
                        full_path = os.path.join(output_img_dir, img_filename)
                        with open(full_path, "wb") as f:
                            f.write(image_obj)
                        lines_with_placeholders.append(
                            f"\n/static/images/{base_filename}/{img_filename}\n")
                        extracted_images.append(
                            f"/static/images/{base_filename}/{img_filename}")
                    except Exception as e:
                        print(f"Error saving image: {e}")
                        lines_with_placeholders.append(
                            "<image could not be extracted>")
                else:
                    lines_with_placeholders.append(
                        "<image could not be extracted>")
            if "lines" in block:
                for line in block["lines"]:
                    text_line = "".join(span["text"]
                                        for span in line["spans"]).strip()
                    if text_line:
                        lines_with_placeholders.append(text_line)

    doc.close()
    cleaned_lines = clean_lines(lines_with_placeholders)
    cleaned_lines = remove_qna_pdf_lines(cleaned_lines)

    os.makedirs(os.path.dirname(output_txt_path) or ".", exist_ok=True)
    if output_txt_path:
        with open(output_txt_path, "w", encoding="utf-8") as txt_file:
            for line in cleaned_lines:
                txt_file.write(line + "\n")
    return output_txt_path, cleaned_lines, extracted_images

# Example usage:
# if __name__ == "__main__":
#     pdf_file = "your.pdf"
#     output_path, lines, images = parse_pdf_and_extract_images(
#         pdf_file,
#         output_img_dir="static/images",
#         output_txt_path="output.txt"
#     )
#     print(f"Processed {len(images)} images")
#     print(f"Text saved to: {output_path}")
