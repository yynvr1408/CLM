from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid
import shutil
from app.database.session import get_db
from app.models.models import Attachment, User
from app.schemas.schemas import AttachmentResponse
from app.api.v1.endpoints.auth import get_current_user, get_user_from_query_token
from app.core.config import settings

router = APIRouter()

UPLOAD_DIR = settings.UPLOAD_DIR or "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

@router.post("/upload", response_model=AttachmentResponse)
async def upload_file(
    file: UploadFile = File(...),
    contract_id: Optional[int] = None,
    clause_id: Optional[int] = None,
    template_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    """Upload a file and create an attachment record."""
    # Create unique filename to prevent collisions
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not save file: {str(e)}"
        )

    # Create DB record
    db_attachment = Attachment(
        filename=file.filename,
        file_path=file_path,
        file_type=file.content_type,
        file_size=os.path.getsize(file_path),
        contract_id=contract_id,
        clause_id=clause_id,
        template_id=template_id,
        uploaded_by_id=current_user.id
    )

    db.add(db_attachment)
    db.commit()
    db.refresh(db_attachment)

    return db_attachment

@router.get("/{attachment_id}", response_model=AttachmentResponse)
def get_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    """Get attachment metadata."""
    attachment = db.query(Attachment).filter(Attachment.id == attachment_id).first()
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")
    return attachment

@router.get("/download/{attachment_id}")
def download_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_user_from_query_token)
):
    """Download the actual physical file."""
    attachment = db.query(Attachment).filter(Attachment.id == attachment_id).first()
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")
        
    if not os.path.exists(attachment.file_path):
        raise HTTPException(status_code=404, detail="Physical file missing on server")
        
    return FileResponse(
        path=attachment.file_path,
        filename=attachment.filename,
        media_type=attachment.file_type
    )

@router.get("", response_model=dict)
def list_attachments(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all attachments in the system."""
    query = db.query(Attachment)
    total = query.count()
    attachments = query.order_by(Attachment.created_at.desc()).offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "items": [AttachmentResponse.model_validate(a) for a in attachments]
    }

@router.delete("/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    """Delete an attachment and its physical file."""
    attachment = db.query(Attachment).filter(Attachment.id == attachment_id).first()
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    # Remove physical file
    if os.path.exists(attachment.file_path):
        os.remove(attachment.file_path)

    db.delete(attachment)
    db.commit()
    return None
