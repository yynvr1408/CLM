import sys
import os

# Add the current directory and the app directory to sys.path
sys.path.append(os.getcwd())

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.models import Role, User, ROLE_TEMPLATES

def migrate_roles():
    engine = create_engine(settings.DATABASE_URL)
    with Session(engine) as db:
        print("Starting role migration...")
        
        # 1. Fetch current roles
        current_roles = {r.name: r for r in db.query(Role).all()}
        print(f"Current roles in DB: {list(current_roles.keys())}")
        
        # 2. Define mapping from old roles to new roles
        mapping = {
            "super_admin": "super_admin",
            "admin": "admin",
            "contract_manager": "editor",
            "legal_reviewer": "editor",
            "approver": "editor",
            "viewer": "viewer",
            "external_party": "viewer"
        }
        
        # 3. Create/Update new roles from ROLE_TEMPLATES
        new_roles = {}
        for role_name, data in ROLE_TEMPLATES.items():
            if role_name in current_roles:
                role = current_roles[role_name]
                role.description = data["description"]
                role.permissions = data["permissions"]
                print(f"Updated existing role: {role_name}")
            else:
                role = Role(
                    name=role_name,
                    description=data["description"],
                    permissions=data["permissions"],
                    is_system_role=True
                )
                db.add(role)
                print(f"Created new role: {role_name}")
            db.flush()
            new_roles[role_name] = role
            
        # 4. Reassign users
        users = db.query(User).all()
        for user in users:
            old_role_name = None
            # Find the name of the role the user currently has
            for name, r in current_roles.items():
                if r.id == user.role_id:
                    old_role_name = name
                    break
            
            if old_role_name and old_role_name in mapping:
                new_role_name = mapping[old_role_name]
                if new_role_name != old_role_name:
                    user.role_id = new_roles[new_role_name].id
                    print(f"Reassigned user {user.username} from {old_role_name} to {new_role_name}")
            elif not old_role_name:
                 # Default to viewer if role is missing for some reason
                 user.role_id = new_roles["viewer"].id
                 print(f"Set missing role for user {user.username} to viewer")

        # 5. Remove roles that are no longer in ROLE_TEMPLATES
        for name, role in current_roles.items():
            if name not in ROLE_TEMPLATES:
                print(f"Removing obsolete role: {name}")
                db.delete(role)
        
        db.commit()
        print("Migration complete.")

if __name__ == "__main__":
    migrate_roles()
