from sqlalchemy.orm import Session
from model import SessionLocal, User

db: Session = SessionLocal()

username = input("Enter username: ").strip()
password = input("Enter password: ").strip()

# ✅ Check if user already exists
existing_user = db.query(User).filter(User.username == username).first()

if existing_user:
    print(f"❌ User '{username}' already exists.")
else:
    new_user = User(username=username, password=password)
    db.add(new_user)
    db.commit()
    print(f"✅ User '{username}' created successfully.")
