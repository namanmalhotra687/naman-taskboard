# ✅ main.py (Final Combined Code)
from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from datetime import date, timedelta
import csv
import io

from model import Base, engine, SessionLocal, Item, User
from schemas import ItemBase, ItemUpdate
from generator_logic import generate_task
from auth import authenticate_user, login_user, logout_user
from email_utils import send_email
from apscheduler.schedulers.background import BackgroundScheduler

app = FastAPI()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session Middleware
app.add_middleware(SessionMiddleware, secret_key="your-secret-key")

# Templates
templates = Jinja2Templates(directory="templates")

# DB setup
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ------------------------ AUTH ROUTES ------------------------
@app.get("/")
def root():
    return RedirectResponse(url="/login")

@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    username = form.get("username")
    password = form.get("password")
    user = authenticate_user(db, username, password)
    if user:
        login_user(request, user)
        return RedirectResponse(url="/view", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})

@app.get("/logout")
def logout(request: Request):
    logout_user(request)
    return RedirectResponse(url="/login")

# ------------------------ FORM ROUTES ------------------------
@app.get("/view", response_class=HTMLResponse)
def view_items(request: Request, tag: str = None, db: Session = Depends(get_db)):
    query = db.query(Item)
    if tag:
        query = query.filter(Item.tag == tag)
    items = query.all()
    return templates.TemplateResponse("view.html", {"request": request, "items": items})


@app.post("/add")
def add_task(request: Request,
             title: str = Form(...),
             description: str = Form(...),
             status: str = Form(...),
             deadline: date = Form(...),
             category: str = Form(...),
             recurrence: str = Form("none"),
             db: Session = Depends(get_db)):
    new_item = Item(title=title, description=description, status=status,
                    deadline=deadline, category=category, recurrence=recurrence)
    db.add(new_item)
    db.commit()
    return RedirectResponse(url="/view", status_code=302)

@app.post("/edit/{item_id}")
def edit_task(item_id: int,
              title: str = Form(...),
              description: str = Form(...),
              status: str = Form(...),
              deadline: date = Form(...),
              category: str = Form(...),
              recurrence: str = Form("none"),
              db: Session = Depends(get_db)):
    task = db.query(Item).filter(Item.id == item_id).first()
    if task:
        task.title = title
        task.description = description
        task.status = status
        task.deadline = deadline
        task.category = category
        task.recurrence = recurrence
        db.commit()
    return RedirectResponse(url="/view", status_code=302)

