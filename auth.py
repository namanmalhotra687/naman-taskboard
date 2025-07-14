from fastapi import Request, Form
from starlette.responses import RedirectResponse
from model import SessionLocal, User

def authenticate_user(db, username, password):
    user = get_user_by_username(db, username)
    if user and user.password == password:
        return user
    return None


def login_user(request: Request, username: str):
    request.session["user"] = username

def logout_user(request: Request):
    request.session.pop("user", None)
