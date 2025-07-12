import sys
import os

# Get the root directory and add it to sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)

from fastapi import FastAPI, Form, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from dotenv import load_dotenv
from src.parser import ResumeParser 
from src.recommender import SkillRecommender 
from jose import jwt, JWTError
from backend.db.database import init_db, SessionLocal
from backend.db import crud, auth
from backend.db.models import User, Session as UserSession
from sqlalchemy.orm import Session as DBSession
import json

# Load environment variables
load_dotenv()
# Initialize DB
init_db()
app = FastAPI()


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


chat_sessions = {}  # {session_id: chat_history list}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

youtube_api_key = os.getenv("YOUTUBE_API_KEY")

# Initialize Resume Parser and Skill Recommender
parser = ResumeParser()
recommender = SkillRecommender(youtube_api_key)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
# Dependency to get current user
def get_current_user(token: str = Depends(oauth2_scheme), db: DBSession = Depends(get_db)):
    try:
        payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        username = payload.get("sub")
        user = crud.get_user_by_username(db, username)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def clean_resume_analysis(summary, credentials, missing_skills, job_skills):
    try:
        # If any field is a string, parse it
        if isinstance(summary, str):
            summary = json.loads(summary)
        if isinstance(credentials, str):
            credentials = json.loads(credentials)
        if isinstance(missing_skills, str):
            missing_skills = json.loads(missing_skills)
        if isinstance(job_skills, str):
            job_skills = json.loads(job_skills)
    except Exception as e:
        raise ValueError(f"Invalid JSON format from LLM: {e}")

    # Fallback defaults
    summary = summary or {}
    credentials = credentials or {}
    missing_skills = missing_skills or {}
    job_skills = job_skills or {}

    return {
        "summary": summary,
        "credentials": credentials,
        "missing_skills": missing_skills,
        "job_skills": job_skills
    }


@app.get("/db_check")
def db_check(db: DBSession = Depends(get_db)):
    users = db.query(User).all()
    sessions = db.query(UserSession).all()

    return {
        "total_users": len(users),
        "users": [u.username for u in users],
        "total_sessions": len(sessions),
        "sessions": [
            {"id": s.id, "name": s.session_name, "user_id": s.user_id, "has_resume_analysis": "resume_analysis" in (s.data or {})}
            for s in sessions
        ]
    }

@app.get("/get_all_data")
def get_all_data(db: DBSession = Depends(get_db)):
    users = db.query(User).all()
    all_data = []

    for user in users:
        user_data = {
            "username": user.username,
            "sessions": []
        }
        for session in user.sessions:
            user_data["sessions"].append({
                "id": session.id,
                "name": session.session_name,
                "data": session.data or {}
            })
        all_data.append(user_data)

    return {
        "total_users": len(users),
        "users": all_data
    }

# --- AUTH ROUTES ---
@app.post("/register")
def register(username: str, email: str, password: str, db: DBSession = Depends(get_db)):
    if crud.get_user_by_username(db, username):
        raise HTTPException(status_code=400, detail="Username already exists")
    hashed_pw = auth.hash_password(password)
    crud.create_user(db, username, email, hashed_pw)
    return {"message": "User registered successfully"}

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: DBSession = Depends(get_db)):
    user = crud.get_user_by_username(db, form_data.username)
    if not user or not auth.verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    access_token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# --- SESSION ROUTES ---
@app.post("/start_session")
def start_session(session_name: str, user: User = Depends(get_current_user), db: DBSession = Depends(get_db)):
    session = crud.create_session(db, user.id, session_name)
    return {"session_id": session.id, "session_name": session.session_name}

@app.get("/my_sessions")
def my_sessions(user: User = Depends(get_current_user), db: DBSession = Depends(get_db)):
    sessions = crud.get_sessions_for_user(db, user.id)
    return [{"id": s.id, "name": s.session_name, "created_at": s.created_at} for s in sessions]

@app.get("/load_session")
def load_session(session_id: int, user: User = Depends(get_current_user), db: DBSession = Depends(get_db)):
    session = db.query(UserSession).filter(
        UserSession.id == session_id,
        UserSession.user_id == user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session.data or {
    "resume_analysis": {},
    "skill_recommendation": {},
    "ats_bullets": {}
    }


class ResumeRequest(BaseModel):
    file_path: str
    job_description: str


@app.post('/parse_resume')
async def parse_resume(
    resume_filename: str = Form(...),
    job_description: str = Form(...),
    session_id: int = Form(...),
    user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):  
    try:
        # Path to src directory
        src_dir = os.path.join(os.path.dirname(__file__), "..", "src")
        resume_path = os.path.join(src_dir, resume_filename)
        if not os.path.exists(resume_path):
            raise HTTPException(status_code=404, detail="Resume file not found")

        print(f"Processing resume at: {resume_path}")
        # Parse resume (your existing logic)
        summary, credentials, missing_skills, job_skills, _ = parser.parse_resume(
            resume_path, job_description
        )

        # Clean and validate LLM output
        resume_analysis = clean_resume_analysis(
            summary, credentials, missing_skills, job_skills
        )
        # Delete the file after processing
        os.remove(resume_path)

        print(session_id, user.id)
        # Save resume summary & results into session data
        session = db.query(UserSession).filter(
            UserSession.id == session_id,
            UserSession.user_id == user.id
        ).first()

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # session.data = session.data or {}  # Initialize if None
        print(type(resume_analysis))
        session.data["resume_analysis"] = resume_analysis
        db.commit()
        db.refresh(session)

        return resume_analysis

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/recommend_courses')
def recommend_courses(skill: str):
    try:
        result = recommender.get_missing_skills_resources(skill)
        return {'courses': result}
    except Exception as e:
        return {'error': str(e)}
    
@app.get('/ats_optimized_bullets')
def get_ats_optimized_bullets(file_path: str):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            ats_content = file.read()

        # If any field is a string, parse it
        if isinstance(ats_content, str):
            ats_content = json.loads(ats_content)
        return {"ats_content": ats_content}
    
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return None
    except Exception as e:
        print(f"Error while processing file: {e}")
        return None
