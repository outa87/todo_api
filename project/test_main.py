from fastapi.testclient import TestClient
from project.main import app
import uuid

client = TestClient(app)

def get_token():
    username = f"user_{uuid.uuid4()}"
    client.post("/register", json={"username": username, "password": "testpass"})
    res = client.post("/login", json={"username": username, "password": "testpass"})
    return res.json()["access_token"]

def test_create_todo():
    token = get_token()
    response = client.post("/todos", json={"task": "テストタスク"}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 201

    data = response.json()
    assert data["task"] == "テストタスク"
    assert data["done"] == False

def test_get_todos_filter():
    token = get_token()
    client.post("/todo", json={"task": "A", "priority": 1}, headers={"Authorization": f"Bearer {token}"})
    client.post("/todo", json={"task": "B", "priority": 3}, headers={"Authorization": f"Bearer {token}"})

    response = client.get("/todos?priority=3", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    
    data = response.json()
    assert all(todo["priority"] == 3 for todo in data)

def test_sort_todos():
    token = get_token()
    client.post("/todo", json={"task": "A"}, headers={"Authorization": f"Bearer {token}"})
    client.post("/todo", json={"task": "B"}, headers={"Authorization": f"Bearer {token}"})
    
    response = client.get("/todos?sort_by=created", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200

def test_update_todo():
    token = get_token()
    res = client.post("/todos", json={"task": "更新テスト"}, headers={"Authorization": f"Bearer {token}"})
    todo_id = res.json()["id"]

    response = client.patch(f"/todos/{todo_id}?done=true", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200

    data = response.json()
    assert data["done"] == True

def test_delete_todo():
    token = get_token()
    res = client.post("/todos", json={"task": "削除テスト"}, headers={"Authorization": f"Bearer {token}"})
    todo_id = res.json()["id"]

    response = client.delete(f"/todos/{todo_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 204
    
def test_not_found():
    token = get_token()
    response = client.patch("/todos/9999?done=true", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404

def test_pagination():
    token = get_token()

    for i in range(15):
        client.post("/todos", json={"task": f"task{i}"}, headers={"Authorization": f"Bearer {token}"})
    res1 = client.get("/todos?skip=0&limit=10", headers={"Authorization": f"Bearer {token}"})
    assert len(res1.json()) == 10

    res2 = client.get("/todos?skip=10&limit=10", headers={"Authorization": f"Bearer {token}"})
    assert len(res2.json()) == 5