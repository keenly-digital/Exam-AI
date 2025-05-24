import fitz
import os
from typing import Tuple, List
import shutil

def is_integer(s: str) -> bool:
    try:
        return str(int(s)) == s
    except ValueError:
        return False

def clean_lines(lines: List[str]) -> List[str]:
    """
    Refined logic:
    - Match lines with '.COM' or 'CERT MAGE'
    - Remove those lines and intelligently decide how many surrounding lines to remove
    """
    to_remove = set()
    n = len(lines)

    for i, line in enumerate(lines):
        if line.endswith(".COM") or "CERT MAGE" in line:
            match_idx = i
            to_remove.add(match_idx)
            # breakpoint()
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
    """
    Removes lines containing 'Questions and Answers PDF' and the next line.
    
    Args:
        lines: List of strings (text lines from a document)
    
    Returns:
        Filtered list with the target line and the next line removed
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

def ensure_directory_exists(directory: str) -> None:
    """Create directory if it doesn't exist."""
    if not os.path.exists(directory):
        os.makedirs(directory)

def parse_pdf_and_extract_images(
    pdf_path: str,
    output_img_dir: str = "static/images",
    output_txt_path: str = "extracted_text.txt"
) -> Tuple[str, List[str], List[str]]:
    """
    Parses the PDF and returns both the output path and extracted lines.
    
    Args:
        pdf_path: Path to the PDF file
        output_img_dir: Directory to save extracted images
        output_txt_path: Path to save extracted text
        
    Returns:
        Tuple containing:
        - Path to the output text file
        - List of extracted and cleaned text lines
        - List of extracted image paths
    """
    # Ensure the image directory exists
    ensure_directory_exists(output_img_dir)
    
    # Create static directory if using relative paths
    if not os.path.isabs(output_img_dir):
        ensure_directory_exists("static")
    
    doc = fitz.open(pdf_path)
    lines_with_placeholders = []
    extracted_images = []

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
                            full_path = os.path.join(output_img_dir, img_filename)
                            
                            # Save the image
                            with open(full_path, "wb") as f:
                                f.write(img_bytes)
                            
                            # Store relative path for web access
                            relative_path = os.path.join("images", img_filename)
                            lines_with_placeholders.append(f"<img src='{relative_path}'>")
                            extracted_images.append(relative_path)
                        except Exception as e:
                            print(f"Error extracting image: {e}")
                            lines_with_placeholders.append("<image could not be extracted>")
                    else:
                        lines_with_placeholders.append("<image could not be extracted>")

                elif isinstance(image_obj, bytes):
                    try:
                        img_filename = f"page_{page_index + 1}_img_{image_count}.jpg"
                        full_path = os.path.join(output_img_dir, img_filename)
                        with open(full_path, "wb") as f:
                            f.write(image_obj)
                        
                        # Store relative path for web access
                        relative_path = os.path.join("images", img_filename)
                        lines_with_placeholders.append(f"<img src='{relative_path}'>")
                        extracted_images.append(relative_path)
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

    # Apply post-filtering rules
    cleaned_lines = clean_lines(lines_with_placeholders)
    cleaned_lines = remove_qna_pdf_lines(cleaned_lines)

    # Write to file if path is provided
    if output_txt_path:
        with open(output_txt_path, "w", encoding="utf-8") as txt_file:
            for line in cleaned_lines:
                txt_file.write(line + "\n")

    return output_txt_path, cleaned_lines, extracted_images

# if __name__ == "__main__":
#     pdf_file = "docs/MB-820 Dumps.pdf"
#     output_path, lines, images = parse_pdf_and_extract_images(
#         pdf_file,
#         output_img_dir="static/images",
#         output_txt_path="cleaned_text_CISSP.txt"
#     )
#     print(f"Processed {len(images)} images")
#     print(f"Text saved to: {output_path}")
