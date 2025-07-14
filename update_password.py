from sqlalchemy.orm import Session
from model import SessionLocal, User

# 🚀 Update these
USERNAME_TO_UPDATE = "admin"
NEW_PASSWORD = "naman"

db: Session = SessionLocal()

user = db.query(User).filter(User.username == USERNAME_TO_UPDATE).first()

if user:
    user.password = NEW_PASSWORD
    db.commit()
    print(f"✅ Password updated successfully for user '{USERNAME_TO_UPDATE}'.")
else:
    print(f"❌ User '{USERNAME_TO_UPDATE}' not found.")

db.close()
