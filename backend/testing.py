import sys
import os

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.db.database import SessionLocal
from backend.db.models import User, Session as UserSession

db = SessionLocal()

# Check users
users = db.query(User).all()
print("Users:")
for user in users:
    print(f"- {user.username} ({user.email})")

# Check sessions
sessions = db.query(UserSession).all()
print("\nSessions:")
for session in sessions:
    print(f"- {session.session_name} (User ID: {session.user_id})")
    print(f"  Data: {session.data}")

db.close()
