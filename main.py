from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm 
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session, joinedload, validates
from typing import Annotated
from database import engine, SessionLocal
from passlib.hash import bcrypt
from passlib.context import CryptContext
from datetime import datetime,timedelta
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
import models
import re
import os

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")


app = FastAPI()
models.Base.metadata.create_all(bind=engine)

oauth2_scheme=OAuth2PasswordBearer(tokenUrl="token")

origins=[
    "http://localhost:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentails=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

def get_db():
    db = SessionLocal()
    try: 
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


## PYDANTIC BASES
class UserBase(BaseModel):
    name: str
    email: EmailStr
    password: str
    
class BooksBase(BaseModel):
    bookKey: str
    userId: int

## FUNCTIONS
# Password validation for regex
def validate_password(password:str):
    pattern = r"^(?=.*\d)(?=.*[a-z])(?=.*[A-Z]).{8,}$"
    match = re.match(pattern, password)
    if not match:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long, contain an uppercase letter, a lowercase letter, and a number."
        )

def get_user_by_email(db:Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db:Session, user:UserBase):
    hashed_password = pwd_context.hash(user.password)
    db_user = models.User(name=user.name, email=user.email, password=hashed_password)
    db.add(db_user)
    db.commit()
    return "complete"

def authenticate_user(name:str, email:str, password:str, db:Session):
    user = db.query(models.User).filter(models.User.email == user.email).first()
    if not user:
        return False
    if not pwd_context.verify(password, user.password):
        return False
    return user

def create_access_token(data:dict, expires_delta:timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(datetime.utc) + expires_delta
    else:
        expire=datetime.now(datetime.utc) + timedelta(minutes=15)
    to_encode.update({"exp":expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str=Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
        email: str=payload.get("sub")
        if email is None:
            raise HTTPException(status_code=403, detail="Token is invalid or expired")
        return payload
    except JWTError:
        raise HTTPException(status_code=403,
        detail="Token is invalid or expired" )


# Create user
@app.post("/singup/", status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: db_dependency):
    db_user = get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User with this email already exists.")
    return create_user(db=db, user=user)

@app.post("/token")
def login_for_access_token(*, form_data:OAuth2PasswordRequestForm = Depends(), db:db_dependency):
    user = authenticate_user(form_data.email, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate":"Bearer"}
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub":user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/verify-token/{oken}")
async def verify_token(token:str):
    verify_token(token=token)
    return {"message":"Token is valid"}
# Login

# Verify 


# Read user
@app.get("/users/{user_id}", status_code=status.HTTP_200_OK)
async def read_user(user_id: int, db:db_dependency):
    user = db.query(models.User).options(
        joinedload(models.User.books_to_read),
        joinedload(models.User.books_read)
        ).filter(models.User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.delete("/users/{user_id}", status_code=status.HTTP_200_OK)
async def delete_post(user_id:int, db:db_dependency):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(db_user)
    db.commit()


@app.post('/books-to-read/', status_code=status.HTTP_201_CREATED)
async def add_book_to_read(post: BooksBase, db: db_dependency):
    db_post = models.BooksToRead(**post.model_dump())
    db.add(db_post)
    db.commit()

@app.delete('/books-to-read/{book_id}', status_code=status.HTTP_200_OK)
async def delete_book_to_read(book_id:int, db:db_dependency):
    db_book = db.query(models.BooksToRead).filter(models.BooksToRead.id == book_id).first()
    if db_book is None:
        raise HTTPException(status_code=404, detail="Books not found")
    db.delete(db_book)
    db.commit()

@app.post('/books-read/', status_code=status.HTTP_201_CREATED)
async def add_book_read(post: BooksBase, db: db_dependency):
    db_post = models.BooksRead(**post.model_dump())
    db.add(db_post)
    db.commit()

@app.delete('/books-read/{book_id}', status_code=status.HTTP_200_OK)
async def delete_book_read(book_id:int, db:db_dependency):
    db_book = db.query(models.BooksRead).filter(models.BooksRead.id == book_id).first()
    if db_book is None:
        raise HTTPException(status_code=404, detail="Books not found")
    db.delete(db_book)
    db.commit()
