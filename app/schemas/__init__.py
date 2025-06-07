from app.schemas.base import BaseSchema
from app.schemas.utilisateur import (
    UtilisateurBase, UtilisateurCreate, UtilisateurUpdate, 
    Utilisateur, UtilisateurAuth
)
from app.schemas.role import RoleBase, RoleCreate, RoleUpdate, Role
# from app.schemas.recruteur import RecruteurBase, RecruteurUpdate, Recruteur 
# 🆕 IMPORTS RECRUTEUR MIS À JOUR avec nouveaux schémas d'inscription
from app.schemas.recruteur import (
    RecruteurBase, 
    RecruteurUpdate, 
    Recruteur,
    RecruteurCreateWithExistingEntreprise,  # Nouveau
    RecruteurCreateWithNewEntreprise,       # Nouveau
    RecruteurInscription                    # Nouveau - schéma principal
)
from app.schemas.responsable_rh import ResponsableRHBase, ResponsableRHCreate, ResponsableRHUpdate, ResponsableRH
from app.schemas.stagiaire import StagiaireBase, StagiaireCreate, StagiaireUpdate, Stagiaire
# from app.schemas.entreprise import EntrepriseBase, EntrepriseCreate, EntrepriseUpdate, Entreprise
# 🆕 IMPORTS ENTREPRISE MIS À JOUR avec nouveaux champs et recherche
from app.schemas.entreprise import (
    EntrepriseBase, 
    EntrepriseCreate, 
    EntrepriseUpdate, 
    Entreprise,
    EntrepriseSearch  # Nouveau - pour la recherche
)
from app.schemas.auth import Token, TokenData
from app.schemas.offre import OffreBase, OffreCreate, OffreUpdate, Offre, OffreSearchResult
from app.schemas.candidature import CandidatureBase, CandidatureCreate, CandidatureResponse, CandidatureTraitement
from app.schemas.conversation import ConversationCreate, ConversationResponse, ConversationWithLastMessage
from app.schemas.message import MessageCreate, MessageResponse, MessageUpdate, ConversationMessages

from app.schemas.mission  import MissionBase, MissionCreate , MissionResponse , MissionAction , MissionUpdate
from app.schemas.stage import StageBase , StageCreate , StageResponse , StageUpdate , StageAction

# 🆕 NOUVEAUX IMPORTS : Schémas d'évaluation
from app.schemas.evaluation import (
    # Enums
    TypeCritereEnum,
    StatutEvaluationEnum,
    StatutCertificatEnum,
    
    # Critères d'évaluation
    CritereEvaluationBase,
    CritereEvaluationCreate,
    CritereEvaluationUpdate,
    CritereEvaluation,
    
    # Détails d'évaluation
    DetailEvaluationBase,
    DetailEvaluationCreate,
    DetailEvaluationUpdate,
    DetailEvaluation,
    
    # Évaluations
    EvaluationBase,
    EvaluationCreate,
    EvaluationUpdate,
    EvaluationValidation,
    Evaluation,
    EvaluationWithRelations,
    
    # Certificats
    CertificatBase,
    CertificatGeneration,
    Certificat,
    CertificatPublic,
    CertificatWithRelations,
    
    # Statistiques
    StatistiquesEvaluation,
    StatistiquesCritere,
    
    # Filtres
    EvaluationFilters,
    CertificatFilters,
    
    # Vérification QR Code
    VerificationQRCode,
    ResultatVerification
)

from app.schemas.admin import AdminBase, AdminCreate, AdminUpdate, Admin
from app.schemas.admin_stats import (
    StatistiquesGlobales, StatistiquesTemporelles, StatistiquesEntreprises,
    StatistiquesSecteurs, UtilisateurDetaille
)


