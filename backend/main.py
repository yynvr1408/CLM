"""Main FastAPI application."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
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
        admin_user = db.query(User).filter(User.email == "admin@clm.local").first()
        if not admin_user:
            admin_user = User(
                email="admin@clm.local",
                username="admin",
                full_name="System Administrator",
                hashed_password=hash_password("admin@123"),
                role_id=admin_role.id,
                is_active=True,
                is_superuser=True,
            )
            db.add(admin_user)
            db.commit()
            print("Created default admin user (admin@clm.local / admin@123).")
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


# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Trusted Host Middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS,
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


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "Welcome to CLM Platform",
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