from sqlalchemy import Column, String, Integer, ForeignKey, Date, Boolean, Text
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class Offre(BaseModel):
    """Modèle pour les offres de stage."""
    
    titre = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=False)
    type_stage = Column(String, nullable=False)  # Présentiel, télétravail, hybride
    remuneration = Column(Integer, nullable=True)
    localisation = Column(String, nullable=True)
    secteur = Column(String, nullable=False)
    date_debut = Column(Date, nullable=False)
    date_fin = Column(Date, nullable=False)
    competences_requises = Column(Text, nullable=True)
    est_active = Column(Boolean, default=True)

     # Clés étrangères
    entreprise_id = Column(Integer, ForeignKey("entreprise.id"), nullable=False)
    recruteur_id = Column(Integer, ForeignKey("recruteur.id"), nullable=False)

     # Relations
    entreprise = relationship("Entreprise", back_populates="offres")
    recruteur = relationship("Recruteur", back_populates="offres")
    candidatures = relationship("Candidature", back_populates="offre")

    def publier(self):
        """Publier l'offre."""
        self.est_active = True
        
    def fermer(self):
        """Fermer l'offre."""
        self.est_active = False