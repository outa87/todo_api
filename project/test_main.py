import random
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from .auth import ALGORITHM, SECRET_KEY
from .database import SessionLocal, init_db
from .main import app
from .models import Todo

client = TestClient(app)

PASSWORD = "testpass"


# ====================
# フィクスチャ
# ====================

@pytest.fixture(scope="session", autouse=True)
def _init_db():
    init_db()


@pytest.fixture
def headers():
    """テストごとに新規ユーザーを作り、認証ヘッダーを返す"""
    return make_auth_headers()


@pytest.fixture
def other_headers():
    """別ユーザーの認証ヘッダー"""
    return make_auth_headers()


# ====================
# ヘルパー
# ====================

def unique_username():
    return f"user_{uuid.uuid4().hex[:8]}"


def username_of_length(length):
    """指定した文字数で、重複しにくいユーザー名を作る

    todo.db が残るので、短い名前を英数字で作ると過去の実行と衝突しうる。
    衝突しにくい漢字で作る（文字数は len() で数えるので境界値テストに使える）。
    """
    return "".join(chr(random.randint(0x4E00, 0x9FA5)) for _ in range(length))


def register(username, password=PASSWORD):
    return client.post("/register", json={"username": username, "password": password})


def login(username, password=PASSWORD):
    return client.post("/login", json={"username": username, "password": password})


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


def make_auth_headers():
    username = unique_username()
    assert register(username).status_code == 201

    response = login(username)
    assert response.status_code == 200

    return bearer(response.json()["access_token"])


def make_jwt(payload, key=SECRET_KEY):
    return jwt.encode(payload, key, algorithm=ALGORITHM)


