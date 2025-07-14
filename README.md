# 📋 Naman TaskBoard

A modern task manager built with FastAPI and Bootstrap. Supports login, task creation, editing, dashboard with charts, task generator (MVP), CSV export, and more.

## 🚀 Features

- ✅ Login / Register system
- ➕ Create tasks via form or generator
- 🧠 MVP-based task generation via keyword
- 📊 Dashboard with pie chart and deadline counters
- 🔍 Search and filter tasks
- 📝 Edit & Delete tasks with modal
- 📤 Export tasks as CSV
- 🔐 Session-based authentication

## 🖥️ Tech Stack

- FastAPI
- Jinja2 Templates
- Bootstrap 5
- SQLite3 (via SQLAlchemy)
- Chart.js
- Python 3.10+

## 🛠️ Getting Started

```bash
# 1. Clone the repo
git clone https://github.com/namanmalhotra687/naman-taskboard.git
cd naman-taskboard

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
uvicorn main:app --reload
