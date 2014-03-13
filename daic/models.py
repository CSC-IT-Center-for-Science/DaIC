from sqlalchemy import (Column, Integer, String)
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Client(Base):
    __tablename__ = 'client'

    id = Column(Integer, primary_key=True)
    instance_id = Column(String(255))


class Resource(Base):
    __tablename__ = 'resource'

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    uuid = Column(String(32))


class UploadToken(Base):
    __tablename__ = 'uploadtoken'

    id = Column(Integer, primary_key=True)
    uuid = Column(String(32))
