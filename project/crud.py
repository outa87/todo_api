import logging
from datetime import datetime

from passlib.context import CryptContext
from sqlalchemy import case
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from .models import MAX_PASSWORD_BYTES, Todo, User

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ====================
# パスワード
# ====================

def hash_password(password: str) -> str:
    pw_bytes = password.encode("utf-8")

    if len(pw_bytes) > MAX_PASSWORD_BYTES:
        raise ValueError(f"password must not exceed {MAX_PASSWORD_BYTES} UTF-8 bytes")

    return pwd_context.hash(pw_bytes)


def verify_password(plain: str, hashed: str) -> bool:
    pw_bytes = plain.encode("utf-8")

    if len(pw_bytes) > MAX_PASSWORD_BYTES:
        return False

    return pwd_context.verify(pw_bytes, hashed)


# ====================
# ユーザー
# ====================

def create_user(db: Session, username: str, password: str) -> User:
    user = User(username=username, hashed_password=hash_password(password))

    try:
        db.add(user)
        db.commit()
        db.refresh(user)
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"[create_user] Failed to create user: {e}")
        raise

    logger.info(f"[create_user] Created user id={user.id}, username='{user.username}'")
    return user


def get_user_by_username(db: Session, username: str) -> User | None:
    return db.query(User).filter(User.username == username).first()


# ====================
# Todo
# ====================

def _get_owned_todo(db: Session, todo_id: int, user_id: int) -> Todo | None:
    """自分のTodoだけを取得する（他人のTodoは見つからない扱い）"""
    return (
        db.query(Todo)
        .filter(Todo.id == todo_id, Todo.user_id == user_id)
        .first()
    )


def add_todo(
    db: Session,
    task: str,
    user_id: int,
    due_date: datetime | None = None,
    priority: int = 1,
) -> Todo:
    logger.info(f"[add_todo] start task='{task}', user_id={user_id}")

    new_todo = Todo(
        task=task,
        done=False,
        user_id=user_id,
        due_date=due_date,
        priority=priority,
    )

    try:
        db.add(new_todo)
        db.commit()
        db.refresh(new_todo)
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"[add_todo] failed: {e}")
        raise

    logger.info(f"[add_todo] success id={new_todo.id}")
    return new_todo


def get_user_todos(
    db: Session,
    user_id: int,
    done: bool | None = None,
    priority: int | None = None,
    sort_by: str | None = None,
    skip: int = 0,
    limit: int = 10,
) -> list[Todo]:
    logger.info(f"[get_user_todos] start user_id={user_id}")

    query = db.query(Todo).filter(Todo.user_id == user_id)

    if done is not None:
        query = query.filter(Todo.done == done)
    if priority is not None:
        query = query.filter(Todo.priority == priority)

    if sort_by == "created":
        order = (Todo.created_at.asc(), Todo.id.asc())
    elif sort_by == "due":
        # 期限なしを最後に、同じ期限ならID順
        order = (
            case((Todo.due_date.is_(None), 1), else_=0).asc(),
            Todo.due_date.asc(),
            Todo.id.asc(),
        )
    else:
        # 並び順の指定がなくてもページネーションがズレないようにIDで固定
        order = (Todo.id.asc(),)

    todos = query.order_by(*order).offset(skip).limit(limit).all()

    logger.info(f"[get_user_todos] Fetched {len(todos)} todos")
    return todos


def update_todo(db: Session, todo_id: int, user_id: int, done: bool) -> Todo | None:
    logger.info(f"[update_todo] start id={todo_id}, user_id={user_id}, done={done}")

    todo = _get_owned_todo(db, todo_id, user_id)
    if not todo:
        logger.warning(f"[update_todo] not found or unauthorized id={todo_id}")
        return None

    old_done = todo.done
    todo.done = done

    try:
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"[update_todo] failed id={todo_id}: {e}")
        raise

    logger.info(f"[update_todo] success id={todo_id}, {old_done} -> {done}")
    return todo


def delete_todo(db: Session, todo_id: int, user_id: int) -> Todo | None:
    logger.info(f"[delete_todo] start id={todo_id}, user_id={user_id}")

    todo = _get_owned_todo(db, todo_id, user_id)
    if not todo:
        logger.warning(f"[delete_todo] not found or unauthorized id={todo_id}")
        return None

    try:
        db.delete(todo)
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"[delete_todo] failed id={todo_id}: {e}")
        raise

    logger.info(f"[delete_todo] success id={todo_id}")
    return todo