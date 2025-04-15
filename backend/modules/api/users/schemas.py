from pydantic import BaseModel, EmailStr, constr


# Modèle Pydantic pour validation
class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str


# Modèle de réponse avec un email anonymisé, en utilisant constr(min_length=1)
class UserResponse(BaseModel):
    id: int
    email: constr(min_length=1)  # type: ignore
    name: str
    is_active: bool
    role: str

    class Config:
        from_attributes = True


# Modèle pour mettre à jour un rôle
class RoleUpdate(BaseModel):
    role_id: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: str | None = None
