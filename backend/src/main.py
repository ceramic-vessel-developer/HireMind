from __future__ import annotations

from datetime import datetime, timedelta
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status, Security, UploadFile, File, Form, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, SecurityScopes
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import ValidationError
from sqlalchemy.orm import Session
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import uuid
import os
import json
import tempfile
import pickle

import CRUD
import models
import schemas
from config import ALGORITHM, SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES, ORIGINS
from database import SessionLocal
import hashlib

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login", scopes={"user": "Zwykly user"})

# Google Drive API setup
SCOPES = ['https://www.googleapis.com/auth/drive.file']
CREDENTIALS_FILE = 'credentials.json'  # OAuth2 credentials from Google Cloud
TOKEN_FILE = 'token.pickle'  # Cached token
GOOGLE_DRIVE_FOLDER_ID = os.getenv('GOOGLE_DRIVE_FOLDER_ID', '')  # Optional folder ID


def get_drive_service():
    """Get authenticated Google Drive service."""
    creds = None
    
    # Load saved token if it exists
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)
    
    # If no valid credentials, perform OAuth2 flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the token for next time
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)
    
    return build('drive', 'v3', credentials=creds)

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


@app.get("/cvs/user/{user_id}", response_model=list[schemas.CVReturn])
async def get_user_cvs(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.UserReturn = Security(get_current_user, scopes=["user"])
):
    if user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Can't retrieve cvs for that user")
    
    cvs = CRUD.get_cvs_by_user(db, user_id)
    if not cvs:
        raise HTTPException(status_code=404, detail="No CVs found for this user")
    
    return cvs


@app.post("/cvs/user/{user_id}", status_code=201)
async def create_user_cv(
    user_id: int,
    cv: Annotated[str, Form()],
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: schemas.UserReturn = Security(get_current_user, scopes=["user"])
):
    if user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Can't upload cv for that user")

    
    # Generate UUID for filename
    file_uuid = str(uuid.uuid4())
    file_ext = os.path.splitext(file.filename)[1]  # Get file extension
    filename = f"{file_uuid}{file_ext}"
    
    # Save file temporarily to system temp directory
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, filename)
    
    with open(temp_path, "wb") as buffer:
        buffer.write(await file.read())
    
    try:
        # Upload to Google Drive
        drive_service = get_drive_service()
    
        file_metadata = {'name': filename}
        if GOOGLE_DRIVE_FOLDER_ID:
            file_metadata['parents'] = [GOOGLE_DRIVE_FOLDER_ID]
        
        media = MediaFileUpload(temp_path, mimetype=file.content_type)
        
        drive_file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        
        file_key = drive_file.get('id')
        
        # Create CV record in database
        cv_db = models.CV(
            user_id=user_id,
            file_format=cv,
            file_key=file_key
        )
        db.add(cv_db)
        db.commit()
        db.refresh(cv_db)
        
        return cv_db
        
    finally:
        # Clean up temp file
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except Exception as e:
            # Log the error but don't fail the request
            print(f"Warning: Could not delete temp file {temp_path}: {e}")



@app.post("/cvs/{cv_id}/analyze", status_code=200)
async def analyze_cv(
    cv_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.UserReturn = Security(get_current_user, scopes=["user"])
):
    """Download CV from Google Drive and analyze it."""
    cv = CRUD.get_cv_by_id(db, cv_id)
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")
    
    if cv.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Can't analyze CV for that user")
    
    try:
        # Download CV from Google Drive
        drive_service = get_drive_service()
        file_content = drive_service.files().get_media(
            fileId=cv.file_key
        ).execute()
        
        # TODO: Implement actual CV analysis here
        # For now, return placeholder response
        return {
            "cv_id": cv_id,
            "analysis": "Placeholder analysis - CV downloaded successfully",
            "file_size": len(file_content) if file_content else 0
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not download CV: {str(e)}")


@app.get("/results/user/{user_id}", response_model=list[schemas.ResultReturn])
async def get_user_results(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.UserReturn = Security(get_current_user, scopes=["user"])
):
    """Get all results for a user."""
    if user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Can't retrieve results for that user")
    
    results = CRUD.get_results_by_user(db, user_id)
    if not results:
        raise HTTPException(status_code=404, detail="No results found for this user")
    
    return results


@app.get("/results/cv/{cv_id}", response_model=list[schemas.ResultReturn])
async def get_cv_results(
    cv_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.UserReturn = Security(get_current_user, scopes=["user"])
):
    """Get all results for a specific CV."""
    cv = CRUD.get_cv_by_id(db, cv_id)
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")
    
    if cv.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Can't retrieve results for that CV")
    
    results = CRUD.get_results_by_cv(db, cv_id)
    if not results:
        raise HTTPException(status_code=404, detail="No results found for this CV")
    
    return results

