# 📘 Naman TaskBoard - API Documentation

## 🛠️ Endpoints

### View Tasks
- `GET /view` - Display all tasks (HTML)

### Add Task
- `POST /add` - Add a new task via form
- `POST /add-json` - Add via JSON

### Edit Task
- `POST /edit/{id}` - Edit task by ID
- `PUT /edit-json/{id}` - Edit via JSON

### Delete
- `GET /delete/{id}`

### Generate Task
- `GET /generate` (random task)

## Tags:
- Tags are comma-separated (`urgent,backend`)


# 📘 Project Docs - Naman TaskBoard

## 🔧 Features
- Task Management (CRUD via UI + JSON)
- Login & Session Auth
- Auto Task Generator (Manual + Scheduled)
- CSV Export
- Dashboard with Charts
- Filter by Status, Deadline, Tags

## 🧪 JSON APIs
- GET /items
- POST /add-json
- PUT /edit-json/{id}
- DELETE /delete/{id}
- POST /generate

## 🖥️ Deployment
Compatible with Render/Heroku – see below...

...
