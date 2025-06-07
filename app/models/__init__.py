from app.models.base import BaseModel
from app.models.utilisateur import Utilisateur, utilisateur_role
from app.models.role import Role
from app.models.responsable_rh import ResponsableRH
from app.models.recruteur import Recruteur
from app.models.stagiaire import Stagiaire
# from app.models.entreprise import Entreprise 
from app.models.entreprise import Entreprise

from app.models.message import Message
from app.models.offre import Offre
from app.models.candidature import Candidature, StatusCandidature

from app.models.conversation import Conversation
from app.models.message import Message
from app.models.stage import Stage , StatusStage
from app.models.mission import Mission , StatusMissionEnum , PrioriteMissionEnum


# 🆕 NOUVEAUX IMPORTS : Modèles d'évaluation
from app.models.evaluation import (
    # Modèles principaux
    Evaluation,
    DetailEvaluation,
    CritereEvaluation,
    Certificat,
    
    # Enums
    StatutEvaluation,
    TypeCritere,
    StatutCertificat
)

from app.models.contact import (StatusContact , TypeMessage , Contact)

from app.models.admin import Admin

# Importer d'autres modèles selon besoin