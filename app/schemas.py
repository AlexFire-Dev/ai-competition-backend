from pydantic import BaseModel


class UserBase(BaseModel):
    email: str
    username: str


class UserCreate(UserBase):
    password: str
    theme: str = "light"
    avatar: str = None


class User(UserBase):
    id: int
    theme: str
    avatar: str

    class Config:
        from_attributes = True
