# app/schemas.py
from pydantic import BaseModel
from typing import Optional

# ---------- AUTH ----------

class LoginRequest(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- USER ----------

class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    roles: list[str] = []

    model_config = {
        "from_attributes": True
    }


# ---------- ROLE ----------

class RoleCreate(BaseModel):
    name: str
    description: Optional[str] = None


class RoleResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    model_config = {
        "from_attributes": True
    }


# ---------- PERMISSION ----------

class PermissionCreate(BaseModel):
    name: str
    description: Optional[str] = None


class PermissionResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    model_config = {
        "from_attributes": True
    }


# ---------- PDF ----------

# (Used earlier for mock PDF creation – can stay)
class PDFCreate(BaseModel):
    title: str
    description: Optional[str] = None


class PDFOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None

    model_config = {
        "from_attributes": True
    }


# ✅ NEW: Used for REAL PDF upload & listing
class PDFResponse(BaseModel):
    id: int
    title: str
    uploaded_by: int
    uploader_name: str
    uploader_role: str
    
    model_config = {
        "from_attributes": True
    }
