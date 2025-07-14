from sqlalchemy.orm import Session
from fastapi import Request

from model import User

def authenticate_user(db: Session, username: str, password: str):
    """Authenticate user with database"""
    return db.query(User).filter(User.username == username, User.password == password).first()

def login_user(request: Request, user: User):
    """Login the user by setting session"""
    request.session['user'] = user.username

def logout_user(request: Request):
    """Logout user by clearing session"""
    request.session.pop('user', None)
