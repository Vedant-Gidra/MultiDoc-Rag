import os
import uuid
from sqlalchemy.orm import Session
from app.models import FileMetadata
from rag.vectorstore import load_vectorstore

UPLOAD_DIR = "storage"


def save_file(file, user_id: int, db: Session):
    """Save a file to user-specific directory."""
    file_id = str(uuid.uuid4())
    filename = file.filename
    
    # Create user-specific directory
    user_dir = os.path.join(UPLOAD_DIR, str(user_id))
    os.makedirs(user_dir, exist_ok=True)
    
    file_path = os.path.join(user_dir, f"{file_id}.pdf")
    
    with open(file_path, "wb") as f:
        f.write(file.file.read())
    
    # Save metadata to database
    file_metadata = FileMetadata(
        user_id=user_id,
        filename=filename,
        file_id=file_id
    )
    db.add(file_metadata)
    db.commit()
    db.refresh(file_metadata)
    
    return file_id, file_path


def get_user_files(user_id: int, db: Session):
    """Get all files for a user."""
    files = db.query(FileMetadata).filter(FileMetadata.user_id == user_id).all()
    return [
        {
            "id": f.id,
            "file_id": f.file_id,
            "filename": f.filename,
            "created_at": f.created_at
        }
        for f in files
    ]


def get_file_path(user_id: int, file_id: str, db: Session):
    """Get the actual file path for a user's file."""
    file_metadata = db.query(FileMetadata).filter(
        FileMetadata.user_id == user_id,
        FileMetadata.file_id == file_id
    ).first()
    
    if not file_metadata:
        return None
    
    return os.path.join(UPLOAD_DIR, str(user_id), f"{file_id}.pdf")


def delete_user_file(user_id: int, file_id: str, db: Session):
    """Delete a user's file and its metadata."""
    file_metadata = db.query(FileMetadata).filter(
        FileMetadata.user_id == user_id,
        FileMetadata.file_id == file_id
    ).first()

    if not file_metadata:
        return False

    # Remove vectorstore docs for this file_id
    try:
        vectorstore = load_vectorstore(user_id=user_id)
        vectorstore.delete(where={"file_id": file_id})
    except Exception:
        # If not possible, continue removal of file/metadata anyway
        pass

    # Delete on-disk file
    file_path = os.path.join(UPLOAD_DIR, str(user_id), f"{file_id}.pdf")
    if os.path.exists(file_path):
        os.remove(file_path)

    # Clean up metadata
    db.delete(file_metadata)
    db.commit()

    # Optionally, cleanup empty user folder
    user_dir = os.path.join(UPLOAD_DIR, str(user_id))
    try:
        if os.path.isdir(user_dir) and not os.listdir(user_dir):
            os.rmdir(user_dir)
    except Exception:
        pass

    return True