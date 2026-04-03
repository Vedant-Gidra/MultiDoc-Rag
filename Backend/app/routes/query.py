from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.models import User, get_db, FileMetadata
from app.services.rag_service import query_rag
from app.dependencies import get_current_user

router = APIRouter()


class QueryRequest(BaseModel):
    question: str
    file_id: str


@router.post("/query")
def query_pdf(
    request: QueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify that the file belongs to the current user
    file_metadata = db.query(FileMetadata).filter(
        FileMetadata.file_id == request.file_id,
        FileMetadata.user_id == current_user.id
    ).first()
    
    if not file_metadata:
        raise HTTPException(status_code=403, detail="File not found or access denied")
    
    response = query_rag(
        request.question,
        request.file_id,
        current_user.id,
        file_metadata.filename
    )

    return response