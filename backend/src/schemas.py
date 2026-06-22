import json

from pydantic import BaseModel, field_validator
from typing import Optional


# Pydantic schema for User
class UserBase(BaseModel):
    email: str


class UserCreate(UserBase):
    password: str


class UserReturn(UserBase):
    id: int

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None
    scopes: list[str] = []


# Pydantic schema for CV
class CVBase(BaseModel):
    user_id: int
    file_format: str
    file_key: str


class CVCreate(BaseModel):
    file_format: str

    class Config:
        extra = "forbid"


class CVReturn(CVBase):
    id: int

    class Config:
        orm_mode = True


# Pydantic schema for Result
class ResultBase(BaseModel):
    user_id: int
    cv_id: int
    joint_score: float
    advice: str


class ResultCreate(ResultBase):
    pass


class ResultReturn(ResultBase):
    id: int

    class Config:
        orm_mode = True


class MatchResult(BaseModel):
    job_keywords: list[str]
    resume_keywords: list[str]
    matched_keywords: list[str]
    missing_keywords: list[str]
    coverage_score: float
    weighted_score: float


class MatchAnalysisTextInput(BaseModel):
    job_offer_text: str


class MatchAnalysisURLInput(BaseModel):
    job_offer_url: str