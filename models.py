from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, DateTime,func
from sqlalchemy.orm import relationship, validates
from database import Base


class Timestamp:
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

class User(Base, Timestamp):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(125), nullable=False)
    # Creates relationships with BooksToRead and BooksRead
    books_to_read = relationship("BooksToRead", back_populates="user")
    books_read = relationship("BooksRead", back_populates="user")

class BooksToRead(Base, Timestamp):
    __tablename__ = "books_to_read"

    id = Column(Integer, primary_key=True, index=True)
    bookKey = Column(String(100), nullable=False)
    userId = Column(Integer, ForeignKey('users.id'), nullable=False)
    # Creates relationship with users
    user = relationship("User", back_populates="books_to_read")

class BooksRead(Base, Timestamp):
    __tablename__ = "books_read"

    id = Column(Integer, primary_key=True, index=True)
    bookKey = Column(String(100), nullable=False)
    userId = Column(Integer, ForeignKey('users.id'), nullable=False)
    # Creates relationship with users
    user = relationship("User", back_populates="books_read")