from sqlalchemy import Column, BigInteger, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)


class Tag(Base):
    __tablename__ = "tags"

    id = Column(BigInteger, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)

    entries = relationship("Entry", back_populates="tag_rel")


class Entry(Base):
    __tablename__ = "entries"

    id = Column(BigInteger, primary_key=True, index=True)
    name = Column(String)
    description = Column(Text)
    link = Column(String, unique=True)
    tag = Column(BigInteger, ForeignKey("tags.id"))
    author = Column(String)

    tag_rel = relationship("Tag", back_populates="entries")
