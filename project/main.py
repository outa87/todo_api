from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional
from .auth import create_access_token, verify_token
from .database import init_db, get_db
from .models import TodoCreate, TodoResponse, UserCreate, UserResponse
from .crud import (add_todo, get_user_todos, update_todo, delete_todo, 
create_user, get_user_by_username, verify_password)
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s", 
                    datefmt="%Y-%m-%d %H:%M:%S")

security = HTTPBearer()
app = FastAPI()
init_db()
logger = logging.getLogger(__name__)


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload

@app.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, db: Session = Depends(get_db)):
    logger.info(f"[register] attempt username={user.username}")
    existing = get_user_by_username(db, user.username)
    if existing:
        logger.warning(f"[register] already exists username={user.username}")
        raise HTTPException(status_code=400, detail="Username already exists")
    new_user = create_user(db, user.username, user.password)
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

@app.post("/todos", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
def create_todo(todo: TodoCreate, user=Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = user["user_id"]
    logger.info(f"[create_todo] user_id={user_id}, task='{todo.task}'")
    return add_todo(db, todo.task, user_id, todo.due_date, todo.priority)
    
@app.get("/todos", response_model=List[TodoResponse])
def get_todos(done: Optional[bool] = None, priority: Optional[int] = None, sort_by: Optional[str] = None, 
              skip: int = 0, limit: int = 10, user=Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = user["user_id"]
    logger.info(f"[get_todos] user_id={user_id}, skip={skip}, limit={limit}")
    return get_user_todos(db, user_id, done, priority, sort_by, skip, limit)
    
@app.patch("/todos/{todo_id}", response_model=TodoResponse)
def update(todo_id: int, done: bool, user=Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = user["user_id"]
    todo = update_todo(db, todo_id, user_id, done)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo

@app.delete("/todos/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(todo_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = user["user_id"]
    todo = delete_todo(db, todo_id, user_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return 