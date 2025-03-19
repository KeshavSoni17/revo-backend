from fastapi import APIRouter
from app.services.utils import extract_data_from_authorization_request, process_authorization
from fastapi import File, UploadFile
import tempfile
import os
import json
router = APIRouter()


@router.post("/extract_data_from_authorization")
async def extract_authorization_data(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
        temp_file.write(await file.read())
        temp_file_path = temp_file.name
    
    try:
        message, references = extract_data_from_authorization_request(temp_file_path)
        print(message)
        return json.loads(message)
    finally:
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

@router.post("/process_authorization_request")
async def process_authorization_request(
    authorization_request: str,
    files: list[UploadFile] = File(...)
):
    temp_file_paths = []
    
    try:
        
        for file in files:
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
                temp_file.write(await file.read())
                temp_file_paths.append(temp_file.name)
        
        message, references = process_authorization(authorization_request, temp_file_paths)
        return json.loads(message)
    
    finally:
        for temp_path in temp_file_paths:
            if os.path.exists(temp_path):
                os.unlink(temp_path)