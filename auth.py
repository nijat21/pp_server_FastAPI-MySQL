from datetime import timedelta, datetime, timezone
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
from dotenv import load_dotenv
import os
import re

load_dotenv()
 
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")


router = APIRouter(
    prefix='/auth',
    tags=['auth']
)


bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme=OAuth2PasswordBearer(tokenUrl="auth/login")


## PYDANTIC BASES
class UserBase(BaseModel):
    name: str
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token:str
    token_type: str

# Model for delete user request
class DeleteUserRequest(BaseModel):
    password: str

class UpdateEmailRequest(BaseModel):
    new_email: EmailStr
    password: str

# Database dependency
def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]


@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def create_user(db:db_dependency, create_user_request: UserBase):
    try:
        db_user = db.query(User).filter(User.email == create_user_request.email).first()
        if db_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User with this email already exists.")
        
        validated_password = validate_password(create_user_request.password)

        create_user_model = User(
            name = create_user_request.name,
            email = create_user_request.email,
            password = bcrypt_context.hash(validated_password)
        )

        db.add(create_user_model)
        db.commit()
        
        # Create access token if user is authenticated
        # Authenticate the user
        user = authenticate_user(create_user_request.email, create_user_request.password, db)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed after user creation."
            )
        # Generate access token
        access_token_expires = timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES))
        access_token = create_access_token(
            data={"email": user.email, "id": user.id, "name": user.name}, 
            expires_delta=access_token_expires
        )
        
        return {"access_token": access_token, "token_type": "bearer"}
    except:
        HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred while creating the user.")

# Password validation for regex
def validate_password(password:str):
    pattern = r"^(?=.*\d)(?=.*[a-z])(?=.*[A-Z]).{8,}$"
    match = re.match(pattern, password)
    if not match:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long, contain an uppercase letter, a lowercase letter, and a number."
        )
    return password


@router.post("/login", response_model=Token)
def login_for_access_token(form_data:Annotated[OAuth2PasswordRequestForm, Depends()], db:db_dependency ):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    # Create access token if user is authenticated
    access_token_expires = timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES))
    access_token = create_access_token(
        data={"email":user.email, "id": user.id, "name": user.name}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# Checks for user and password
def authenticate_user(email:str, password:str, db):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return False
    if not bcrypt_context.verify(password, user.password):
        return False
    return user

# Creates access token with JWT, sets expiration time 

def create_access_token(data:dict, expires_delta:timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(tz=timezone.utc) + expires_delta
    else:
        expire=datetime.now(tz=timezone.utc) + timedelta(minutes=20)
    to_encode.update({"exp":expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Validate token and return user information
async def get_current_user(token:Annotated[str, Depends(oauth2_scheme)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email:str = payload.get("email")
        id:int = payload.get("id")
        name:str = payload.get("name")
        if email is None or id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is invalid or expired")
        return payload
    except JWTError:
        raise HTTPException(status_code=403,
        detail="Token is invalid or expired" )

user_dependency = Annotated[dict, Depends(get_current_user)]

# Returns user if active JWT
@router.get("/verify", status_code=status.HTTP_200_OK)
async def user(user:user_dependency, db:db_dependency):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed")
    return {"User": user}


@router.delete("/deleteUser/{user_id}", status_code=status.HTTP_200_OK)
async def delete_post(user_id:int, request:DeleteUserRequest, db:db_dependency, user:user_dependency):
    try:
        db_user = db.query(User).filter(User.id == user_id).first()
        if db_user is None:
            raise HTTPException(status_code=404, detail="User not found")
        if not authenticate_user(db_user.email, request.password, db):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The password included is not correct")
        
        db.delete(db_user)
        db.commit()
        return {"detail": "Account deleted successfully"}
    except:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error occurred deleting the account")

@router.put("/updateEmail/{user_id}", status_code=status.HTTP_200_OK)
async def update_email(user_id: int, request:UpdateEmailRequest, db: db_dependency, user:user_dependency):
    try:
        db_user = db.query(User).filter(User.id == user_id).first()
        if db_user is None:
            raise HTTPException(status_code=404, detail="User not found")
        if not authenticate_user(db_user.email, request.password, db):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The password included is not correct")
        # Update the email
        db_user.email = request.new_email
        db.commit()
        return {"detail": "Email updated successfully"}
    except:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error occurred updating the email")

# # Read user
# @app.get("/users/{user_id}", status_code=status.HTTP_200_OK)
# async def read_user(user_id: int, db:db_dependency):
#     user = db.query(models.User).options(
#         joinedload(models.User.books_to_read),
#         joinedload(models.User.books_read)
#         ).filter(models.User.id == user_id).first()
#     if user is None:
#         raise HTTPException(status_code=404, detail="User not found")
#     return user
