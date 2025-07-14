from model import SessionLocal, User

db = SessionLocal()

username = input("Enter username to delete: ")
user = db.query(User).filter(User.username == username).first()

if user:
    db.delete(user)
    db.commit()
    print(f"✅ User '{username}' deleted.")
else:
    print(f"❌ User '{username}' does not exist.")
