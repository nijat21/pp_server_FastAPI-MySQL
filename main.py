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
    bookKey: str
    userId: int

@app.post('/books-to-read/', status_code=status.HTTP_201_CREATED)
async def add_book_to_read(post: BooksBase, db: db_dependency, user:user_dependency):
    db_post = models.BooksToRead(**post.model_dump())
    db.add(db_post)
    db.commit()

@app.delete('/books-to-read/{book_id}', status_code=status.HTTP_200_OK)
async def delete_book_to_read(book_id:int, db:db_dependency, user:user_dependency):
    db_book = db.query(models.BooksToRead).filter(models.BooksToRead.id == book_id).first()
    if db_book is None:
        raise HTTPException(status_code=404, detail="Books not found")
    db.delete(db_book)
    db.commit()

@app.post('/books-read/', status_code=status.HTTP_201_CREATED)
async def add_book_read(post: BooksBase, db: db_dependency, user:user_dependency):
    db_post = models.BooksRead(**post.model_dump())
    db.add(db_post)
    db.commit()

@app.delete('/books-read/{book_id}', status_code=status.HTTP_200_OK)
async def delete_book_read(book_id:int, db:db_dependency, user:user_dependency):
    db_book = db.query(models.BooksRead).filter(models.BooksRead.id == book_id).first()
    if db_book is None:
        raise HTTPException(status_code=404, detail="Books not found")
    db.delete(db_book)
    db.commit()
