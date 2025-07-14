from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse, StreamingResponse, Response
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from datetime import date
import csv
import io
import os

from model import Base, engine, SessionLocal, Item, User
from schemas import ItemBase, ItemUpdate
from generator_logic import generate_task
from auth import authenticate_user, login_user, logout_user
from apscheduler.schedulers.background import BackgroundScheduler

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="your-secret-key")
templates = Jinja2Templates(directory="templates")
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.head("/")
def root_head():
    return Response(status_code=200)

@app.get("/", response_class=HTMLResponse)
def read_root():
    return RedirectResponse(url="/login")

@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    username = form.get("username")
    password = form.get("password")
    user = authenticate_user(db, username, password)  # ✅ db comes first
    if user:
        login_user(request, user)
        return RedirectResponse(url="/view", status_code=303)
    else:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})


@app.get("/logout")
def logout(request: Request):
    logout_user(request)
    return RedirectResponse(url="/login")

@app.get("/view", response_class=HTMLResponse)
def view_tasks(request: Request, db: Session = Depends(get_db)):
    user = request.session.get("user")
    if not user:
        return RedirectResponse(url="/login")
    tasks = db.query(Item).all()
   return templates.TemplateResponse("view.html", {"request": request, "tasks": tasks})


@app.post("/add")
def add_task(request: Request,
             title: str = Form(...),
             description: str = Form(...),
             status: str = Form(...),
             deadline: date = Form(...),
             db: Session = Depends(get_db)):
    new_item = Item(title=title, description=description, status=status, deadline=deadline)
    db.add(new_item)
    db.commit()
    return RedirectResponse(url="/view", status_code=302)

@app.get("/delete/{item_id}")
def delete_task(item_id: int, db: Session = Depends(get_db)):
    task = db.query(Item).filter(Item.id == item_id).first()
    if task:
        db.delete(task)
        db.commit()
    return RedirectResponse(url="/view", status_code=302)

@app.post("/edit/{item_id}")
def edit_task(item_id: int,
              title: str = Form(...),
              description: str = Form(...),
              status: str = Form(...),
              deadline: date = Form(...),
              db: Session = Depends(get_db)):
    task = db.query(Item).filter(Item.id == item_id).first()
    if task:
        task.title = title
        task.description = description
        task.status = status
        task.deadline = deadline
        db.commit()
    return RedirectResponse(url="/view", status_code=302)

@app.get("/export")
def export_csv(db: Session = Depends(get_db)):
    items = db.query(Item).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Title", "Description", "Status", "Deadline"])
    for item in items:
        writer.writerow([item.id, item.title, item.description, item.status, item.deadline])
    output.seek(0)
    return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=tasks.csv"})

@app.post("/generate")
def generate_from_mvp(local_kw: str = Form(""), db: Session = Depends(get_db)):
    generated = generate_task(local_kw)
    new_item = Item(**generated)
    db.add(new_item)
    db.commit()
    return RedirectResponse(url="/view", status_code=302)

@app.post("/add-json")
def add_json(item: ItemBase, db: Session = Depends(get_db)):
    new_item = Item(**item.dict())
    db.add(new_item)
    db.commit()
    return {"message": "Task added successfully"}

@app.put("/edit-json/{item_id}")
def edit_json(item_id: int, item: ItemUpdate, db: Session = Depends(get_db)):
    task = db.query(Item).filter(Item.id == item_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Item not found")
    for key, value in item.dict(exclude_unset=True).items():
        setattr(task, key, value)
    db.commit()
    return {"message": "Task updated successfully"}

def schedule_task():
    db = SessionLocal()
    generated = generate_task()
    new_item = Item(**generated)
    db.add(new_item)
    db.commit()
    db.close()

scheduler = BackgroundScheduler()
scheduler.add_job(schedule_task, "interval", minutes=60)
scheduler.start()
