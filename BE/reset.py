from sqlalchemy import text, inspect
from database.main_db import main_engine

def get_all_tables():
    inspector = inspect(main_engine)
    return inspector.get_table_names()

def drop_all_tables():
    tables = get_all_tables()
    
    with main_engine.begin() as conn:
        # Disable foreign key checks for PostgreSQL
        conn.execute(text("SET CONSTRAINTS ALL DEFERRED;"))
        
        for table in tables:
            conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE;"))
            print(f"Dropped table: {table}")
        
        # Re-enable foreign key checks
        conn.execute(text("SET CONSTRAINTS ALL IMMEDIATE;"))

    print(f"\nSuccessfully dropped {len(tables)} tables.")

if __name__ == "__main__":
    print("Starting database reset...")
    drop_all_tables()
    print("Database reset completed.")