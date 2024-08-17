from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
import models
from database import engine, SessionLocal
from typing import Annotated
from sqlalchemy.orm import Session, joinedload, validates
from pydantic import BaseModel, EmailStr
import auth
from auth import get_current_user


app = FastAPI()
app.include_router(auth.router)
models.Base.metadata.create_all(bind=engine)

origins=[
    "http://localhost:5173",
    "https://phoenix-pages.netlify.app"
]

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

def get_db():
    db = SessionLocal()
    try: 
        yield db
    finally:
        db.close()

# Dependencies
db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

## PYDANTIC BASES
class BooksBase(BaseModel):
    book_key: str
    user_id: int

# BOOKS TO READ 
@app.post('/books-to-read', status_code=status.HTTP_201_CREATED)
async def add_book_to_read(post:BooksBase, db: db_dependency, user:user_dependency):
    try:
        db_book = db.query(models.BooksToRead).filter(
            models.BooksToRead.bookKey == post.book_key,
            models.BooksToRead.userId == post.user_id
            ).first()
        if db_book:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This book is already in the list")
        db_post = models.BooksToRead(bookKey=post.book_key, userId=post.user_id)
        db.add(db_post)
        db.commit()
        return {"detail":"Book added successfully"}
    except:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@app.get('/books-to-read/{user_id}', status_code=status.HTTP_200_OK)
async def retrieve_books_to_read(user_id:int, db:db_dependency, user:user_dependency):
    try:
        db_books = db.query(models.BooksToRead).filter(models.BooksToRead.userId == user_id).all()
        if db_books is None:
            raise HTTPException(status_code=404, detail="Books not found")
        return {"books_to_read": db_books}
    except:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@app.delete('/books-to-read', status_code=status.HTTP_200_OK)
async def delete_book_to_read(req:BooksBase, db:db_dependency, user:user_dependency):
    try:
        db_book = db.query(models.BooksToRead).filter(
            models.BooksToRead.bookKey == req.book_key,
            models.BooksToRead.userId == req.user_id
            ).first()
        if db_book is None:
            raise HTTPException(status_code=404, detail="Books not found")
        db.delete(db_book)
        db.commit()
        return {"detail":"Book deleted successfully"}
    except:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


# BOOKS READ
@app.post('/books-read', status_code=status.HTTP_201_CREATED)
async def add_book_read(post: BooksBase,db: db_dependency, user:user_dependency):
    try:
        db_book = db.query(models.BooksRead).filter(
            models.BooksRead.bookKey == post.book_key,
            models.BooksRead.userId == post.user_id
            ).first()
        if db_book:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This book is already in the list")
        db_post = models.BooksRead(bookKey=post.book_key, userId=post.user_id)
        db.add(db_post)
        db.commit()
        return {"detail":"Book added successfully"}
    except:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@app.get('/books-read/{user_id}', status_code=status.HTTP_200_OK)
async def retrieve_books_read(user_id:int, db:db_dependency, user:user_dependency):
    try:
        db_books = db.query(models.BooksRead).filter(models.BooksRead.userId == user_id).all()
        if db_books is None:
            raise HTTPException(status_code=404, detail="Books not found")
        return {"books_read": db_books}
    except:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@app.delete('/books-read', status_code=status.HTTP_200_OK)
async def delete_book_read(req:BooksBase, db:db_dependency, user:user_dependency):
    try:
        db_book = db.query(models.BooksRead).filter(
            models.BooksRead.bookKey == req.book_key,
            models.BooksToRead.userId == req.user_id
            ).first()
        if db_book is None:
            raise HTTPException(status_code=404, detail="Books not found")
        db.delete(db_book)
        db.commit()
        return {"detail":"Book deleted successfully"}
    except:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
