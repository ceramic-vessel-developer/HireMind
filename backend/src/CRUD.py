from sqlalchemy.orm import Session
import models
import schemas
from sqlalchemy.exc import IntegrityError


def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(email=user.email, password=user.password)
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except IntegrityError:
        db.rollback()
        raise ValueError("Email already exists")


def get_user_by_id(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def create_entry(db: Session, entry: schemas.EntryCreate):
    db_entry = models.Entry(**entry.dict())
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    return db_entry


def create_tag(db: Session, tag: schemas.TagCreate):
    db_tag = models.Tag(**tag.dict())
    db.add(db_tag)
    db.commit()
    db.refresh(db_tag)
    return db_tag


def get_entries(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.Entry).offset(skip).limit(limit).all()


def get_entries_by_tag(db: Session, tag_id: int, skip: int = 0, limit: int = 10):
    return db.query(models.Entry).filter(models.Entry.tag == tag_id).offset(skip).limit(limit).all()


def get_entry_by_id(db: Session, entry_id: int):
    return db.query(models.Entry).filter(models.Entry.id == entry_id).first()


def get_all_tags(db: Session):
    return db.query(models.Tag).all()

