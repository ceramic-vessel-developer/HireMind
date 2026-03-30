from sqlalchemy import Column, BigInteger, Integer, String, Text, ForeignKey, Float
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)

    cvs = relationship("CV", back_populates="user", cascade="all, delete")
    results = relationship("Result", back_populates="user", cascade="all, delete")


class CV(Base):
    __tablename__ = "cvs"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    file_format = Column(String, nullable=False)
    file_key = Column(String, unique=True, nullable=False)

    user = relationship("User", back_populates="cvs")
    results = relationship("Result", back_populates="cv", cascade="all, delete")


class Result(Base):
    __tablename__ = "results"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    cv_id = Column(Integer, ForeignKey("cvs.id", ondelete="CASCADE"), nullable=False)
    joint_score = Column(Float, nullable=False)
    advice = Column(Text, nullable=False)

    user = relationship("User", back_populates="results")
    cv = relationship("CV", back_populates="results")