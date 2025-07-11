import requests
import json

tasks = [
    {"title": "Fix login bug", "status": "in progress", "deadline": "2025-07-10"},
    {"title": "Write unit tests", "status": "pending", "deadline": "2025-07-12"},
]

response = requests.post("http://127.0.0.1:8000/generate", json=tasks)

print("📋 Summary:")
print(response.json()["summary"])
