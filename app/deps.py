from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from .database import get_db
from .auth import get_current_user
from .models import User, RolePermission, Permission, UserRole

def require_permission(permission_name: str):
    def checker(
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        # SUPER ADMIN FULL BYPASS
        role_names = {ur.role.name for ur in user.roles}
        if "super_admin" in role_names:
            return True

        perms = (
            db.query(Permission.name)
            .join(RolePermission)
            .join(UserRole, UserRole.role_id == RolePermission.role_id)
            .filter(UserRole.user_id == user.id)
            .all()
        )

        user_permissions = {p[0] for p in perms}

        if permission_name not in user_permissions:
            raise HTTPException(
                status_code=403,
                detail=f"Permission '{permission_name}' required"
            )

        return True

    return checker
