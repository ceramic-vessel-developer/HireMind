from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import Depends, FastAPI, HTTPException, status, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, SecurityScopes
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import ValidationError
from sqlalchemy.orm import Session

import CRUD
import models
import schemas
from config import ALGORITHM, SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES, ORIGINS
from database import SessionLocal
import hashlib

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login", scopes={"user": "Zwykly user"})

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_password_hash(password: str) -> str:
    password_bytes = password.encode("utf-8")
    digest = hashlib.sha256(password_bytes).digest()
    return pwd_context.hash(digest)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    digest = hashlib.sha256(plain_password.encode("utf-8")).digest()
    return pwd_context.verify(digest, hashed_password)

def get_user(db: Session, username: str):
    user = CRUD.get_user_by_email(db, username)
    return user


# funkcja odpowiadajaca za tworzenie tokenow JWT
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# funkcja odpowiadajaca za logowanie uzytkownika
def authenticate_user(db: Session, username: str, password: str):
    user = CRUD.get_user_by_email(db, username)
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user


# funkcja odpowiadajaca za autoryzacje
def get_current_user(security_scopes: SecurityScopes, token: str = Depends(oauth2_scheme),
                     db: Session = Depends(get_db)):
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_scopes = payload.get("scopes", [])
        token_data = schemas.TokenData(scopes=token_scopes, username=username)
    except (JWTError, ValidationError):
        raise credentials_exception
    user = get_user(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    for scope in security_scopes.scopes:
        if scope not in token_data.scopes:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not enough permissions",
                headers={"WWW-Authenticate": authenticate_value},
            )
    return user


# Endpoint rejestrujacy nowych uzytkownikow
@app.post("/register", status_code=201)
def register(user: schemas.UserCreate, session: Session = Depends(get_db)):
    existing_user = session.query(models.User).filter_by(email=user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    user.password = get_password_hash(user.password)

    CRUD.create_user(session, user)

    return {"message": "user created successfully"}


"""
    Endpoint sluzacy do logowania. Zwraca token JWT.
    Aby uzytkownik otrzymal stopien uprawnien "user", w bazie danych musi mu byc przypisana rola o nazwie "user".
"""


@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    scopes = ["user"]
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "scopes": scopes}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me", response_model=schemas.UserReturn)
async def read_users_me(current_user: schemas.UserReturn = Depends(get_current_user)):
    return current_user


@app.get("/users/{id}", response_model=schemas.UserReturn)
async def read_user(id: int, db: Session = Depends(get_db)):
    db_user = CRUD.get_user_by_id(db, id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.delete("/users/{id}", status_code=200)
async def delete_user(id: int, db: Session = Depends(get_db),
                      current_user: schemas.UserReturn = Security(get_current_user, scopes=["user"])):
    db_user = CRUD.get_user_by_id(db, id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(db_user)
    try:
        db.commit()
    except:
        db.rollback()
        raise HTTPException(status_code=400, detail="Could not delete user")
    return {"message": "user deleted successfully"}

#TODO upload cv
@app.post("/users/{id}", status_code=200)
async def delete_user(id: int, db: Session = Depends(get_db),
                      current_user: schemas.UserReturn = Security(get_current_user, scopes=["user"])):
    pass


# TODO zbadaj cv
# TODO get results
# TODO get cv results

