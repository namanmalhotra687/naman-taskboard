from datetime import date, timedelta
from model import SessionLocal, Item

def generate_task(local_kw: str = ""):
    task = {
        "title": f"Auto Task {local_kw}",
        "description": f"Generated automatically with keyword: {local_kw}",
        "status": "pending",
        "deadline": date.today() + timedelta(days=3)
    }
    return task
