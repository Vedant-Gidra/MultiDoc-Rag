from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session
from app.models import User, get_db
from app.services.file_service import save_file
from app.services.vector_service import process_and_store
from app.dependencies import get_current_user

router = APIRouter()


@router.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    file_id, file_path = save_file(file, current_user.id, db)
    
    process_and_store(file_path, file_id, current_user.id, filename=file.filename)
    
    return {
        "message": "File uploaded successfully",
        "file_id": file_id,
        "filename": file.filename
    }