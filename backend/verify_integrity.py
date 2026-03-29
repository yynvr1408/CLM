import sys
import os
sys.path.append(os.getcwd())

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.models import Base, AuditLog, User, Clause
from app.services.audit_service import AuditService
from app.services.clause_service import ClauseService
from app.schemas.schemas import ClauseCreate, ClauseUpdate

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./clm_data.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def test_audit_chain():
    db = SessionLocal()
    try:
        # 1. Create a user if none exists
        user = db.query(User).first()
        if not user:
            print("No user found, please run main.py seed first.")
            return

        print(f"Testing with user: {user.username}")

        # 2. Log some actions using AuditService
        print("Logging actions...")
        AuditService.log_action(db, user.id, "TEST_A", "system")
        AuditService.log_action(db, user.id, "TEST_B", "system", changes={"key": "val"})

        # 3. Verify Chain
        result = AuditService.verify_chain(db)
        print(f"Chain Integrity Result: {result}")
        
        if result["is_valid"]:
            print("✅ Chain is VALID")
        else:
            print("❌ Chain is BROKEN")

        # 4. Tamper Test
        print("\nSimulating Tamper...")
        last_log = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
        last_log.action = "TAMPERED_ACTION"
        db.commit()

        result_tampered = AuditService.verify_chain(db)
        print(f"Tampered Integrity Result: {result_tampered}")
        if not result_tampered["is_valid"]:
            print("✅ Tamper Detection WORKED")
        else:
            print("❌ Tamper Detection FAILED")

    finally:
        db.close()

if __name__ == "__main__":
    test_audit_chain()
