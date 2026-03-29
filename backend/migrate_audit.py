from sqlalchemy import create_engine, inspect, text
from app.core.config import settings

def migrate():
    engine = create_engine(settings.DATABASE_URL)
    inspector = inspect(engine)
    
    # 1. Update audit_logs table
    columns = [c['name'] for c in inspector.get_columns('audit_logs')]
    print(f"Current audit_logs columns: {columns}")
    
    with engine.connect() as conn:
        if 'clause_id' not in columns:
            print("Adding clause_id to audit_logs...")
            conn.execute(text("ALTER TABLE audit_logs ADD COLUMN clause_id INTEGER REFERENCES clauses(id)"))
        
        # Any other missing columns?
        # Standard columns from previous sessions
        for col in ['ip_address', 'user_agent', 'previous_hash', 'entry_hash']:
            if col not in columns:
                print(f"Adding {col} to audit_logs...")
                conn.execute(text(f"ALTER TABLE audit_logs ADD COLUMN {col} TEXT"))
                
        conn.commit()
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
