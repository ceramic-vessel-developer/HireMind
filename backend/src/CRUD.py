from sqlalchemy.orm import Session
import models
import schemas
from sqlalchemy.exc import IntegrityError


# User CRUD operations
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


def delete_user(db: Session, user_id: int):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user:
        db.delete(db_user)
        db.commit()
    return db_user


# CV CRUD operations
def create_cv(db: Session, cv: schemas.CVCreate):
    db_cv = models.CV(**cv.dict())
    db.add(db_cv)
    db.commit()
    db.refresh(db_cv)
    return db_cv


def get_cv_by_id(db: Session, cv_id: int):
    return db.query(models.CV).filter(models.CV.id == cv_id).first()


def get_cvs_by_user(db: Session, user_id: int):
    return db.query(models.CV).filter(models.CV.user_id == user_id).all()


def delete_cv(db: Session, cv_id: int):
    db_cv = db.query(models.CV).filter(models.CV.id == cv_id).first()
    if db_cv:
        db.delete(db_cv)
        db.commit()
    return db_cv


# Result CRUD operations
def create_result(db: Session, result: schemas.ResultCreate):
    db_result = models.Result(**result.dict())
    db.add(db_result)
    db.commit()
    db.refresh(db_result)
    return db_result


def get_result_by_id(db: Session, result_id: int):
    return db.query(models.Result).filter(models.Result.id == result_id).first()


def get_results_by_user(db: Session, user_id: int):
    return db.query(models.Result).filter(models.Result.user_id == user_id).all()


def get_results_by_cv(db: Session, cv_id: int):
    return db.query(models.Result).filter(models.Result.cv_id == cv_id).all()


def delete_result(db: Session, result_id: int):
    db_result = db.query(models.Result).filter(models.Result.id == result_id).first()
    if db_result:
        db.delete(db_result)
        db.commit()
    return db_result

