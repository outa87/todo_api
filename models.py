from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

MAX_PASSWORD_BYTES = 72


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ====================
# DBモデル
# ====================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    todos = relationship("Todo", back_populates="owner")


class Todo(Base):
    __tablename__ = "todos"

    id = Column(Integer, primary_key=True)
    task = Column(String, nullable=False)
    done = Column(Boolean, default=False, nullable=False)

    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    owner = relationship("User", back_populates="todos")

    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    due_date = Column(DateTime, nullable=True)
    priority = Column(Integer, default=1, nullable=False)


# ====================
# APIスキーマ: ユーザー
# ====================

class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=30)
    password: str = Field(min_length=8, max_length=MAX_PASSWORD_BYTES)

    @field_validator("username", mode="before")
    @classmethod
    def validate_username(cls, value):
        if isinstance(value, str):
            value = value.strip()
            if not value:
                raise ValueError("username cannot be empty or whitespace only")
        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value):
        if not value.strip():
            raise ValueError("password cannot be empty or whitespace only")

        if len(value.encode("utf-8")) > MAX_PASSWORD_BYTES:
            raise ValueError(f"password must not exceed {MAX_PASSWORD_BYTES} UTF-8 bytes")

        return value


class UserResponse(BaseModel):
    id: int
    username: str

    model_config = ConfigDict(from_attributes=True)


# ====================
# APIスキーマ: Todo
# ====================

class TodoCreate(BaseModel):
    task: str = Field(min_length=1, max_length=200)
    due_date: datetime | None = None
    priority: int = Field(default=1, ge=1, le=3)

    @field_validator("task", mode="before")
    @classmethod
    def validate_task(cls, value):
        if isinstance(value, str):
            value = value.strip()
            if not value:
                raise ValueError("task cannot be empty or whitespace only")
        return value


class TodoResponse(BaseModel):
    id: int
    task: str
    done: bool
    created_at: datetime
    updated_at: datetime
    due_date: datetime | None
    priority: int

    model_config = ConfigDict(from_attributes=True)