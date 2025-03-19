from app.services.perplexity import ask_perplexity
import tempfile
import sys
import os
import cv2
import numpy as np
import pytesseract
import PyPDF2
from pdf2image import convert_from_path
from pdf2image.exceptions import PDFInfoNotInstalledError

def process_authorization(authorization_request, patient_chart):
    system_instructions = """
    Be precise and concise. Here's what I want you to do:

    1. Extract the patient's healthcare plan, and the CPT codes and names which the doctor has requested authorization for.

    2. Based on the patient's healthcare plan, gather the specific criteria that must be met for that CPT code to be approved.

    3. Carefully read the patient's medical chart provided in the other PDFs.

    4. Compare and analyze whether patient's medical chart provided sufficient justification and meet the criteria you found in step 2.

    5. Provide your response in the following JSON format:
    {
    "cpt_codes": [
        {
        "code": "<CPT code>",
        "name": "<procedure name>",
        "approved": true/false,
        "justification": "<detailed justification with quotes from source documents>", 
        "confidence": 0.XX
        }
    ]
    }"""
    
    user_message = f"Here is the authorization request: {authorization_request}\n\nHere is the patient's medical chart: {patient_chart}.Extract the information from the authorization request. Only return the JSON response, nothing else. No other text or commentary. The JSON should have the cpt_codes, with each cpt_code having the code, name, approved, justification, and confidence."
    return ask_perplexity(system_instructions, user_message)

def extract_data_from_authorization_request(authorization_request):
    text = extract_text_from_pdf(authorization_request)
    system_instructions = """
    Be precise and concise. Extract the following information from the authorization request:

    1. Patient's full name
    2. Authorization ID number
    3. Medical insurance plan name
    4. Name of requesting doctor
    5. All CPT codes being requested for authorization

    Return the information in the following JSON format:
    {
        "patient_name": "<full name>",
        "authorization_id": "<auth id>", 
        "medical_plan": "<plan name>",
        "requesting_doctor": "<doctor name>",
        "cpt_codes": [
            {
                "code": "<CPT code>",
                "name": "<procedure name>"
            }
        ]
    }
    """
    user_message = f"Here is the authorization request: {text}. Extract the information from the authorization request. Only return the JSON response, nothing else. No other text or commentary. The JSON should have the keys patient_name, authorization_id, medical_plan, requesting_doctor, and cpt_codes."
    return ask_perplexity(system_instructions, user_message)

def extract_text_from_pdf(pdf_path):
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                images = convert_from_path(
                    pdf_path,
                    dpi=300,
                    output_folder=temp_dir,
                    fmt="png"
                )
            except PDFInfoNotInstalledError:
                print("Poppler not found. Please install poppler using:")
                if sys.platform.startswith('darwin'):
                    print("brew install poppler")
                elif sys.platform.startswith('linux'):
                    print("sudo apt-get install poppler-utils")
                else:
                    print("Download from: https://github.com/oschwartz10612/poppler-windows/releases/")
                print("\nFalling back to PyPDF2 (limited functionality)...")
                return fallback_extract_text(pdf_path)
            
            full_text = ""
            
            for i, image in enumerate(images):
                img = np.array(image)
                img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
                
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                
                try:
                    osd = pytesseract.image_to_osd(gray)
                    angle = int(osd.split("Rotate: ")[1].split("\n")[0])
                    
                    if angle != 0:
                        (h, w) = gray.shape
                        center = (w // 2, h // 2)
                        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
                        gray = cv2.warpAffine(gray, rotation_matrix, (w, h), 
                                            flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
                except Exception as e:
                    print(f"Warning: Could not determine orientation for page {i+1}: {e}")
                
                gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
                
                gray = cv2.medianBlur(gray, 3)
                
                try:
                    config = r'--oem 3 --psm 6'
                    text = pytesseract.image_to_string(gray, config=config)
                    full_text += text + "\n\n"
                except Exception as e:
                    print(f"Warning: OCR failed for page {i+1}: {e}")
                    print("Is Tesseract installed and in your PATH?")
                    full_text += "[OCR FAILED FOR THIS PAGE]\n\n"
            
            return full_text
    except Exception as e:
        print(f"Error during OCR processing: {e}")
        print("Falling back to PyPDF2...")
        return fallback_extract_text(pdf_path)

def fallback_extract_text(pdf_path):
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ''
            for page in pdf_reader.pages:
                text += page.extract_text() or "[NO TEXT EXTRACTED FROM THIS PAGE]\n"
                text += "\n\n"
        return text
    except Exception as e:
        print(f"PyPDF2 fallback also failed: {e}")
        return f"[FAILED TO EXTRACT TEXT FROM {pdf_path}]"