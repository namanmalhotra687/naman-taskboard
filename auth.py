from sqlalchemy.orm import Session
from model import User

def authenticate_user(db: Session, username: str, password: str):
    user = db.query(User).filter(User.username == username).first()
    if user and user.password == password:
        return user
    return None

def login_user(request, user):
    request.session["user"] = user.username

def logout_user(request):
    request.session.clear()
