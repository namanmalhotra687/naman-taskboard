from fastapi import Request, Form
from starlette.responses import RedirectResponse
from model import SessionLocal, User

def authenticate_user(username: str, password: str):
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    db.close()
    return user and user.password == password

def login_user(request: Request, username: str):
    request.session["user"] = username

def logout_user(request: Request):
    request.session.pop("user", None)
