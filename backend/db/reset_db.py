import sys
import os

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import Base, engine, init_db  # use from "name of directory in which .py file is"."name of .py file to import"
from db import models

def reset_database():
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("Creating tables...")
    init_db()
    print("✅ Database reset complete.")

if __name__ == "__main__":
    reset_database()
