from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class Entreprise(BaseModel):
    # raison_social = Column(String, nullable=False)
    raison_social = Column(String, nullable=False, unique=True, index=True)  # ← Index pour recherche rapide

    secteur_activite = Column(String, nullable=False)
    description = Column(String, nullable=True)
    
    # NOUVEAUX CHAMPS
    adresse = Column(String, nullable=True)
    ville = Column(String, nullable=True)
    code_postal = Column(String, nullable=True)
    pays = Column(String, default="France")
    telephone = Column(String, nullable=True)
    site_web = Column(String, nullable=True)
    taille_entreprise = Column(String, nullable=True)  # "1-10", "11-50", "51-200", "200+"

    
    # Relations avec les utilisateurs
    recruteurs = relationship("Recruteur", back_populates="entreprise")
    responsables_rh = relationship("ResponsableRH", back_populates="entreprise")
    
    # Offres de stage
    offres = relationship("Offre", back_populates="entreprise")
    
    # Historique des stages
    # historiques = relationship("HistoriqueStage", back_populates="entreprise")

    # Ajouter cette relation
    stages = relationship("Stage", back_populates="entreprise")
    
    
    criteres_evaluation = relationship("CritereEvaluation", back_populates="entreprise")