from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from pathlib import Path

from app.database import get_db, engine, Base
from app.models import User, Role, Permission, UserRole, RolePermission
from app.auth import get_current_user, create_access_token
from app.schemas import UserCreate, UserResponse, RoleCreate, PermissionCreate, LoginRequest, Token
from app.deps import require_permission
from app.pdfs import router as pdfs_router

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="RBAC API",
    description="Role-Based Access Control API",
    version="1.0.0"
)

#  CORS MIDDLEWARE (ADDED)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow frontend access (OK for learning)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(pdfs_router, prefix="/api", tags=["PDFs"])

# Serve frontend static files - use absolute path
frontend_path = Path(__file__).parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")


# Redirect root to the frontend index
@app.get("/", include_in_schema=False)
def root_html():
    return RedirectResponse(url="/static/index.html")

# Health check endpoint
@app.get("/health", tags=["Health"])
def health_check():
    """Check API health status"""

    return {"status": "healthy"}

# Note: root is redirected to the frontend index (see above)

# Initialize default roles and permissions
@app.post("/init", tags=["Init"], include_in_schema=False)
def initialize_db(db: Session = Depends(get_db)):
    """Initialize database with default roles, permissions, and demo users (one-time setup)"""

    # Create roles if they don't exist
    roles_data = [
        {"name": "user", "description": "Basic user"},
        {"name": "admin", "description": "Admin user"},
        {"name": "super_admin", "description": "Super admin"},
    ]

    roles = {}
    for role_data in roles_data:
        role = db.query(Role).filter(Role.name == role_data["name"]).first()
        if not role:
            role = Role(name=role_data["name"], description=role_data["description"])
            db.add(role)
            db.commit()
        roles[role_data["name"]] = role
    
    # Create permissions if they don't exist
    perms_data = [
        {"name": "CREATE", "description": "Create PDFs"},
        {"name": "READ", "description": "Read PDFs"},
        {"name": "UPDATE", "description": "Update PDFs"},
        {"name": "DELETE", "description": "Delete PDFs"},
    ]
    
    perms = {}
    for perm_data in perms_data:
        perm = db.query(Permission).filter(Permission.name == perm_data["name"]).first()
        if not perm:
            perm = Permission(name=perm_data["name"], description=perm_data["description"])
            db.add(perm)
            db.commit()
        perms[perm_data["name"]] = perm
    
    # Assign permissions to roles
    def assign_perm(role_name, perm_names):
        role = roles[role_name]
        for perm_name in perm_names:
            if not db.query(RolePermission).filter(RolePermission.role_id == role.id, RolePermission.permission_id == perms[perm_name].id).first():
                db.add(RolePermission(role_id=role.id, permission_id=perms[perm_name].id))
        db.commit()
    
    assign_perm("user", ["READ"])
    assign_perm("admin", ["CREATE", "READ", "UPDATE"])
    assign_perm("super_admin", ["CREATE", "READ", "UPDATE", "DELETE"])
    
    # Create demo users if they don't exist
    demo_users = [
        {"username": "user1", "email": "user1@example.com", "password": "user123", "role": "user"},
        {"username": "admin1", "email": "admin1@example.com", "password": "admin123", "role": "admin"},
        {"username": "superadmin1", "email": "superadmin1@example.com", "password": "super123", "role": "super_admin"},
    ]
    
    for user_data in demo_users:
        user = db.query(User).filter(User.username == user_data["username"]).first()
        if not user:
            user = User(username=user_data["username"], email=user_data["email"])
            user.set_password(user_data["password"])
            db.add(user)
            db.commit()
            db.refresh(user)
            # Assign role
            user_role = UserRole(user_id=user.id, role_id=roles[user_data["role"]].id)
            db.add(user_role)
            db.commit()
    
    return {
        "message": "Database initialized!",
        "roles": list(roles.keys()),
        "permissions": list(perms.keys()),
        "users": [
            {"username": u["username"], "password": u["password"], "role": u["role"]}
            for u in demo_users
        ]
    }

