from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from datetime import date, datetime
import csv
import io

from model import Base, engine, SessionLocal, Item, User
from schemas import ItemBase, ItemUpdate
from generator_logic import generate_task
from auth import authenticate_user, login_user, logout_user

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="super-secret")
templates = Jinja2Templates(directory="templates")

# Create DB tables and default admin
Base.metadata.create_all(bind=engine)
db = SessionLocal()
if not db.query(User).filter(User.username == "admin").first():
    db.add(User(username="admin", password="admin"))
    db.commit()
    print("✅ Default user 'admin' created.")
db.close()

# Dependency for DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Dependency for login check
def get_current_user(request: Request):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user

# Login routes
@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if authenticate_user(username, password):
        login_user(request, username)
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})

@app.get("/logout")
def logout(request: Request):
    logout_user(request)
    return RedirectResponse("/login", status_code=303)

# Registration routes
@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
def register_user(request: Request, username: str = Form(...), password: str = Form(...)):
    db = SessionLocal()
    if db.query(User).filter(User.username == username).first():
        db.close()
        return templates.TemplateResponse("register.html", {"request": request, "error": "Username already exists"})
    db.add(User(username=username, password=password))
    db.commit()
    db.close()
    return templates.TemplateResponse("register.html", {"request": request, "success": "User registered successfully!"})

# HTML: Add Task Form
@app.get("/", response_class=HTMLResponse)
def form(request: Request):
    get_current_user(request)
    today = date.today().isoformat()
    return templates.TemplateResponse("form.html", {"request": request, "current_date": today})

@app.post("/add")
def add_task(
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
    status: str = Form(...),
    deadline: str = Form(...)
):
    get_current_user(request)
    db = SessionLocal()
    item = Item(title=title, description=description, status=status, deadline=deadline)
    db.add(item)
    db.commit()
    db.close()
    return RedirectResponse("/view", status_code=303)

# HTML: View Tasks
@app.get("/view", response_class=HTMLResponse)
def view_tasks(request: Request, q: str = "", status: str = ""):
    get_current_user(request)
    db = SessionLocal()
    query = db.query(Item)
    if q:
        query = query.filter(Item.title.ilike(f"%{q}%") | Item.description.ilike(f"%{q}%"))
    if status:
        query = query.filter(Item.status == status)
    tasks = query.all()
    db.close()
    return templates.TemplateResponse("view.html", {
        "request": request,
        "tasks": tasks,
        "q": q,
        "status": status,
        "current_date": date.today().isoformat()
    })

@app.post("/edit/{item_id}")
def edit_task_html(
    item_id: int,
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
    status: str = Form(...),
    deadline: str = Form(...)
):
    get_current_user(request)
    db = SessionLocal()
    task = db.query(Item).filter(Item.id == item_id).first()
    if task:
        task.title = title
        task.description = description
        task.status = status
        task.deadline = deadline
        db.commit()
    db.close()
    return RedirectResponse("/view", status_code=303)

@app.post("/delete/{item_id}")
def delete_task_html(item_id: int, request: Request):
    get_current_user(request)
    db = SessionLocal()
    task = db.query(Item).filter(Item.id == item_id).first()
    if task:
        db.delete(task)
        db.commit()
    db.close()
    return RedirectResponse("/view", status_code=303)

# JSON APIs
@app.post("/add-json")
def add_item_json(item: ItemBase, db: Session = Depends(get_db)):
    new_item = Item(**item.dict())
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return {"message": "Item added", "item": new_item}

@app.get("/items")
def get_all_items(db: Session = Depends(get_db)):
    return db.query(Item).all()

@app.get("/items/{item_id}")
def get_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@app.put("/edit-json/{item_id}")
def update_item(item_id: int, item: ItemUpdate, db: Session = Depends(get_db)):
    db_item = db.query(Item).filter(Item.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    for key, value in item.dict(exclude_unset=True).items():
        setattr(db_item, key, value)
    db.commit()
    db.refresh(db_item)
    return {"message": "Item updated", "item": db_item}

@app.delete("/delete-json/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(Item).filter(Item.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(db_item)
    db.commit()
    return {"message": "Item deleted"}

@app.post("/generate")
def run_generator(request: Request, local_kw: str = Form(...)):
    get_current_user(request)
    db = SessionLocal()
    data = generate_task(local_kw)
    item = Item(**data, generated=True)
    db.add(item)
    db.commit()
    db.close()
    return RedirectResponse(url="/view", status_code=303)

@app.get("/export")
def export_csv(db: Session = Depends(get_db)):
    items = db.query(Item).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Title", "Description", "Status", "Deadline"])
    for item in items:
        writer.writerow([item.id, item.title, item.description, item.status, item.deadline])
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=tasks.csv"}
    )

@app.post("/toggle-complete/{item_id}")
def toggle_complete(item_id: int, request: Request):
    get_current_user(request)
    db = SessionLocal()
    task = db.query(Item).filter(Item.id == item_id).first()
    if task:
        task.status = "completed" if task.status != "completed" else "pending"
        db.commit()
    db.close()
    return RedirectResponse("/view", status_code=303)

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    get_current_user(request)

    all_tasks = db.query(Item).all()

    completed = sum(1 for t in all_tasks if t.status == "completed")
    in_progress = sum(1 for t in all_tasks if t.status == "in-progress")
    pending = sum(1 for t in all_tasks if t.status == "pending")

    today = date.today()

    def parse_deadline(deadline_str):
        try:
            return datetime.strptime(deadline_str, "%Y-%m-%d").date()
        except:
            return None

    overdue = sum(1 for t in all_tasks if t.deadline and parse_deadline(t.deadline) and parse_deadline(t.deadline) < today)
    due_today = sum(1 for t in all_tasks if t.deadline and parse_deadline(t.deadline) and parse_deadline(t.deadline) == today)
    future = sum(1 for t in all_tasks if t.deadline and parse_deadline(t.deadline) and parse_deadline(t.deadline) > today)

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "completed": completed,
        "in_progress": in_progress,
        "pending": pending,
        "overdue": overdue,
        "due_today": due_today,
        "future": future
    })
