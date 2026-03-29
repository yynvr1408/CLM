"""Main FastAPI application with security middleware and RBAC."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.core.config import settings
from app.core.security import hash_password
from app.core.middleware import SecurityHeadersMiddleware, RequestLoggingMiddleware
from app.database.session import engine, SessionLocal
from app.models.models import (
    Base, Role, User, Organization, ROLE_TEMPLATES
)
from app.api.v1.endpoints import (
    auth, contracts, clauses, approvals, renewals, audit,
    templates, comments, tags, notifications,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    # Create tables
    Base.metadata.create_all(bind=engine)
    print("[OK] Database tables created/verified.")

    # Seed default data
    db = SessionLocal()
    try:
# ------- Seed default organization ------------------------
        default_org = db.query(Organization).filter(Organization.slug == "default").first()
        if not default_org:
            default_org = Organization(
                name="Default Organization",
                slug="default",
                settings={},
                subscription_tier="enterprise",
            )
            db.add(default_org)
            db.commit()
            db.refresh(default_org)
            print("[OK] Created default organization.")

        # ------- Seed roles from ROLE_TEMPLATES -------------------
        for role_name, role_config in ROLE_TEMPLATES.items():
            existing = db.query(Role).filter(Role.name == role_name).first()
            if not existing:
                role = Role(
                    name=role_name,
                    description=role_config["description"],
                    permissions=role_config["permissions"],
                    is_system_role=True,
                )
                db.add(role)
                print(f"  [OK] Created role: {role_name}")
            else:
                # Update permissions on existing system roles
                if existing.is_system_role:
                    existing.permissions = role_config["permissions"]
                    existing.description = role_config["description"]

        db.commit()

        # ------- Seed default admin user --------------------------
        admin_role = db.query(Role).filter(Role.name == "super_admin").first()
        if not admin_role:
            admin_role = db.query(Role).filter(Role.name == "admin").first()

        admin_user = db.query(User).filter(User.email == "admin@clm.com").first()
        if not admin_user and admin_role:
            admin_user = User(
                email="admin@clm.com",
                username="admin",
                full_name="System Administrator",
                hashed_password=hash_password("Admin@123"),
                role_id=admin_role.id,
                organization_id=default_org.id,
                is_active=True,
                is_approved=True,
                is_superuser=True,
            )
            db.add(admin_user)
            db.commit()
            print("[OK] Created default admin user (admin@clm.com / Admin@123)")
        elif admin_user:
            # Ensure admin is always active and approved
            if not admin_user.is_active or not admin_user.is_approved:
                admin_user.is_active = True
                admin_user.is_approved = True
                db.commit()

        # Final commit to ensure all read-only transactions are finalized
        db.commit()
        print("[OK] Database initialization complete.")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Database initialization failed: {str(e)}")
    finally:
        db.close()

    yield


# ===============================================================
# Initialize FastAPI app
# ===============================================================
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Enterprise-grade Contract Lifecycle Management Platform with RBAC",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)


# ===============================================================
# Middleware Stack (order matters -- added in reverse execution order)
# ===============================================================

# 1. Security headers (runs last in middleware chain -> first in response)
app.add_middleware(SecurityHeadersMiddleware)

# 2. Request logging
app.add_middleware(RequestLoggingMiddleware)

# 3. Trusted Host
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS,
)

# 4. CORS (runs first in middleware chain)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Requested-With"],
)


# ===============================================================
# API Router
# ===============================================================
from fastapi import APIRouter

api_v1 = APIRouter(prefix=settings.API_V1_STR)

# Register all endpoint routers
api_v1.include_router(auth.router)
api_v1.include_router(contracts.router)
api_v1.include_router(clauses.router)
api_v1.include_router(approvals.router)
api_v1.include_router(renewals.router)
api_v1.include_router(audit.router)
api_v1.include_router(templates.router)
api_v1.include_router(comments.router)
api_v1.include_router(tags.router)
api_v1.include_router(notifications.router)

# Mount in main app
app.include_router(api_v1)


# ===============================================================
# Health Check
# ===============================================================
@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "version": "2.0.0",
        "features": [
            "RBAC", "Multi-tenancy", "Token Blocklist", "Account Lockout",
            "Comments", "Templates", "Tags", "In-App Notifications",
            "Soft Delete", "Audit Trail", "Security Headers",
        ]
    }


# ===============================================================
# Static Files (SPA serving)
# ===============================================================
import sys

if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

STATIC_DIR = os.path.join(BASE_DIR, "static")

if os.path.exists(STATIC_DIR):
    assets_dir = os.path.join(STATIC_DIR, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{catchall:path}")
    def serve_frontend(catchall: str):
        file_path = os.path.join(STATIC_DIR, catchall)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))
else:
    @app.get("/")
    def root():
        """Root endpoint."""
        return {
            "message": "CLM Platform API v2.0 (Frontend not built)",
            "version": "2.0.0",
            "docs_url": "/api/docs",
            "health_url": "/health",
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )