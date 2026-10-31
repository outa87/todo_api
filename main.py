import logging
from pathlib import Path
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .auth import create_access_token, verify_token
from .crud import (
    add_todo,
    create_user,
    delete_todo,
    get_user_by_username,
    get_user_todos,
    update_todo,
    verify_password,
)
from .database import get_db, init_db
from .models import TodoCreate, TodoResponse, UserCreate, UserResponse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

FRONTEND_DIR = Path(__file__).resolve().parent / "frontend"

security = HTTPBearer()
app = FastAPI()
init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")


# ====================
# 認証
# ====================

def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> int:
    payload = verify_token(credentials.credentials)
    user_id = payload.get("user_id") if payload else None

    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return user_id


@app.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, db: Session = Depends(get_db)):
    logger.info(f"[register] attempt username={user.username}")

    if get_user_by_username(db, user.username):
        logger.warning(f"[register] already exists username={user.username}")
        raise HTTPException(status_code=400, detail="Username already exists")

    try:
        new_user = create_user(db, user.username, user.password)
    except IntegrityError:
        # 同時登録などで上のチェックをすり抜けた場合
        raise HTTPException(status_code=400, detail="Username already exists")

    logger.info(f"[register] success user_id={new_user.id}")
    return new_user


@app.post("/login")
def login(user: UserCreate, db: Session = Depends(get_db)):
    logger.info(f"[login] attempt username={user.username}")

    db_user = get_user_by_username(db, user.username)
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        logger.warning(f"[login] failed username={user.username}")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"user_id": db_user.id})
    logger.info(f"[login] success user_id={db_user.id}")
    return {"access_token": token, "token_type": "bearer"}


# ====================
# Todo
# ====================

@app.post("/todos", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
def create_todo(
    todo: TodoCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    logger.info(f"[create_todo] user_id={user_id}, task='{todo.task}'")
    return add_todo(db, todo.task, user_id, todo.due_date, todo.priority)


@app.get("/todos", response_model=list[TodoResponse])
def get_todos(
    done: bool | None = None,
    priority: int | None = Query(default=None, ge=1, le=3),
    sort_by: Literal["created", "due"] | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    logger.info(f"[get_todos] user_id={user_id}, skip={skip}, limit={limit}")
    return get_user_todos(db, user_id, done, priority, sort_by, skip, limit)


@app.patch("/todos/{todo_id}", response_model=TodoResponse)
def update(
    todo_id: int,
    done: bool,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    todo = update_todo(db, todo_id, user_id, done)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo


@app.delete("/todos/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(
    todo_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    todo = delete_todo(db, todo_id, user_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")