@app.get("/delete/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(item)
    db.commit()
    return RedirectResponse(url="/view", status_code=303)

# ------------------------ JSON ROUTES ------------------------
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
        raise HTTPException(status_code=404, detail="Task not found")
    for key, value in item.dict(exclude_unset=True).items():
        setattr(task, key, value)
    db.commit()
    return {"message": "Task updated"}

@app.delete("/delete-json/{item_id}")
def delete_json(item_id: int, db: Session = Depends(get_db)):
    task = db.query(Item).filter(Item.id == item_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return {"message": "Task deleted"}

# ------------------------ CSV EXPORT ------------------------
@app.get("/export")
def export_csv(db: Session = Depends(get_db)):
    items = db.query(Item).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Title", "Description", "Status", "Deadline", "Category", "Recurrence"])
    for item in items:
        writer.writerow([item.id, item.title, item.description, item.status, item.deadline, item.category, item.recurrence])
    output.seek(0)
    return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=tasks.csv"})

# ------------------------ GENERATOR ------------------------
@app.post("/generate")
def generate_from_mvp(local_kw: str = Form(""), db: Session = Depends(get_db)):
    generated = generate_task(local_kw)
    new_item = Item(**generated)
    db.add(new_item)
    db.commit()
    return RedirectResponse(url="/view", status_code=302)

# ------------------------ BACKGROUND SCHEDULER ------------------------
def handle_recurring_tasks():
    db = SessionLocal()
    today = date.today()
    recurring_tasks = db.query(Item).filter(Item.recurrence != "none").all()
    for task in recurring_tasks:
        should_repeat = (
            (task.recurrence == "daily" and task.deadline < today) or
            (task.recurrence == "weekly" and task.deadline + timedelta(days=7) <= today)
        )
        if should_repeat:
            new_deadline = today if task.recurrence == "daily" else task.deadline + timedelta(days=7)
            new_task = Item(
                title=task.title,
                description=task.description,
                status="pending",
                deadline=new_deadline,
                category=task.category,
                recurrence=task.recurrence,
                generated=True
            )
            db.add(new_task)
    db.commit()
    db.close()

def send_task_reminders():
    db = SessionLocal()
    today = date.today()
    tomorrow = today + timedelta(days=1)
    tasks = db.query(Item).filter(Item.deadline.in_([today, tomorrow])).all()
    if not tasks:
        print("📭 No tasks to remind today.")
        return
    recipient = "youremail@example.com"
    for task in tasks:
        subject = f"⏰ Reminder: {task.title} due on {task.deadline}"
        body = (
            f"Task: {task.title}\nDescription: {task.description}\nDeadline: {task.deadline}\n"
        )
        send_email(recipient, subject, body)
    db.close()

scheduler = BackgroundScheduler()
scheduler.add_job(handle_recurring_tasks, "interval", hours=24)
scheduler.add_job(send_task_reminders, "cron", hour=9)
scheduler.start()

from datetime import datetime
from fastapi import status

@app.post("/add-json", status_code=status.HTTP_201_CREATED)
def add_json(item: ItemBase, db: Session = Depends(get_db)):
    try:
        print("📩 Received JSON:", item.dict())

        # Parse and convert the deadline from string to date if needed
        item_data = item.dict()
        if isinstance(item_data["deadline"], str):
            item_data["deadline"] = datetime.strptime(item_data["deadline"], "%Y-%m-%d").date()

        new_item = Item(**item_data)
        db.add(new_item)
        db.commit()
        db.refresh(new_item)
        print("✅ Task inserted with ID:", new_item.id)
        return {"message": "Task added", "id": new_item.id}

    except Exception as e:
        import traceback
        traceback.print_exc()  # Prints full traceback in terminal
        raise HTTPException(status_code=500, detail=f"Server Error: {str(e)}")

# main.py

@app.post("/add")
def add_item(
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
    status: str = Form(...),
    deadline: date = Form(...),
    tag: str = Form(None),  # 👈 Add this
    db: Session = Depends(get_db),
):
    item = Item(title=title, description=description, status=status, deadline=deadline, tag=tag)
    db.add(item)
    db.commit()
    return RedirectResponse(url="/view", status_code=303)

from fastapi import Form
from typing import List

@app.post("/bulk-action")
def bulk_action(
    request: Request,
    item_ids: List[int] = Form(...),
    action: str = Form(...),
    db: Session = Depends(get_db),
):
    if action == "delete":
        db.query(Item).filter(Item.id.in_(item_ids)).delete(synchronize_session=False)
    elif action == "complete":
        db.query(Item).filter(Item.id.in_(item_ids)).update({"status": "Completed"}, synchronize_session=False)
    db.commit()
    return RedirectResponse(url="/view", status_code=303)

@app.get("/view", response_class=HTMLResponse)
def view_page(request: Request, db: Session = Depends(get_db)):
    items = db.query(Item).all()
    return templates.TemplateResponse("view.html", {"request": request, "items": items})

from fastapi.responses import HTMLResponse
from fastapi import APIRouter, Request, Depends

@app.api_route("/view", methods=["GET", "HEAD"], response_class=HTMLResponse)
def view_page(request: Request, db: Session = Depends(get_db)):
    tasks = db.query(Item).all()
    return templates.TemplateResponse("view.html", {"request": request, "tasks": tasks})

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    items = db.query(Item).all()

    # Count task statuses
    status_count = {"Pending": 0, "Completed": 0, "In Progress": 0}
    for item in items:
        status = item.status
        if status in status_count:
            status_count[status] += 1
        else:
            status_count[status] = 1

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "status_count": status_count
    })
