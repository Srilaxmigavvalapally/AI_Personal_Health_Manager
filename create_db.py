# create_db.py (in the root folder)

from modules.database import create_db_and_tables

if __name__ == "__main__":
    print("Initializing the database...")
    try:
        create_db_and_tables()
        print("\nDatabase and tables created successfully!")
    except Exception as e:
        print(f"\nAn error occurred: {e}")