from fastapi.testclient import TestClient
import uuid
from datetime import datetime, timedelta, timezone
from .main import app
from .database import init_db, SessionLocal
from .models import Todo
from .auth import SECRET_KEY, ALGORITHM
from jose import jwt




# ====================
# DB初期化
# ====================

init_db()


# ====================
# TestClient
# ====================

client = TestClient(app)


# ====================
# テスト用ユーザーを作成して
# JWTトークンを取得する
# ====================

def get_token():

    username = f"user_{uuid.uuid4().hex[:8]}"

    response = client.post(
        "/register",
        json={
            "username": username,
            "password": "testpass"
        }
    )

    assert response.status_code == 201


    response = client.post(
        "/login",
        json={
            "username": username,
            "password": "testpass"
        }
    )

    assert response.status_code == 200


    return response.json()["access_token"]


# ====================
# Authorizationヘッダー
# ====================

def auth_header(token):

    return {
        "Authorization": f"Bearer {token}"
    }


# ====================
# 登録テスト
# ====================

def test_register():

    username = f"user_{uuid.uuid4().hex[:8]}"

    response = client.post(
        "/register",
        json={
            "username": username,
            "password": "testpass"
        }
    )

    assert response.status_code == 201

    data = response.json()

    assert data["username"] == username


# ====================
# 重複ユーザー登録テスト
# ====================

def test_register_duplicate():

    username = f"user_{uuid.uuid4().hex[:8]}"

    response = client.post(
        "/register",
        json={
            "username": username,
            "password": "testpass"
        }
    )

    assert response.status_code == 201


    response = client.post(
        "/register",
        json={
            "username": username,
            "password": "testpass"
        }
    )

    assert response.status_code == 400


# ====================
# username入力バリデーションテスト
# ====================

def test_register_username_too_short():
    response = client.post(
        "/register",
        json={
            "username": "ab",
            "password": "testpass"
        }
    )

    assert response.status_code == 422


def test_register_username_too_long():
    response = client.post(
        "/register",
        json={
            "username": "a" * 31,
            "password": "testpass"
        }
    )

    assert response.status_code == 422


def test_register_username_whitespace_only():
    response = client.post(
        "/register",
        json={
            "username": "   ",
            "password": "testpass"
        }
    )

    assert response.status_code == 422


def test_register_username_max_length():
    username = "a" * 26 + uuid.uuid4().hex[:4]

    response = client.post(
        "/register",
        json={
            "username": username,
            "password": "testpass"
        }
    )

    assert response.status_code == 201
    assert response.json()["username"] == username


# ====================
# password入力バリデーションテスト
# ====================

def test_register_password_too_short():
    response = client.post(
        "/register",
        json={
            "username": f"user_{uuid.uuid4().hex[:8]}",
            "password": "abc123"
        }
    )

    assert response.status_code == 422


def test_register_password_whitespace_only():
    response = client.post(
        "/register",
        json={
            "username": f"user_{uuid.uuid4().hex[:8]}",
            "password": "        "
        }
    )

    assert response.status_code == 422


def test_register_password_too_many_utf8_bytes():
    response = client.post(
        "/register",
        json={
            "username": f"user_{uuid.uuid4().hex[:8]}",
            "password": "あ" * 25
        }
    )

    assert response.status_code == 422


# ====================
# ログイン成功テスト
# ====================

