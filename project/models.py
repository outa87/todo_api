from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, relationship
from pydantic import BaseModel
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    todos = relationship("Todo", back_populates="owner")

class Todo(Base):
    __tablename__ = "todos"

    id = Column(Integer, primary_key=True)
    task = Column(String)
    done = Column(Boolean, default=False)

    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    owner = relationship("User", back_populates="todos")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    due_date = Column(DateTime, nullable=True)
    priority = Column(Integer, default=1)

class UserCreate(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str

class TodoCreate(BaseModel):
    task: str
    due_date: datetime | None = None
    priority: int  = 1

class TodoResponse(BaseModel):
    id: int
    task: str
    done: bool
    created_at : datetime
    updated_at : datetime
    due_date: datetime | None
    priority: int

    class Config:
        orm_mode = True