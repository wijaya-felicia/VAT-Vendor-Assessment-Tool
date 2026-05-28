"""
Script to unlock all locked model priors in the database.
Handles both old and new database schemas.
Run this from the backend directory: python unlock_priors.py
"""

from sqlalchemy import text
from src.database.connection import SessionLocal, engine


def unlock_all_priors():
    """Unlock all locked model checkpoints."""
    db = SessionLocal()
    
    try:
        # Use raw SQL to avoid schema conflicts during migration
        result = db.execute(text(
            "UPDATE model_checkpoints SET is_locked = 0 WHERE is_locked = 1"
        ))
        
        affected_rows = result.rowcount
        db.commit()
        
        if affected_rows == 0:
            print("✓ No locked priors found or already unlocked.")
        else:
            print(f"✓ Successfully unlocked {affected_rows} prior(s).")
    
    except Exception as e:
        db.rollback()
        print(f"✗ Error unlocking priors: {e}")
        print("\nTrying to add missing columns to schema...")
        try:
            migrate_schema(db)
            # Retry the unlock
            result = db.execute(text(
                "UPDATE model_checkpoints SET is_locked = 0 WHERE is_locked = 1"
            ))
            affected_rows = result.rowcount
            db.commit()
            if affected_rows == 0:
                print("✓ No locked priors found.")
            else:
                print(f"✓ Schema updated and unlocked {affected_rows} prior(s).")
        except Exception as e2:
            db.rollback()
            print(f"✗ Migration also failed: {e2}")
    
    finally:
        db.close()


def migrate_schema(db):
    """Add missing columns if they don't exist."""
    inspector_sql = "PRAGMA table_info(model_checkpoints)"
    columns = db.execute(text(inspector_sql)).fetchall()
    column_names = [col[1] for col in columns]
    
    if 'user_id' not in column_names:
        print("  Adding user_id column...")
        db.execute(text("ALTER TABLE model_checkpoints ADD COLUMN user_id INTEGER"))
    
    if 'locked_by_user_id' not in column_names:
        print("  Adding locked_by_user_id column...")
        db.execute(text("ALTER TABLE model_checkpoints ADD COLUMN locked_by_user_id INTEGER"))
    
    if 'locked_at' not in column_names:
        print("  Adding locked_at column...")
        db.execute(text("ALTER TABLE model_checkpoints ADD COLUMN locked_at DATETIME"))
    
    db.commit()
    print("✓ Schema migration complete.")


if __name__ == "__main__":
    unlock_all_priors()
