from pydantic import BaseModel, EmailStr, constr


class UserBaseScheme(BaseModel):
    email: EmailStr


class UserCreationScheme(UserBaseScheme):
    password: constr(min_length=8)
    password_confirm: str


class UserResponseScheme(UserBaseScheme):
    pass
