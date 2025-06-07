from sqlalchemy import Column, Integer, ForeignKey, String
from sqlalchemy.orm import relationship
from app.models.utilisateur import Utilisateur

class Admin(Utilisateur):
    __tablename__ = 'admin'
    
    id = Column(Integer, ForeignKey('utilisateur.id'), primary_key=True)
    niveau_acces = Column(String, default="super_admin")  # super_admin, admin
    
    __mapper_args__ = {
        'polymorphic_identity': 'admin',
    }