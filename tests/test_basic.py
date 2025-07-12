from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import sys
import os

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.db.models import User, Session as UserSession
from backend.db.database import Base
import json

# Update with your actual DATABASE_URL
DATABASE_URL = "postgresql://postgres:abhi2004@localhost:5432/resume_reviewer"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# Test JSON Data
test_json_data = {
    "resume_analysis": {
        "summary": {
            "skills": ["Python", "C++", "SQL"],
            "personal_info": {
                "name": "Abhishek Srivastava",
                "email": "srivabhi22@iitk.ac.in"
            }
        },
        "credentials": ["Python", "Machine Learning", "Deep Learning"],
        "missing_skills": ["Kubernetes", "Docker"],
        "job_skills": ["SQL", "REST APIs"]
    },
    "skill_recommendation": {
        "next_skills": ["Docker", "Kubernetes"],
        "resources": [
            {"title": "Docker Basics", "link": "https://docker.com"}
        ]
    },
    "ats_bullets": {
        "optimized_bullets": [
            "Implemented CNN model with 95% accuracy.",
            "Managed a team of 10 developers."
        ]
    }
}


def store_in_existing_session():
    db = SessionLocal()
    try:
        # Find user
        user = db.query(User).filter(User.username == "srivabhi22").first()
        if not user:
            print("❌ User 'srivabhi22' not found")
            return

        # Find session 1
        session = db.query(UserSession).filter(
            UserSession.id == 1,
            UserSession.user_id == user.id
        ).first()
        if not session:
            print("❌ Session 1 for user 'srivabhi22' not found")
            return

        print("✅ Found Session:", session.session_name)

        # Update session.data
        session.data = test_json_data
        db.commit()
        db.refresh(session)

        print("✅ JSON data stored successfully in session 1")

        # Fetch and print stored data
        print("\nStored Data in Session 1:")
        print(json.dumps(session.data, indent=2))

    except Exception as e:
        print("❌ Error:", e)
    finally:
        db.close()


if __name__ == "__main__":
    store_in_existing_session()