def test_login():

    username = f"user_{uuid.uuid4().hex[:8]}"

    client.post(
        "/register",
        json={
            "username": username,
            "password": "testpass"
        }
    )


    response = client.post(
        "/login",
        json={
            "username": username,
            "password": "testpass"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"


# ====================
# ログイン失敗テスト
# ====================

def test_login_invalid_password():

    username = f"user_{uuid.uuid4().hex[:8]}"

    client.post(
        "/register",
        json={
            "username": username,
            "password": "testpass"
        }
    )


    response = client.post(
        "/login",
        json={
            "username": username,
            "password": "wrongpassword"
        }
    )

    assert response.status_code == 401


# ====================
# 認証なしでTodo作成
# ====================

def test_create_todo_without_token():

    response = client.post(
        "/todos",
        json={
            "task": "認証なしテスト"
        }
    )

    assert response.status_code == 401


# ====================
# 不正なJWTトークンのテスト
# ====================

def test_create_todo_with_invalid_token():
    response = client.post(
        "/todos",
        json={"task": "不正トークンテスト"},
        headers=auth_header("invalid.token.value")
    )

    assert response.status_code == 401


def test_get_todos_with_invalid_token():
    response = client.get(
        "/todos",
        headers=auth_header("invalid.token.value")
    )

    assert response.status_code == 401


def test_create_todo_with_expired_token():
    expired_time = datetime.now(timezone.utc) - timedelta(minutes=1)

    token = jwt.encode(
        {
            "user_id": 1,
            "exp": expired_time,
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    response = client.post(
        "/todos",
        json={"task": "期限切れトークンテスト"},
        headers=auth_header(token),
    )

    assert response.status_code == 401


# ====================
# Todo作成テスト
# ====================

def test_create_todo():

    token = get_token()


    response = client.post(
        "/todos",
        json={
            "task": "テストタスク"
        },
        headers=auth_header(token)
    )

    assert response.status_code == 201


    data = response.json()

    assert data["task"] == "テストタスク"
    assert data["done"] is False
    assert data["priority"] == 1
    assert data["due_date"] is None


# ====================
# task入力バリデーションテスト
# ====================

def test_create_todo_empty_task():
    token = get_token()

    response = client.post(
        "/todos",
        json={"task": ""},
        headers=auth_header(token)
    )

    assert response.status_code == 422


def test_create_todo_whitespace_only_task():
    token = get_token()

    response = client.post(
        "/todos",
        json={"task": "   "},
        headers=auth_header(token)
    )

    assert response.status_code == 422


def test_create_todo_task_too_long():
    token = get_token()

    response = client.post(
        "/todos",
        json={"task": "a" * 201},
        headers=auth_header(token)
    )

    assert response.status_code == 422


def test_create_todo_task_max_length():
    token = get_token()

    response = client.post(
        "/todos",
        json={"task": "a" * 200},
        headers=auth_header(token)
    )

    assert response.status_code == 201
    assert response.json()["task"] == "a" * 200


# ====================
# priority 1 テスト
# ====================

def test_create_todo_priority_1():

    token = get_token()


    response = client.post(
        "/todos",
        json={
            "task": "priority 1",
            "priority": 1
        },
        headers=auth_header(token)
    )

    assert response.status_code == 201

    assert response.json()["priority"] == 1


# ====================
# priority 2 テスト
# ====================

def test_create_todo_priority_2():

    token = get_token()


    response = client.post(
        "/todos",
        json={
            "task": "priority 2",
            "priority": 2
        },
        headers=auth_header(token)
    )

    assert response.status_code == 201

    assert response.json()["priority"] == 2


# ====================
# priority 3 テスト
# ====================

def test_create_todo_priority_3():

    token = get_token()


    response = client.post(
        "/todos",
        json={
            "task": "priority 3",
            "priority": 3
        },
        headers=auth_header(token)
    )

    assert response.status_code == 201

    assert response.json()["priority"] == 3


# ====================
# priority 0 拒否テスト
# ====================

def test_create_todo_priority_too_low():

    token = get_token()


    response = client.post(
        "/todos",
        json={
            "task": "priority 0",
            "priority": 0
        },
        headers=auth_header(token)
    )

    assert response.status_code == 422


# ====================
# priority 4 拒否テスト
# ====================

def test_create_todo_priority_too_high():

    token = get_token()


    response = client.post(
        "/todos",
        json={
            "task": "priority 4",
            "priority": 4
        },
        headers=auth_header(token)
    )

    assert response.status_code == 422


# ====================
# priority 999 拒否テスト
# ====================

def test_create_todo_priority_999():

    token = get_token()


    response = client.post(
        "/todos",
        json={
            "task": "priority 999",
            "priority": 999
        },
        headers=auth_header(token)
    )

    assert response.status_code == 422


# ====================
# Todo取得テスト
# ====================

def test_get_todos():

    token = get_token()


    client.post(
        "/todos",
        json={
            "task": "A"
        },
        headers=auth_header(token)
    )


    response = client.get(
        "/todos",
        headers=auth_header(token)
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)


# ====================
# priorityフィルターテスト
# ====================

def test_get_todos_filter():

    token = get_token()


    client.post(
        "/todos",
        json={
            "task": "A",
            "priority": 1
        },
        headers=auth_header(token)
    )


    client.post(
        "/todos",
        json={
            "task": "B",
            "priority": 3
        },
        headers=auth_header(token)
    )


    response = client.get(
        "/todos?priority=3",
        headers=auth_header(token)
    )

    assert response.status_code == 200


    data = response.json()

    assert len(data) >= 1

    assert all(
        todo["priority"] == 3
        for todo in data
    )


# ====================
# doneフィルターテスト
# ====================

def test_get_todos_done_filter():

    token = get_token()


    response = client.post(
        "/todos",
        json={
            "task": "完了テスト"
        },
        headers=auth_header(token)
    )

    todo_id = response.json()["id"]


    client.patch(
        f"/todos/{todo_id}?done=true",
        headers=auth_header(token)
    )


    response = client.get(
        "/todos?done=true",
        headers=auth_header(token)
    )

    assert response.status_code == 200


    data = response.json()

    assert len(data) >= 1

    assert all(
        todo["done"] is True
        for todo in data
    )


# ====================
# limitフィルターテスト
# ====================

def test_get_todos_limit_max():
    token = get_token()

    for i in range(100):
        response = client.post(
            "/todos",
            json={
                "task": f"limit{i}"
            },
            headers=auth_header(token)
        )

        assert response.status_code == 201

    response = client.get(
        "/todos?limit=1",
        headers=auth_header(token)
    )

    assert response.status_code == 200
    assert len(response.json()) == 1

    response = client.get(
        "/todos?limit=100",
        headers=auth_header(token)
    )

    assert response.status_code == 200
    assert len(response.json()) == 100


# ====================
# priorityクエリパラメータ制限テスト
# ====================

def test_get_todos_priority_too_low():
    token = get_token()

    response = client.get(
        "/todos?priority=0",
        headers=auth_header(token)
    )

    assert response.status_code == 422


def test_get_todos_priority_too_high():
    token = get_token()

    response = client.get(
        "/todos?priority=4",
        headers=auth_header(token)
    )

    assert response.status_code == 422


# ====================
# skip制限テスト
# ====================

def test_get_todos_skip_negative():
    token = get_token()

    response = client.get(
        "/todos?skip=-1",
        headers=auth_header(token)
    )

    assert response.status_code == 422


# ====================
# limit制限テスト
# ====================

def test_get_todos_limit_too_low():
    token = get_token()

    response = client.get(
        "/todos?limit=0",
        headers=auth_header(token)
    )

    assert response.status_code == 422


def test_get_todos_limit_too_high():
    token = get_token()

    response = client.get(
        "/todos?limit=101",
        headers=auth_header(token)
    )

    assert response.status_code == 422


# ====================
# 作成日時ソートテスト
# ====================

def test_sort_todos():

    token = get_token()


    res1 =client.post(
        "/todos",
        json={
            "task": "A"
        },
        headers=auth_header(token)
    )


    res2 =client.post(
        "/todos",
        json={
            "task": "B"
        },
        headers=auth_header(token)
    )

    assert res1.status_code == 201
    assert res2.status_code == 201

    todo1_id = res1.json()["id"]
    todo2_id = res2.json()["id"]

    same_time = datetime(2030, 1, 1, 12, 0, 0)

    db = SessionLocal()

    try:
        db.query(Todo).filter(Todo.id.in_([todo1_id, todo2_id])).update(
            {Todo.created_at: same_time}, synchronize_session=False)

        db.commit()

    finally:
        db.close()
        

    response = client.get(
        "/todos?sort_by=created",
        headers=auth_header(token)
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2

    assert [todo["id"] for todo in data] == sorted([todo1_id, todo2_id])


# ====================
# 期限ソートテスト
# ====================

def test_sort_todos_by_due_date():

    token = get_token()


    res1 =client.post(
        "/todos",
        json={
            "task": "A",
            "due_date": "2030-01-02T10:00:00",
        },
        headers=auth_header(token)
    )


    res2 = client.post(
        "/todos",
        json={
            "task": "B",
            "due_date": "2030-01-01T10:00:00",
        },
        headers=auth_header(token)
    )

    assert res1.status_code == 201
    assert res2.status_code == 201


    response = client.get(
        "/todos?sort_by=due",
        headers=auth_header(token)
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2

    assert data[0]["task"] == "B"
    assert data[1]["task"] == "A"


# ====================
# 期限未設定のTodoを最後にするテスト
# ====================

def test_sort_todos_due_date_none_last():

    token = get_token()

    
    res1 = client.post(
        "/todos",
        json={
            "task": "期限が遅い",
            "due_date": "2030-01-03T10:00:00"
        },
        headers=auth_header(token)
    )

    
    res2 = client.post(
        "/todos",
        json={
            "task": "期限なし"
        },
        headers=auth_header(token)
    )

    
    res3 = client.post(
        "/todos",
        json={
            "task": "期限が早い",
            "due_date": "2030-01-01T10:00:00"
        },
        headers=auth_header(token)
    )

    assert res1.status_code == 201
    assert res2.status_code == 201
    assert res3.status_code == 201

    response = client.get(
        "/todos?sort_by=due",
        headers=auth_header(token)
    )

    assert response.status_code == 200

    data = response.json()

    assert [
        todo["task"] for todo in data
    ] == [
        "期限が早い",
        "期限が遅い",
        "期限なし"
    ]


# ====================
# 同じ期限ならIDの小さい順にするテスト
# ====================

def test_sort_todos_same_due_date_by_id():

    token = get_token()

    same_due_date = "2030-01-01T10:00:00"

    res1 = client.post(
        "/todos",
        json={
            "task": "同じ期限A",
            "due_date": same_due_date
        },
        headers=auth_header(token)
    )

    res2 = client.post(
        "/todos",
        json={
            "task": "同じ期限B",
            "due_date": same_due_date
        },
        headers=auth_header(token)
    )

    assert res1.status_code == 201
    assert res2.status_code == 201

    todo1_id = res1.json()["id"]
    todo2_id = res2.json()["id"]

    response = client.get(
        "/todos?sort_by=due",
        headers=auth_header(token)
    )

    assert response.status_code == 200

    data = response.json()

    assert [todo["id"] for todo in data] == sorted([todo1_id, todo2_id])


# ====================
# sort_by制限テスト
# ====================

def test_get_todos_invalid_sort_by():
    token = get_token()

    response = client.get(
        "/todos?sort_by=invalid",
        headers=auth_header(token)
    )

    assert response.status_code == 422


# ====================
# Todo更新テスト
# ====================

def test_update_todo():

    token = get_token()


    response = client.post(
        "/todos",
        json={
            "task": "更新テスト"
        },
        headers=auth_header(token)
    )

    todo_id = response.json()["id"]


    response = client.patch(
        f"/todos/{todo_id}?done=true",
        headers=auth_header(token)
    )

    assert response.status_code == 200


    data = response.json()

    assert data["done"] is True


# ====================
# Todoを未完了に戻すテスト
# ====================

def test_update_todo_to_false():

    token = get_token()


    response = client.post(
        "/todos",
        json={
            "task": "未完了に戻すテスト"
        },
        headers=auth_header(token)
    )

    todo_id = response.json()["id"]


    client.patch(
        f"/todos/{todo_id}?done=true",
        headers=auth_header(token)
    )


    response = client.patch(
        f"/todos/{todo_id}?done=false",
        headers=auth_header(token)
    )

    assert response.status_code == 200

    assert response.json()["done"] is False


# ====================
# Todo削除テスト
# ====================

def test_delete_todo():

    token = get_token()


    response = client.post(
        "/todos",
        json={
            "task": "削除テスト"
        },
        headers=auth_header(token)
    )

    todo_id = response.json()["id"]


    response = client.delete(
        f"/todos/{todo_id}",
        headers=auth_header(token)
    )

    assert response.status_code == 204


# ====================
# 削除後に存在しないことを確認
# ====================

def test_delete_todo_and_check_not_found():

    token = get_token()


    response = client.post(
        "/todos",
        json={
            "task": "削除確認テスト"
        },
        headers=auth_header(token)
    )

    todo_id = response.json()["id"]


    delete_response = client.delete(
        f"/todos/{todo_id}",
        headers=auth_header(token)
    )

    assert delete_response.status_code == 204


    update_response = client.patch(
        f"/todos/{todo_id}?done=true",
        headers=auth_header(token)
    )

    assert update_response.status_code == 404


# ====================
# 存在しないTodo更新
# ====================

def test_not_found():

    token = get_token()


    response = client.patch(
        "/todos/999999999?done=true",
        headers=auth_header(token)
    )

    assert response.status_code == 404


# ====================
# 他ユーザーのTodoを更新できない
# ====================

def test_cannot_update_other_users_todo():

    token1 = get_token()
    token2 = get_token()


    response = client.post(
        "/todos",
        json={
            "task": "ユーザー1のTodo"
        },
        headers=auth_header(token1)
    )

    todo_id = response.json()["id"]


    response = client.patch(
        f"/todos/{todo_id}?done=true",
        headers=auth_header(token2)
    )

    assert response.status_code == 404


# ====================
# 他ユーザーのTodoを削除できない
# ====================

def test_cannot_delete_other_users_todo():

    token1 = get_token()
    token2 = get_token()


    response = client.post(
        "/todos",
        json={
            "task": "ユーザー1のTodo"
        },
        headers=auth_header(token1)
    )

    todo_id = response.json()["id"]


    response = client.delete(
        f"/todos/{todo_id}",
        headers=auth_header(token2)
    )

    assert response.status_code == 404


# ====================
# 他ユーザーのTodoが取得結果に出ない
# ====================

def test_cannot_get_other_users_todos():

    token1 = get_token()
    token2 = get_token()


    client.post(
        "/todos",
        json={
            "task": "ユーザー1だけのTodo"
        },
        headers=auth_header(token1)
    )

    client.post(
        "/todos",
        json={
            "task": "ユーザー2だけのTodo"
        },
        headers=auth_header(token2)
    )

    response = client.get(
        "/todos",
        headers=auth_header(token2)
    )

    assert response.status_code == 200


    data = response.json()

    assert any(
        todo["task"] == "ユーザー2だけのTodo"
        for todo in data
    )

    assert all(
        todo["task"] != "ユーザー1だけのTodo"
        for todo in data
    )


# ====================
# ページネーションテスト
# ====================

def test_pagination():

    token = get_token()


    for i in range(15):

        response = client.post(
            "/todos",
            json={
                "task": f"task{i}"
            },
            headers=auth_header(token)
        )

        assert response.status_code == 201


    # 1ページ目
    response = client.get(
        "/todos?skip=0&limit=10",
        headers=auth_header(token)
    )

    assert response.status_code == 200

    assert len(response.json()) == 10


    # 2ページ目
    response = client.get(
        "/todos?skip=10&limit=10",
        headers=auth_header(token)
    )

    assert response.status_code == 200

    assert len(response.json()) == 5


# ====================
# ページネーション空ページ
# ====================

def test_pagination_empty_page():

    token = get_token()


    for i in range(10):

        response = client.post(
            "/todos",
            json={
                "task": f"pagination{i}"
            },
            headers=auth_header(token)
        )

        assert response.status_code == 201


    response = client.get(
        "/todos?skip=10&limit=10",
        headers=auth_header(token)
    )

    assert response.status_code == 200

    assert response.json() == []


# ====================
# 完了済みフィルターとページネーションの組み合わせテスト
# ====================


def test_done_filter_with_pagination():
    token = get_token()
    headers = auth_header(token)

    
    for i in range(12):
        create_response = client.post(
            "/todos",
            json={"task": f"完了済みTodo{i}"},
            headers=headers,
        )
        assert create_response.status_code == 201

        todo_id = create_response.json()["id"]

        update_response = client.patch(
            f"/todos/{todo_id}?done=true",
            headers=headers,
        )
        assert update_response.status_code == 200

    
    for i in range(3):
        response = client.post(
            "/todos",
            json={"task": f"未完了Todo{i}"},
            headers=headers,
        )
        assert response.status_code == 201

    
    page1 = client.get(
        "/todos?done=true&skip=0&limit=10",
        headers=headers,
    )
    assert page1.status_code == 200
    page1_data = page1.json()
    assert len(page1_data) == 10
    assert all(todo["done"] is True for todo in page1_data)

    
    page2 = client.get(
        "/todos?done=true&skip=10&limit=10",
        headers=headers,
    )
    assert page2.status_code == 200
    page2_data = page2.json()
    assert len(page2_data) == 2
    assert all(todo["done"] is True for todo in page2_data)


# ====================
# 優先度フィルターとページネーションの組み合わせテスト
# ====================

def test_priority_filter_with_pagination():
    token = get_token()
    headers = auth_header(token)

    
    for i in range(12):
        response = client.post(
            "/todos",
            json={
                "task": f"優先度2のTodo{i}",
                "priority": 2,
            },
            headers=headers,
        )
        assert response.status_code == 201

    
    for i in range(3):
        response = client.post(
            "/todos",
            json={
                "task": f"優先度1のTodo{i}",
                "priority": 1,
            },
            headers=headers,
        )
        assert response.status_code == 201

    
    page1 = client.get(
        "/todos?priority=2&skip=0&limit=10",
        headers=headers,
    )
    assert page1.status_code == 200

    page1_data = page1.json()
    assert len(page1_data) == 10
    assert all(todo["priority"] == 2 for todo in page1_data)

    
    page2 = client.get(
        "/todos?priority=2&skip=10&limit=10",
        headers=headers,
    )
    assert page2.status_code == 200

    page2_data = page2.json()
    assert len(page2_data) == 2
    assert all(todo["priority"] == 2 for todo in page2_data)
