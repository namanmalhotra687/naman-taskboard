# create_user.py
from model import SessionLocal, User

db = SessionLocal()
user = User(username="admin", password="admin")
db.add(user)
db.commit()
db.close()
print("✅ User created: admin / admin")