# Authentication endpoint
@app.post("/login", response_model=Token, tags=["Auth"])
def login(login_req: LoginRequest, db: Session = Depends(get_db)):
    """Login and get access token"""
    user = db.query(User).filter(User.username == login_req.username).first()
    if not user or not user.verify_password(login_req.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": user.username})   
    return {"access_token": access_token, "token_type": "bearer"}

# User endpoints
@app.post("/users", response_model=UserResponse, tags=["Users"])
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user and assign default 'user' role"""
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="User already exists")

    new_user = User(username=user.username, email=user.email)
    new_user.set_password(user.password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Assign default "user" role
    default_role = db.query(Role).filter(Role.name == "user").first()
    if default_role:
        user_role = UserRole(user_id=new_user.id, role_id=default_role.id)
        db.add(user_role)
        db.commit()
        db.refresh(new_user)

    # Return properly formatted response
    roles = [ur.role.name for ur in new_user.roles]
    return {
        "id": new_user.id,
        "username": new_user.username,
        "email": new_user.email,
        "roles": roles,
    }

@app.get("/users", response_model=list[UserResponse], tags=["Users"])
def list_users(db: Session = Depends(get_db), _=Depends(get_current_user)):
    """List all users"""
    return db.query(User).all()

@app.get("/users/me", response_model=UserResponse, tags=["Users"])
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""  
    # Include role names in the returned payload for frontend convenience
    roles = [ur.role.name for ur in current_user.roles]
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "roles": roles,
    }

@app.get("/users/{user_id}", response_model=UserResponse, tags=["Users"])
def get_user(user_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    """Get user by ID"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.put("/users/{user_id}/role/{role_id}", tags=["Users"])
def update_user_role(
    user_id: int,
    role_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a user's role (admin only)"""
    user_roles = [ur.role.name for ur in current_user.roles]
    if "admin" not in user_roles and "super_admin" not in user_roles:
        raise HTTPException(status_code=403, detail="Only admins can update user roles")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    db.query(UserRole).filter(UserRole.user_id == user_id).delete()
    db.add(UserRole(user_id=user_id, role_id=role_id))
    db.commit()

    return {"message": f"User '{user.username}' role updated to '{role.name}'"}

# Role endpoints
@app.post("/roles", tags=["Roles"])
def create_role(role: RoleCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    """Create a new role"""
    if db.query(Role).filter(Role.name == role.name).first():
        raise HTTPException(status_code=400, detail="Role already exists")

    new_role = Role(name=role.name, description=role.description)
    db.add(new_role)
    db.commit()
    db.refresh(new_role)
    return new_role

@app.get("/roles", tags=["Roles"])
def list_roles(db: Session = Depends(get_db), _=Depends(get_current_user)):
    """List all roles"""
    return db.query(Role).all()

# Permission endpoints
@app.post("/permissions", tags=["Permissions"])
def create_permission(permission: PermissionCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    """Create a new permission"""
    if db.query(Permission).filter(Permission.name == permission.name).first():
        raise HTTPException(status_code=400, detail="Permission already exists")

    new_permission = Permission(name=permission.name, description=permission.description)
    db.add(new_permission)
    db.commit()
    db.refresh(new_permission)
    return new_permission

@app.get("/permissions", tags=["Permissions"])
def list_permissions(db: Session = Depends(get_db), _=Depends(get_current_user)):
    """List all permissions"""
    return db.query(Permission).all()


@app.get("/admin/users", tags=["Admin"])
def admin_list_users(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """List users and their roles (admin + super_admin only)"""
    user_roles = [ur.role.name for ur in current_user.roles]
    if "admin" not in user_roles and "super_admin" not in user_roles:
        raise HTTPException(status_code=403, detail="Only admins can view users")

    users = db.query(User).all()
    result = []
    for u in users:
        roles = [ur.role.name for ur in u.roles]
        result.append({"id": u.id, "username": u.username, "email": u.email, "roles": roles})
    return result


@app.post("/admin/users/{user_id}/set_role", tags=["Admin"])
def set_user_role(user_id: int, role_name: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Set a user's role (super_admin only). Body: role_name (string)"""
    # Only super_admin can change roles
    user_roles = [ur.role.name for ur in current_user.roles]
    if "super_admin" not in user_roles:
        raise HTTPException(status_code=403, detail="Only super_admin can change roles")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    role = db.query(Role).filter(Role.name == role_name).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    # Remove existing roles and assign the new role
    db.query(UserRole).filter(UserRole.user_id == user_id).delete()
    db.add(UserRole(user_id=user_id, role_id=role.id))
    db.commit()

    return {"message": f"Role for user {user.username} set to {role.name}"}

@app.delete("/admin/users/{user_id}", tags=["Admin"])
def delete_user(user_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Delete a user (super_admin only)"""
    user_roles = [ur.role.name for ur in current_user.roles]
    if "super_admin" not in user_roles:
        raise HTTPException(status_code=403, detail="Only super_admin can delete users")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent super_admin from deleting themselves
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")

    # Delete user roles and the user
    db.query(UserRole).filter(UserRole.user_id == user_id).delete()
    db.delete(user)
    db.commit()

    return {"message": f"User {user.username} deleted successfully"}

@app.get("/users/me/permissions", tags=["Permissions"])
def get_current_user_permissions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's permissions"""
    perms = (
        db.query(Permission)
        .join(RolePermission)
        .join(UserRole, UserRole.role_id == RolePermission.role_id)
        .filter(UserRole.user_id == current_user.id)
        .all()
    )
    return perms

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