def create_todo(headers, task="task", **fields):
    """Todoを作成してレスポンスJSONを返す（201は常に検証する）"""
    response = client.post(
        "/todos",
        json={"task": task, **fields},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_done_todo(headers, task="done"):
    """完了済みのTodoを作る（doneがTrueになったことも検証する）"""
    todo = create_todo(headers, task)

    response = set_done(headers, todo["id"], True)
    assert response.status_code == 200
    assert response.json()["done"] is True

    return todo


def set_done(headers, todo_id, done):
    """doneを更新してレスポンスを返す（404テストでも使うので検証しない）"""
    return client.patch(
        f"/todos/{todo_id}?done={'true' if done else 'false'}",
        headers=headers,
    )


def get_todos(headers, query=""):
    return client.get(f"/todos{query}", headers=headers)


# ====================
# 登録
# ====================

def test_register():
    username = unique_username()

    response = register(username)

    assert response.status_code == 201
    assert response.json()["username"] == username


def test_register_duplicate():
    username = unique_username()

    assert register(username).status_code == 201
    assert register(username).status_code == 400


def test_register_username_is_stripped():
    username = unique_username()

    response = register(f"  {username}  ")

    assert response.status_code == 201
    assert response.json()["username"] == username


@pytest.mark.parametrize("length", [3, 30], ids=["min_3", "max_30"])
def test_register_valid_username_length(length):
    username = username_of_length(length)

    response = register(username)

    assert response.status_code == 201
    assert response.json()["username"] == username


@pytest.mark.parametrize(
    "username",
    ["ab", "a" * 31, "   ", "  ab  "],
    ids=["2_chars", "31_chars", "whitespace", "2_chars_after_strip"],
)
def test_register_invalid_username(username):
    assert register(username).status_code == 422


@pytest.mark.parametrize(
    "password",
    ["a" * 8, "a" * 72, "あ" * 24],
    ids=["min_8_chars", "max_72_bytes_ascii", "max_72_bytes_utf8"],
)
def test_register_valid_password_length(password):
    # "あ" は UTF-8 で3バイト → 24文字でちょうど72バイト
    assert register(unique_username(), password).status_code == 201


@pytest.mark.parametrize(
    "password",
    ["a" * 7, "        ", "a" * 73, "あ" * 24 + "a"],
    ids=["7_chars", "whitespace", "73_chars", "73_bytes_utf8"],
)
def test_register_invalid_password(password):
    assert register(unique_username(), password).status_code == 422


# ====================
# ログイン
# ====================

def test_login():
    username = unique_username()
    assert register(username).status_code == 201

    response = login(username)

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_password():
    username = unique_username()
    assert register(username).status_code == 201

    assert login(username, "wrongpassword").status_code == 401


def test_login_unknown_user():
    assert login(unique_username()).status_code == 401


# ====================
# 認証（JWT）
# ====================

@pytest.mark.parametrize(
    "method, path, body",
    [
        ("post", "/todos", {"task": "認証なし"}),
        ("get", "/todos", None),
        ("patch", "/todos/1?done=true", None),
        ("delete", "/todos/1", None),
    ],
    ids=["post_todos", "get_todos", "patch_todo", "delete_todo"],
)
def test_endpoints_require_token(method, path, body):
    response = client.request(method, path, json=body)

    assert response.status_code == 401


@pytest.mark.parametrize(
    "token",
    [
        pytest.param("invalid.token.value", id="malformed"),
        pytest.param(
            make_jwt({
                "user_id": 1,
                "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
            }),
            id="expired",
        ),
        pytest.param(
            make_jwt(
                {"user_id": 1, "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
                key="wrong-secret-key-wrong-secret-key",
            ),
            id="wrong_key",
        ),
        pytest.param(
            make_jwt({"exp": datetime.now(timezone.utc) + timedelta(hours=1)}),
            id="no_user_id",
        ),
    ],
)
def test_bad_token_is_rejected(token):
    # 認証は全エンドポイント共通の依存関係なので、GET /todos で代表して確認する
    # （各エンドポイントが認証を要求することは test_endpoints_require_token で確認）
    assert get_todos(bearer(token)).status_code == 401


# ====================
# Todo作成
# ====================

def test_create_todo(headers):
    data = create_todo(headers, "テストタスク")

    assert data["task"] == "テストタスク"
    assert data["done"] is False
    assert data["priority"] == 1
    assert data["due_date"] is None


def test_create_todo_with_due_date(headers):
    data = create_todo(headers, "期限あり", due_date="2030-01-01T10:00:00")

    assert data["due_date"].startswith("2030-01-01T10:00:00")


def test_create_todo_task_is_stripped(headers):
    assert create_todo(headers, "  trim  ")["task"] == "trim"


@pytest.mark.parametrize("length", [1, 200], ids=["min_1", "max_200"])
def test_create_todo_valid_task_length(headers, length):
    task = "a" * length

    assert create_todo(headers, task)["task"] == task


@pytest.mark.parametrize("task", ["", "   ", "a" * 201], ids=["empty", "whitespace", "too_long"])
def test_create_todo_invalid_task(headers, task):
    response = client.post("/todos", json={"task": task}, headers=headers)

    assert response.status_code == 422


@pytest.mark.parametrize("priority", [1, 2, 3])
def test_create_todo_valid_priority(headers, priority):
    assert create_todo(headers, f"priority {priority}", priority=priority)["priority"] == priority


@pytest.mark.parametrize("priority", [0, 4])
def test_create_todo_invalid_priority(headers, priority):
    response = client.post(
        "/todos",
        json={"task": f"priority {priority}", "priority": priority},
        headers=headers,
    )

    assert response.status_code == 422


# ====================
# Todo取得・フィルター
# ====================

def test_get_todos(headers):
    create_todo(headers, "A")

    response = get_todos(headers)

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_get_todos_default_order_is_id_asc(headers):
    ids = [create_todo(headers, f"task{i}")["id"] for i in range(5)]

    response = get_todos(headers)

    assert response.status_code == 200
    assert [t["id"] for t in response.json()] == ids


@pytest.mark.parametrize("priority", [1, 2, 3])
def test_get_todos_priority_filter(headers, priority):
    for p in (1, 2, 3):
        create_todo(headers, f"priority {p}", priority=p)

    response = get_todos(headers, f"?priority={priority}")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["priority"] == priority


def test_get_todos_done_filter(headers):
    create_done_todo(headers, "完了")
    create_todo(headers, "未完了")

    response = get_todos(headers, "?done=true")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["done"] is True


def test_get_todos_limit(headers):
    for i in range(100):
        create_todo(headers, f"limit{i}")

    # 100件作るのが重いので、parametrizeにせず1テストの中で両方確認する
    for limit in (1, 100):
        response = get_todos(headers, f"?limit={limit}")

        assert response.status_code == 200
        assert len(response.json()) == limit


@pytest.mark.parametrize(
    "query",
    [
        "?priority=0",
        "?priority=4",
        "?skip=-1",
        "?limit=0",
        "?limit=101",
        "?sort_by=invalid",
    ],
)
def test_get_todos_invalid_query(headers, query):
    assert get_todos(headers, query).status_code == 422


# ====================
# ソート
# ====================

def test_sort_todos_by_created(headers):
    """作成日時が同じ場合はIDの小さい順になる"""
    ids = [create_todo(headers, "A")["id"], create_todo(headers, "B")["id"]]

    db = SessionLocal()
    try:
        db.query(Todo).filter(Todo.id.in_(ids)).update(
            {Todo.created_at: datetime(2030, 1, 1, 12, 0, 0)},
            synchronize_session=False,
        )
        db.commit()
    finally:
        db.close()

    response = get_todos(headers, "?sort_by=created")

    assert response.status_code == 200
    assert [t["id"] for t in response.json()] == sorted(ids)


def test_sort_todos_by_due_date(headers):
    create_todo(headers, "A", due_date="2030-01-02T10:00:00")
    create_todo(headers, "B", due_date="2030-01-01T10:00:00")

    response = get_todos(headers, "?sort_by=due")

    assert response.status_code == 200
    assert [t["task"] for t in response.json()] == ["B", "A"]


def test_sort_todos_due_date_none_last(headers):
    create_todo(headers, "期限が遅い", due_date="2030-01-03T10:00:00")
    create_todo(headers, "期限なし")
    create_todo(headers, "期限が早い", due_date="2030-01-01T10:00:00")

    response = get_todos(headers, "?sort_by=due")

    assert response.status_code == 200
    assert [t["task"] for t in response.json()] == ["期限が早い", "期限が遅い", "期限なし"]


def test_sort_todos_same_due_date_by_id(headers):
    due = "2030-01-01T10:00:00"
    ids = [
        create_todo(headers, "同じ期限A", due_date=due)["id"],
        create_todo(headers, "同じ期限B", due_date=due)["id"],
    ]

    response = get_todos(headers, "?sort_by=due")

    assert response.status_code == 200
    assert [t["id"] for t in response.json()] == sorted(ids)


# ====================
# ページネーション
# ====================

@pytest.mark.parametrize(
    "skip, limit, expected_len",
    [
        (0, 10, 10),
        (10, 10, 5),
        (15, 10, 0),
    ],
    ids=["first_page", "second_page_partial", "empty_page"],
)
def test_pagination(headers, skip, limit, expected_len):
    for i in range(15):
        create_todo(headers, f"task{i}")

    response = get_todos(headers, f"?skip={skip}&limit={limit}")

    assert response.status_code == 200
    assert len(response.json()) == expected_len


@pytest.mark.parametrize("skip, expected_len", [(0, 10), (10, 2)], ids=["first_page", "last_page"])
def test_done_filter_with_pagination(headers, skip, expected_len):
    for i in range(12):
        create_done_todo(headers, f"完了済み{i}")
    for i in range(3):
        create_todo(headers, f"未完了{i}")

    response = get_todos(headers, f"?done=true&skip={skip}&limit=10")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == expected_len
    assert all(t["done"] is True for t in data)


@pytest.mark.parametrize("skip, expected_len", [(0, 10), (10, 2)], ids=["first_page", "last_page"])
def test_priority_filter_with_pagination(headers, skip, expected_len):
    for i in range(12):
        create_todo(headers, f"優先度2の{i}", priority=2)
    for i in range(3):
        create_todo(headers, f"優先度1の{i}", priority=1)

    response = get_todos(headers, f"?priority=2&skip={skip}&limit=10")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == expected_len
    assert all(t["priority"] == 2 for t in data)


# ====================
# Todo更新
# ====================

def test_update_todo(headers):
    todo = create_todo(headers, "更新テスト")

    response = set_done(headers, todo["id"], True)

    assert response.status_code == 200
    assert response.json()["done"] is True


def test_update_todo_to_false(headers):
    todo = create_done_todo(headers, "未完了に戻すテスト")

    response = set_done(headers, todo["id"], False)

    assert response.status_code == 200
    assert response.json()["done"] is False


def test_update_todo_not_found(headers):
    assert set_done(headers, 999999999, True).status_code == 404


# ====================
# Todo削除
# ====================

def test_delete_todo(headers):
    todo = create_todo(headers, "削除テスト")

    response = client.delete(f"/todos/{todo['id']}", headers=headers)

    assert response.status_code == 204


def test_deleted_todo_is_not_found(headers):
    todo = create_todo(headers, "削除確認テスト")

    assert client.delete(f"/todos/{todo['id']}", headers=headers).status_code == 204
    assert set_done(headers, todo["id"], True).status_code == 404


def test_delete_todo_not_found(headers):
    assert client.delete("/todos/999999999", headers=headers).status_code == 404


# ====================
# 他ユーザーとの分離
# ====================

def test_cannot_update_other_users_todo(headers, other_headers):
    todo = create_todo(headers, "ユーザー1のTodo")

    assert set_done(other_headers, todo["id"], True).status_code == 404


def test_cannot_delete_other_users_todo(headers, other_headers):
    todo = create_todo(headers, "ユーザー1のTodo")

    assert client.delete(f"/todos/{todo['id']}", headers=other_headers).status_code == 404


def test_cannot_get_other_users_todos(headers, other_headers):
    create_todo(headers, "ユーザー1だけのTodo")
    create_todo(other_headers, "ユーザー2だけのTodo")

    response = get_todos(other_headers)

    assert response.status_code == 200
    assert [t["task"] for t in response.json()] == ["ユーザー2だけのTodo"]
