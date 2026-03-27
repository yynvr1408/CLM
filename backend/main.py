"""Main FastAPI application."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.core.config import settings
from app.core.security import hash_password
from app.database.session import engine, SessionLocal
from app.models.models import Base, Role, User
from app.api.v1.endpoints import auth, contracts, clauses, approvals, renewals, audit


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    # Create tables
    Base.metadata.create_all(bind=engine)
    print("Database tables created/verified.")

    # Seed default roles and admin user
    db = SessionLocal()
    try:
        # Create admin role if missing
        admin_role = db.query(Role).filter(Role.name == "admin").first()
        if not admin_role:
            admin_role = Role(
                name="admin",
                description="Administrator role",
                permissions={"all": True},
            )
            db.add(admin_role)
            db.commit()
            db.refresh(admin_role)
            print("Created admin role.")

        # Create user role if missing
        user_role = db.query(Role).filter(Role.name == "user").first()
        if not user_role:
            user_role = Role(
                name="user",
                description="Standard user role",
                permissions={"read_contracts": True},
            )
            db.add(user_role)
            db.commit()
            print("Created user role.")

        # Create default admin user if missing
        admin_user = db.query(User).filter(User.email == "admin@clm.com").first()
        if not admin_user:
            admin_user = User(
                email="admin@clm.com",
                username="admin",
                full_name="System Administrator",
                hashed_password=hash_password("admin@123"),
                role_id=admin_role.id,
                is_active=True,
                is_superuser=True,
            )
            db.add(admin_user)
            db.commit()
            print("Created default admin user (admin@clm.com / admin@123).")
    finally:
        db.close()

    yield


# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Enterprise-grade Contract Lifecycle Management Platform",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)


# Trusted Host Middleware (added first so it runs after CORS)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS,
)

# CORS Middleware (added second so it runs first — reverse order in Starlette)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# API Router
from fastapi import APIRouter

api_v1 = APIRouter(prefix=settings.API_V1_STR)


# Register endpoint routers
api_v1.include_router(auth.router)
api_v1.include_router(contracts.router)
api_v1.include_router(clauses.router)
api_v1.include_router(approvals.router)
api_v1.include_router(renewals.router)
api_v1.include_router(audit.router)


# Include router in main app
app.include_router(api_v1)


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": settings.PROJECT_NAME}


import sys

# Create static directory path compatible with PyInstaller
if getattr(sys, 'frozen', False):
    # Running in a PyInstaller bundle
    BASE_DIR = sys._MEIPASS
else:
    # Running in normal Python environment
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

STATIC_DIR = os.path.join(BASE_DIR, "static")

if os.path.exists(STATIC_DIR):
    # Mount the assets directory (where JS/CSS land in Vite build)
    assets_dir = os.path.join(STATIC_DIR, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
    
    # Catch-all route to serve the SPA index.html for React Router
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
            "message": "Welcome to CLM Platform API (Frontend not built)",
            "version": "1.0.0",
            "docs_url": "/api/docs",
            "health_url": "/health"
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )