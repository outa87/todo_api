import logging
from models import Todo, User
from passlib.context import CryptContext

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)

def create_user(db, username: str, password: str):
    hashed_pw = hash_password(password)
    user = User(username=username, hashed_password=hashed_pw)
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info(f"[create_user] Created user id={user.id}, username='{user.username}'")
    return user

def get_user_by_username(db, username: str):
    return db.query(User).filter(User.username == username).first()

def add_todo(db, task: str, user_id: int, due_date=None, priority=1):
    logger.info(f"[add_todo] start task='{task}', user_id={user_id}")

    new_todo = Todo(task=task, done=False, user_id=user_id, due_date=due_date,priority=priority)
    db.add(new_todo)
    db.commit()
    db.refresh(new_todo)  
    logger.info(f"[add_todo] success id={new_todo.id}")     
    return new_todo

def get_user_todos(db, user_id: int, done: bool = None, priority: int = None, sort_by: str = None, 
                   skip: int = 0, limit: int = 10):
    logger.info(f"[get_user_todos] start user_id={user_id}")

    query = db.query(Todo).filter(Todo.user_id == user_id)
    if done is not None:
        query = query.filter(Todo.done == done)
    if priority is not None:
        query = query.filter(Todo.priority == priority)
    if sort_by == "created":
        query = query.order_by(Todo.created_at)
    elif sort_by == "due":
        query = query.order_by(Todo.due_date)

    todos = query.offset(skip).limit(limit).all()
    
    logger.info(f"[get_user_todos] Fetched {len(todos)} todos")
    return todos

def update_todo(db, todo_id: int, user_id: int, done: bool):
    logger.info(f"[update_todo] start id={todo_id}, user_id={user_id}, done={done}")
    todo = db.query(Todo).filter(Todo.id == todo_id, Todo.user_id == user_id).first()

    if not todo:
        logger.warning(f"[update_todo] not found or unauthorized id={todo_id}")
        return None
    old_done = todo.done
    todo.done = done
    db.commit() 
    logger.info(f"[update_todo] success id={todo_id}, {old_done} -> {done}")       
    return todo
            
def delete_todo(db, todo_id: int, user_id: int):
    logger.info(f"[delete_todo] start id={todo_id}, user_id={user_id}")

    todo = db.query(Todo).filter(Todo.id == todo_id, Todo.user_id == user_id).first()
    if not todo:     
        logger.warning(f"[delete_todo] not found or unauthorized id={todo_id}")       
        return None
    db.delete(todo)
    db.commit()
    logger.info(f"[delete_todo] success id={todo_id}")
    return todo
