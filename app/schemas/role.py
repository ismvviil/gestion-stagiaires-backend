from pydantic import BaseModel
from typing import Optional, List
from app.schemas.base import BaseSchema

class RoleBase(BaseModel):
    nom: str
    permissions: Optional[str] = None

class RoleCreate(RoleBase):
    pass

class RoleUpdate(BaseModel):
    nom: Optional[str] = None
    permissions: Optional[str] = None

class Role(RoleBase, BaseSchema):
    class Config:
        from_attributes = True