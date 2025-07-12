import psycopg2
from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()

import os
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
try:
    conn = psycopg2.connect(
        dbname="resume_reviewer",
        user="postgres",
        password=POSTGRES_PASSWORD,
        host="localhost",
        port="5432"
    )
    print("✅ Connected to PostgreSQL successfully!")
    conn.close()
except Exception as e:
    print("❌ Failed to connect:", e)
