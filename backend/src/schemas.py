from pydantic import BaseModel
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


class EntryCreate(BaseModel):
    name: Optional[str]
    description: Optional[str]
    link: str
    tag: int
    author: Optional[str]


class EntryReturn(EntryCreate):
    id: int

    class Config:
        orm_mode = True


class TagCreate(BaseModel):
    name: str


class TagReturn(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True
