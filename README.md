# PhoenixPagesApp - FastAPI Backend

![Books image](https://collegeinfogeek.com/wp-content/uploads/2018/11/Essential-Books.jpg)

PhoenixPagesApp is a FastAPI-based backend that allows users to manage their reading lists. Users can create accounts, log in, and manage books they wish to read as well as books they have already read.

This backend uses authentication with JWT tokens for secure access to user accounts and data. The project integrates SQLAlchemy for database interactions and provides RESTful endpoints for managing users and books.

## Features

- **User Registration and Authentication**:
  - Register new users.
  - Secure login with JWT-based access tokens.
  - Password validation ensuring strong security.
- **Manage Books**:
  - Add books to the "To Read" list.
  - Add books to the "Read" list.
  - Retrieve and delete books from both lists.
- **CORS Support**:
  - Configured for cross-origin resource sharing with allowed origins.

## Requirements

- Python 3.10+
- FastAPI 0.112.0+
- SQLAlchemy 2.0.31+
- bcrypt 4.2.0+
- Python-Jose 3.3.0+
- PyMySQL 1.1.1
- Uvicorn 0.30.5+

## Installation

1.  Clone the repository:

        bash

        Copy code

        `git clone https://github.com/yourusername/PhoenixPagesApp.git

    cd PhoenixPagesApp`

2.  Install dependencies:

    bash

    Copy code

    `pip install -r requirements.txt`

3.  Set up environment variables: Create a `.env` file in the project root and define the following variables:

        env

        Copy code

        `URL_DATABASE=mysql+pymysql://username:password@localhost/dbname

    SECRET_KEY=your_secret_key
    ALGORITHM=HS256
    ACCESS_TOKEN_EXPIRE_MINUTES=30
    ORIGIN=https://yourfrontend.com`

4.  Initialize the database:

    bash

    Copy code

    `python -m sqlalchemy <script_to_initialize_db>.py`

## Running the Application

To start the FastAPI server with Uvicorn, run:

bash

Copy code

`uvicorn main:app --reload`

The application will be available at `http://127.0.0.1:8000`.

## API Endpoints

### Authentication

- **Sign Up**:

  - Endpoint: `/auth/signup`
  - Method: `POST`
  - Payload:

        json

        Copy code

        `{

    "name": "John Doe",
    "email": "johndoe@example.com",
    "password": "YourPassword123!"
    }`

- **Login**:

  - Endpoint: `/auth/login`
  - Method: `POST`
  - Payload:

        json

        Copy code

        `{

    "username": "johndoe@example.com",
    "password": "YourPassword123!"
    }`

  - Response:

        json

        Copy code

        `{

    "access_token": "jwt_token_here",
    "token_type": "bearer"
    }`

- **Verify Token**:

  - Endpoint: `/auth/verify`
  - Method: `GET`

### Manage Books

- **Add a Book to "To Read" List**:

  - Endpoint: `/books-to-read`
  - Method: `POST`
  - Payload:

        json

        Copy code

        `{

    "book_key": "book_identifier",
    "user_id": 1
    }`

- **Retrieve Books "To Read"**:

  - Endpoint: `/books-to-read/{user_id}`
  - Method: `GET`

- **Delete a Book from "To Read" List**:

  - Endpoint: `/books-to-read`
  - Method: `DELETE`
  - Payload:

        json

        Copy code

        `{

    "book_key": "book_identifier",
    "user_id": 1
    }`

- **Add a Book to "Read" List**:

  - Endpoint: `/books-read`
  - Method: `POST`
  - Payload:

        json

        Copy code

        `{

    "book_key": "book_identifier",
    "user_id": 1
    }`

- **Retrieve "Read" Books**:

  - Endpoint: `/books-read/{user_id}`
  - Method: `GET`

- **Delete a Book from "Read" List**:

  - Endpoint: `/books-read`
  - Method: `DELETE`
  - Payload:

        json

        Copy code

        `{

    "book_key": "book_identifier",
    "user_id": 1
    }`

## Database Models

### User

python

Copy code

`class User(Base):
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(125), nullable=False)
    books_to_read = relationship("BooksToRead", back_populates="user")
    books_read = relationship("BooksRead", back_populates="user")`

### BooksToRead

python

Copy code

`class BooksToRead(Base):
    id = Column(Integer, primary_key=True, index=True)
    bookKey = Column(String(100), nullable=False)
    userId = Column(Integer, ForeignKey('users.id'), nullable=False)
    user = relationship("User", back_populates="books_to_read")`

### BooksRead

python

Copy code

`class BooksRead(Base):
    id = Column(Integer, primary_key=True, index=True)
    bookKey = Column(String(100), nullable=False)
    userId = Column(Integer, ForeignKey('users.id'), nullable=False)
    user = relationship("User", back_populates="books_read")`

## Security

- Passwords are hashed using bcrypt.
- JWT tokens are used for authentication and authorization.
- Environment variables store sensitive information like secret keys.
