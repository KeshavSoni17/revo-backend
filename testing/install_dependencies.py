import subprocess
import sys

def install_dependencies():
    """Install all required dependencies for the PDF text extraction system."""
    dependencies = [
        "requests",
        "PyPDF2",  # Keep for compatibility
        "pdf2image",
        "pytesseract",
        "numpy",
        "opencv-python",
        "Pillow",
    ]
    
    print("Installing required Python packages...")
    for package in dependencies:
        print(f"Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    
    print("\nPython dependencies installed successfully.")
    
    # Check if tesseract is installed
    try:
        result = subprocess.run(["tesseract", "--version"], 
                                capture_output=True, 
                                text=True)
        print("Tesseract already installed:")
        print(result.stdout.split("\n")[0])
    except FileNotFoundError:
        print("\nIMPORTANT: You need to install Tesseract OCR on your system:")
        print("- On macOS: brew install tesseract")
        print("- On Ubuntu/Debian: sudo apt-get install tesseract-ocr")
        print("- On Windows: Download and install from https://github.com/UB-Mannheim/tesseract/wiki")
    
    # Check if poppler is installed (required by pdf2image)
    try:
        # Different command based on OS
        if sys.platform.startswith('win'):
            # On Windows, we just check if the package is installed
            import pdf2image
            print("pdf2image installed, which requires poppler.")
            print("If you encounter errors, install poppler from: https://github.com/oschwartz10612/poppler-windows/releases/")
        else:
            # On Unix-like systems, we can check for pdftoppm
            result = subprocess.run(["pdftoppm", "-v"], 
                                    capture_output=True, 
                                    text=True)
            print("Poppler already installed.")
    except (FileNotFoundError, ImportError):
        print("\nIMPORTANT: You need to install poppler on your system (required by pdf2image):")
        print("- On macOS: brew install poppler")
        print("- On Ubuntu/Debian: sudo apt-get install poppler-utils")
        print("- On Windows: Download and install from https://github.com/oschwartz10612/poppler-windows/releases/")

if __name__ == "__main__":
    install_dependencies() 