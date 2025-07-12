from sqlalchemy.orm import Session
from . import models

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, username: str, email: str, hashed_password: str):
    user = models.User(username=username, email=email, password_hash=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def create_session(db: Session, user_id: int, session_name: str):
    session = models.Session(
        user_id=user_id,
        session_name=session_name
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

def get_sessions_for_user(db: Session, user_id: int):
    return db.query(models.Session).filter(models.Session.user_id == user_id).all()
