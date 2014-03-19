from sqlalchemy import (Column, BigInteger, Integer, String, Text,
                        DateTime, ForeignKey)
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Serializable(object):
    __public__ = []

    def to_dict(self):
        d = {}
        for field in self.__public__:
            value = getattr(self, field)
            if value:
                d[field] = value
        return d


class Client(Base):
    __tablename__ = 'client'

    id = Column(Integer, primary_key=True)
    instance_id = Column(String(255))


class Container(Base, Serializable):
    __tablename__ = 'container'
    __public__ = ['name', 'uuid', 'create_ts', 'access_ts']

    id = Column(Integer, primary_key=True)
    name = Column(String)
    uuid = Column(String(255))
    create_ts = Column(DateTime)
    access_ts = Column(DateTime)


class File(Base, Serializable):
    __tablename__ = 'resource'
    __public__ = ['name', 'uuid', 'meta']

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    uuid = Column(String(32))
    container = Column(Integer, ForeignKey('container.id'))
    meta = Column(Text)


class Content(Base, Serializable):
    __tablename__ = 'base'
    __public__ = ['name', 'uri', 'uuid', 'size', 'checksum']

    id = Column(Integer, primary_key=True)
    uri = Column(String(255))
    uuid = Column(String(255))
    size = Column(BigInteger)
    checksum = Column(String(64))


class UploadToken(Base):
    __tablename__ = 'uploadtoken'

    id = Column(Integer, primary_key=True)
    uuid = Column(String(32))
