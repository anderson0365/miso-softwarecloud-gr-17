from sqlalchemy import Column, Integer, String, ForeignKey
from .database import Base
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__="user"
    id = Column(Integer, primary_key = True)
    username = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    tasks = relationship('Task', cascade='all, delete, delete-orphan')

    def simplified(self):
        return { 'id': self.id, 'username': self.username, 'password': self.password }

class Task(Base):
    __tablename__ ="task"
    id = Column(Integer, primary_key = True)
    fileName = Column(String(128), nullable=False)
    newFormat = Column(String(20), nullable=False)
    timeStamp = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False)
    user = Column(Integer, ForeignKey("user.id"))

class UserSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = User
        include_relationships = True
        load_instance = True

class TaskSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Task
        include_relationships = True
        load_instance = True