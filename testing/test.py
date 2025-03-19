import requests
import json
import PyPDF2
import os
import tempfile
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
import numpy as np
import cv2
import sys
import subprocess
from pdf2image.exceptions import PDFInfoNotInstalledError

def ask_perplexity(message):
    url = "https://api.perplexity.ai/chat/completions"
    api_key = "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"
    payload = {
        "model": "sonar-pro", 
        "messages": [
            {
                "role": "system",
                "content": "Be precise and concise. Here's what I want you to do:\n\n1. Extract the patient's healthcare plan, and the CPT codes and names which the doctor has requested authorization for.\n2. Based on the patient's healthcare plan, gather the specific criteria that must be met for that CPT code to be approved.\n3. Carefully read the patient's medical chart provided in the other PDFs.\n4. Compare and analyze whether patient's medical chart provided sufficient justification and meet the criteria you found in step 2.\n5. Provide your response in the following JSON format:\n{\n  \"cpt_codes\": [\n    {\n      \"code\": \"<CPT code>\",\n      \"name\": \"<procedure name>\", \n      \"approved\": true/false,\n      \"justification\": \"<detailed justification with quotes from source documents>\",\n      \"confidence\": 0.XX\n    }\n  ]\n}"
            },
            {
                "role": "user", 
                "content": message
            }
        ],
        "max_tokens": 123,
        "temperature": 0.2,
        "top_p": 0.9,
        "search_domain_filter": None,
        "return_images": False,
        "return_related_questions": False,
        "search_recency_filter": "month",
        "top_k": 0,
        "stream": False,
        "presence_penalty": 0,
        "frequency_penalty": 1,
        "response_format": None
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    response = requests.request("POST", url, json=payload, headers=headers)
    response_json = json.loads(response.text)
    
    message_content = response_json["choices"][0]["message"]["content"]
    citations = response_json["citations"]
    
    return message_content, citations

def process_authorization(authorization_request, patient_chart):
    response = ask_perplexity(f"Here is the authorization request: {authorization_request}\n\nHere is the patient's medical chart: {patient_chart}")
    return response

def extract_text_from_pdf(pdf_path):
    """
    Extract text from PDF using pytesseract OCR with preprocessing for better accuracy.
    Converts PDF to images, corrects orientation, and performs OCR.
    Falls back to PyPDF2 if poppler is not installed.
    """
    try:
        # Create a temporary directory to store the images
        with tempfile.TemporaryDirectory() as temp_dir:
            # Convert PDF to images
            try:
                images = convert_from_path(
                    pdf_path, 
                    dpi=300,  # Higher DPI for better quality
                    output_folder=temp_dir,
                    fmt="png"
                )
            except PDFInfoNotInstalledError:
                print("Poppler not found. Please install poppler using:")
                if sys.platform.startswith('darwin'):  # macOS
                    print("brew install poppler")
                elif sys.platform.startswith('linux'):
                    print("sudo apt-get install poppler-utils")
                else:  # Windows
                    print("Download from: https://github.com/oschwartz10612/poppler-windows/releases/")
                print("\nFalling back to PyPDF2 (limited functionality)...")
                return fallback_extract_text(pdf_path)
            
            full_text = ""
            
            for i, image in enumerate(images):
                # Convert PIL image to OpenCV format
                img = np.array(image)
                img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
                
                # Convert to grayscale
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                
                # Check orientation and rotate if needed
                try:
                    osd = pytesseract.image_to_osd(gray)
                    angle = int(osd.split("Rotate: ")[1].split("\n")[0])
                    
                    # Rotate if needed
                    if angle != 0:
                        (h, w) = gray.shape
                        center = (w // 2, h // 2)
                        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
                        gray = cv2.warpAffine(gray, rotation_matrix, (w, h), 
                                            flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
                except Exception as e:
                    print(f"Warning: Could not determine orientation for page {i+1}: {e}")
                    # Continue without rotation
                
                # Apply thresholding to clean up the image
                gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
                
                # Optional: Apply some noise reduction
                gray = cv2.medianBlur(gray, 3)
                
                # Perform OCR on the processed image
                try:
                    config = r'--oem 3 --psm 6'  # OCR Engine Mode 3 = Legacy + LSTM, Page Segmentation Mode 6 = Assume a single uniform block of text
                    text = pytesseract.image_to_string(gray, config=config)
                    full_text += text + "\n\n"
                except Exception as e:
                    print(f"Warning: OCR failed for page {i+1}: {e}")
                    print("Is Tesseract installed and in your PATH?")
                    # Try a different approach or continue with empty text
                    full_text += "[OCR FAILED FOR THIS PAGE]\n\n"
            
            return full_text
    except Exception as e:
        print(f"Error during OCR processing: {e}")
        print("Falling back to PyPDF2...")
        return fallback_extract_text(pdf_path)

def fallback_extract_text(pdf_path):
    """Fallback method using PyPDF2 when OCR processing fails"""
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

def install_poppler():
    """Attempt to install poppler based on the operating system"""
    try:
        print("Attempting to install poppler...")
        if sys.platform.startswith('darwin'):  # macOS
            subprocess.check_call(["brew", "install", "poppler"])
            print("Poppler installed successfully via Homebrew")
            return True
        elif sys.platform.startswith('linux'):
            subprocess.check_call(["sudo", "apt-get", "install", "-y", "poppler-utils"])
            print("Poppler installed successfully via apt")
            return True
        else:
            print("Automatic installation not supported on this platform.")
            print("Please install poppler manually:")
            print("- Windows: https://github.com/oschwartz10612/poppler-windows/releases/")
            print("- macOS: brew install poppler")
            print("- Linux: sudo apt-get install poppler-utils")
            return False
    except Exception as e:
        print(f"Failed to install poppler: {e}")
        return False

def check_and_install_dependencies():
    """Check if required dependencies are installed and try to install them if needed"""
    # Check if tesseract is installed
    try:
        subprocess.run(["tesseract", "--version"], capture_output=True, check=True)
        print("✅ Tesseract is installed")
    except (subprocess.SubprocessError, FileNotFoundError):
        print("❌ Tesseract is not installed")
        if sys.platform.startswith('darwin'):
            print("Installing Tesseract via Homebrew...")
            try:
                subprocess.check_call(["brew", "install", "tesseract"])
                print("✅ Tesseract installed successfully")
            except Exception as e:
                print(f"Failed to install Tesseract: {e}")
                print("Please install manually: brew install tesseract")
    
    # Check if poppler is installed
    try:
        if sys.platform.startswith('win'):
            # On Windows, check if PDF to image conversion works
            test_conversion = convert_from_path(pdf_path, dpi=72, first_page=1, last_page=1)
            print("✅ Poppler is installed")
        else:
            # On Unix-like systems
            subprocess.run(["pdftoppm", "-v"], capture_output=True, check=True)
            print("✅ Poppler is installed")
    except Exception:
        print("❌ Poppler is not installed")
        install_poppler()

# Example usage
if __name__ == "__main__":
    # Optional: Check and install dependencies
    # check_and_install_dependencies()
    
    pdf_path = "/Users/keshavsoni/Halo Medical Solutions Inc./Revo/revo-backend/dataset/approved/25031802710313600006/charts/PrintPage.aspx.pdf"
    print(extract_text_from_pdf(pdf_path))