from sqlalchemy import Column, String, ForeignKey, Integer
from sqlalchemy.orm import relationship
from app.models.utilisateur import Utilisateur

class ResponsableRH(Utilisateur):
    __tablename__ = 'responsable_rh'
    
    id = Column(Integer, ForeignKey('utilisateur.id'), primary_key=True)
    poste = Column(String, nullable=False)
    entreprise_id = Column(Integer, ForeignKey('entreprise.id'))
    
    # Relation avec l'entreprise
    entreprise = relationship("Entreprise", back_populates="responsables_rh")
    
    # Certificats générés
    # certificats = relationship("Certificat", back_populates="responsable_rh")
    
    __mapper_args__ = {
        'polymorphic_identity': 'responsable_rh',
    }