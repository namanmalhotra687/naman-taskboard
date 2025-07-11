from pydantic import BaseModel
from typing import Optional

class ItemBase(BaseModel):
    title: str
    description: str
    status: str
    deadline: str

class ItemUpdate(BaseModel):
    title: Optional[str]
    description: Optional[str]
    status: Optional[str]
    deadline: Optional[str]

class UserLogin(BaseModel):
    username: str
    password: str

class ItemBase(BaseModel):
    title: str
    description: str
    status: str
    deadline: str

class ItemUpdate(BaseModel):
    title: Optional[str]
    description: Optional[str]
    status: Optional[str]
    deadline: Optional[str]

class UserLogin(BaseModel):
    username: str
    password: str

