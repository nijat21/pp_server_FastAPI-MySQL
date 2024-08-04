from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr
from typing import Annotated
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session, joinedload

app = FastAPI()
models.Base.metadata.create_all(bind=engine)

class UserBase(BaseModel):
    name: str
    email: EmailStr

class BooksBase(BaseModel):
    bookKey: str
    userId: int

def get_db():
    db = SessionLocal()
    try: 
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


@app.post("/users/", status_code=status.HTTP_201_CREATED)
async def create_user(user: UserBase, db: db_dependency):
    db_user = models.User(**user.model_dump())
    db.add(db_user)
    db.commit()

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
