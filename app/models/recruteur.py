from sqlalchemy import Column, Integer, ForeignKey, String
from sqlalchemy.orm import relationship
from app.models.utilisateur import Utilisateur

class Recruteur(Utilisateur):
    __tablename__ = 'recruteur'
    
    id = Column(Integer, ForeignKey('utilisateur.id'), primary_key=True)
    poste = Column(String, nullable=False)
    entreprise_id = Column(Integer, ForeignKey('entreprise.id'))
    
    # Relation avec l'entreprise
    entreprise = relationship("Entreprise", back_populates="recruteurs")
    
    # Offres publiées
    offres = relationship("Offre", back_populates="recruteur")
    
    # Candidatures gérées
    candidatures = relationship("Candidature", back_populates="recruteur")
    

    # Ajouter ces relations
    stages_encadres = relationship("Stage", back_populates="recruteur")
    missions_assignees = relationship("Mission", back_populates="assigne_par")

    
    __mapper_args__ = {
        'polymorphic_identity': 'recruteur',
    }
