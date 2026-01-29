import pytesseract, cv2, numpy as np
from pdf2image import convert_from_path

def extract_text(file_path):
    text = ""
    pages = convert_from_path(file_path, dpi=300)
    for page in pages:
        img = cv2.cvtColor(np.array(page), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        text += pytesseract.image_to_string(gray)
    return text
