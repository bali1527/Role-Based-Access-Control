# app/pdfs.py

from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    File,
    Form,
    HTTPException
)
from sqlalchemy.orm import Session
from typing import List
import os
import shutil
from uuid import uuid4

from .database import get_db
from .models import PDF
from .auth import get_current_user
from .deps import require_permission
from .schemas import PDFResponse
from fastapi.responses import FileResponse
from .models import PDF, User, UserRole


router = APIRouter(prefix="/pdf", tags=["PDFs"])

# Directory where PDFs are stored
UPLOAD_DIR = "uploads/pdfs"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_pdf_with_user_info(pdf: PDF, db: Session):
    """Helper function to get PDF with uploader user info"""
    user = db.query(User).filter(User.id == pdf.uploaded_by).first()
    role = (
        db.query(UserRole)
        .filter(UserRole.user_id == user.id)
        .first()
    ) if user else None

    return {
        "id": pdf.id,
        "title": pdf.title,
        "uploaded_by": pdf.uploaded_by,
        "uploader_name": user.username if user else "Unknown",
        "uploader_role": role.role.name.upper() if role else "USER"
    }


# -------------------------------
# UPLOAD PDF (CREATE PERMISSION)
# -------------------------------
@router.post(
    "/upload",
    response_model=PDFResponse
)
def upload_pdf(
    title: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: bool = Depends(require_permission("CREATE"))
):
    """
    Upload a PDF file.
    Only users with CREATE permission can upload.
    """

    # Validate file type
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed"
        )

    # Create a unique filename
    unique_filename = f"{uuid4()}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    # Save file to disk
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Save metadata to database
    pdf = PDF(
        title=title,
        filename=unique_filename,
        uploaded_by=current_user.id
    )

    db.add(pdf)
    db.commit()
    db.refresh(pdf)

    return get_pdf_with_user_info(pdf, db)


# -------------------------------
# LIST PDFs (READ PERMISSION)
# -------------------------------
@router.get("/", response_model=List[PDFResponse])
def list_pdfs(
    db: Session = Depends(get_db),
    _: bool = Depends(require_permission("READ"))
):
    """List all PDFs - accessible to all users with READ permission"""
    pdfs = db.query(PDF).all()
    result = [get_pdf_with_user_info(pdf, db) for pdf in pdfs]
    return result


# -------------------------------
# READ PDF (GET METADATA)
# -------------------------------
@router.get(
    "/{pdf_id}",
    response_model=PDFResponse
)
def get_pdf(
    pdf_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(require_permission("READ"))
):
    """Get a single PDF metadata - requires READ permission"""
    pdf = db.query(PDF).filter(PDF.id == pdf_id).first()

    if not pdf:
        raise HTTPException(status_code=404, detail="PDF not found")

    return get_pdf_with_user_info(pdf, db)


# -------------------------------
# UPDATE PDF TITLE (UPDATE PERMISSION)
# -------------------------------
@router.put(
    "/{pdf_id}",
    response_model=PDFResponse
)
def update_pdf(
    pdf_id: int,
    title: str = Form(...),
    db: Session = Depends(get_db),
    _: bool = Depends(require_permission("UPDATE"))
):
    """
    Update PDF title.
    Requires UPDATE permission.
    """
    pdf = db.query(PDF).filter(PDF.id == pdf_id).first()

    if not pdf:
        raise HTTPException(status_code=404, detail="PDF not found")

    pdf.title = title
    db.commit()
    db.refresh(pdf)

    return get_pdf_with_user_info(pdf, db)


# -------------------------------
# DELETE PDF (DELETE PERMISSION)
# -------------------------------
@router.delete(
    "/{pdf_id}"
)
def delete_pdf(
    pdf_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(require_permission("DELETE")),
    current_user=Depends(get_current_user)
):
    """
    Delete a PDF.
    Requires DELETE permission (Super Admin only).
    """
    pdf = db.query(PDF).filter(PDF.id == pdf_id).first()

    if not pdf:
        raise HTTPException(status_code=404, detail="PDF not found")

    # Prevent users with the 'admin' role from deleting PDFs
    role_names = {ur.role.name for ur in current_user.roles}
    if "admin" in role_names:
        raise HTTPException(status_code=403, detail="Admins are not allowed to delete PDFs")

    # Remove file from disk
    file_path = os.path.join(UPLOAD_DIR, pdf.filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    # Remove DB record
    db.delete(pdf)
    db.commit()

    return {"message": "PDF deleted successfully"}


# -------------------------------
# DOWNLOAD PDF (READ PERMISSION)
# -------------------------------
@router.get("/{pdf_id}/download")
def download_pdf(
    pdf_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(require_permission("READ"))
):
    """Download a PDF file - requires READ permission"""
    pdf = db.query(PDF).filter(PDF.id == pdf_id).first()
    if not pdf:
        raise HTTPException(status_code=404, detail="PDF not found")

    file_path = os.path.join(UPLOAD_DIR, pdf.filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")

    return FileResponse(path=file_path, filename=pdf.filename, media_type='application/pdf')
