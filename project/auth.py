from datetime import datetime, timedelta
from jose import jwt, JWTError
import os
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv(dotenv_path="project/.env")
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY is not set")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    logger.info(f"[create_access_token] token created for data={data}")
    return token

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        logger.info(f"[verify_token] token valid: payload={payload}")
        return payload
    except JWTError as e:
        logger.warning(f"[verify_token] invalid token: {token}, error={e}")
        return None