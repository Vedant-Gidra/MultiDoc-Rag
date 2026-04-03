from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models import User, get_db
from app.services.file_service import get_user_files, delete_user_file
from app.dependencies import get_current_user

router = APIRouter()


@router.get("/files")
def get_files(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all files for the current user."""
    files = get_user_files(current_user.id, db)
    return {"files": files}


@router.delete("/files/{file_id}")
def remove_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a user file and its metadata"""
    success = delete_user_file(current_user.id, file_id, db)
    if not success:
        raise HTTPException(status_code=404, detail="File not found")
    return {"message": "File deleted successfully", "file_id": file_id}