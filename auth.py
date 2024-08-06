from datetime import timedelta, datetime
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from starlette import status
from database import SessionLocal
from models import User
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
import os

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")

router = APIRouter(
    prefix='/auth',
    tags=['auth']
)


bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme=OAuth2PasswordBearer(tokenUrl="token")


## PYDANTIC BASES
class UserBase(BaseModel):
    name: str
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token:str
    token_type: str

def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def create_user(db:db_dependency, create_user_request: UserBase):
    create_user_model = User(
        name=create_user_request.name,
        email = create_user_request.email,
        password = bcrypt_context.hash(create_user_request.password)
    )

    db.add(create_user_model)
    db.commit()

@router.post("/token", response_model=Token)
def login_for_access_token(*, form_data:OAuth2PasswordRequestForm = Depends(), db:db_dependency):
    user = authenticate_user(form_data.email, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate":"Bearer"}
        )
    # Create access token if user is authenticated
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub":user.email, "id": user.id, "name": user.name}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# Checks for user and password
def authenticate_user(email:str, password:str, db:Session):
    user = db.query(User).filter(User.email == user.email).first()
    if not user:
        return False
    if not bcrypt_context.verify(password, user.password):
        return False
    return user

# Creates access token with JWT, sets expiration time 
def create_access_token(data:dict, expires_delta:timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(datetime.utc) + expires_delta
    else:
        expire=datetime.now(datetime.utc) + timedelta(minutes=20)
    to_encode.update({"exp":expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Validate token and return user information
async def validate_token(token:Annotated[str, Depends(oauth2_scheme)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithm=ALGORITHM)
        email:str = payload.get('sub')
        id:int = payload.get('id')
        name:str = payload.get('name')
        if email is None or id is None or name is None:
            raise HTTPException(status_code=403, detail="Token is invalid or expired")
        return payload
    except JWTError:
        raise HTTPException(status_code=403,
        detail="Token is invalid or expired" )