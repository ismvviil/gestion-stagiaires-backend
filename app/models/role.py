from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
from app.models.utilisateur import utilisateur_role

class Role(BaseModel):
    nom = Column(String, unique=True, nullable=False)
    permissions = Column(String)  # Stockées en format JSON ou sous forme de chaîne
    
    # Relation avec les utilisateurs
    utilisateurs = relationship("Utilisateur", secondary=utilisateur_role, back_populates="roles")
    
    def verifier_permission(self, action):
        """Vérifie si le rôle a une permission spécifique"""
        # À implémenter selon votre logique de permissions
        return action in self.permissions if self.permissions else False