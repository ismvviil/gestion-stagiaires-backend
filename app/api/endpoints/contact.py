# app/api/endpoints/contact.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, validator
from app.api.deps import get_current_user, get_db
from app.models.contact import Contact, TypeMessage, StatusContact
from app.services.email_service import EmailService
import re

router = APIRouter()

# Schémas Pydantic
class ContactCreate(BaseModel):
    nom: str
    prenom: str
    email: EmailStr
    telephone: Optional[str] = None
    entreprise: Optional[str] = None
    poste: Optional[str] = None
    type_message: TypeMessage
    sujet: str
    message: str
    
    @validator('nom', 'prenom')
    def validate_names(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError('Le nom et prénom doivent contenir au moins 2 caractères')
        if len(v) > 100:
            raise ValueError('Le nom et prénom ne peuvent pas dépasser 100 caractères')
        return v.strip()
    
    @validator('telephone')
    def validate_phone(cls, v):
        if v and v.strip():
            # Regex simple pour numéros français/internationaux
            phone_pattern = r'^(?:\+212|0)([5-7]\d{8})$'
            if not re.match(phone_pattern, v.strip()):
                raise ValueError('Format de téléphone invalide')
            return v.strip()
        return v
    
    @validator('sujet')
    def validate_subject(cls, v):
        if not v or len(v.strip()) < 5:
            raise ValueError('Le sujet doit contenir au moins 5 caractères')
        if len(v) > 200:
            raise ValueError('Le sujet ne peut pas dépasser 200 caractères')
        return v.strip()
    
    @validator('message')
    def validate_message(cls, v):
        if not v or len(v.strip()) < 10:
            raise ValueError('Le message doit contenir au moins 10 caractères')
        if len(v) > 2000:
            raise ValueError('Le message ne peut pas dépasser 2000 caractères')
        return v.strip()

class ContactResponse(BaseModel):
    id: int
    nom: str
    prenom: str
    email: str
    telephone: Optional[str]
    entreprise: Optional[str]
    poste: Optional[str]
    type_message: TypeMessage
    sujet: str
    message: str
    status: StatusContact
    created_at: str
    
    class Config:
        from_attributes = True

class ContactListResponse(BaseModel):
    contacts: List[ContactResponse]
    total: int
    page: int
    limit: int

# Endpoints
@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_contact(
    contact: ContactCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Créer un nouveau message de contact et envoyer les notifications email.
    """
    try:
        # Récupérer l'IP et User-Agent pour le suivi
        client_ip = request.client.host
        user_agent = request.headers.get("user-agent", "")
        
        # Créer l'enregistrement en base
        db_contact = Contact(
            nom=contact.nom,
            prenom=contact.prenom,
            email=contact.email,
            telephone=contact.telephone,
            entreprise=contact.entreprise,
            poste=contact.poste,
            type_message=contact.type_message,
            sujet=contact.sujet,
            message=contact.message,
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        db.add(db_contact)
        db.commit()
        db.refresh(db_contact)
        
        # Préparer les données pour l'email
        email_data = {
            'nom': contact.nom,
            'prenom': contact.prenom,
            'email': contact.email,
            'telephone': contact.telephone,
            'entreprise': contact.entreprise,
            'poste': contact.poste,
            'type_message': contact.type_message.value,
            'sujet': contact.sujet,
            'message': contact.message
        }
        
        # Envoyer les emails de notification
        email_service = EmailService()
        email_sent = email_service.send_contact_notification(email_data)
        
        response_data = {
            "success": True,
            "message": "Votre message a été envoyé avec succès. Nous vous répondrons dans les plus brefs délais.",
            "contact_id": db_contact.id,
            "email_sent": email_sent
        }
        
        if not email_sent:
            response_data["warning"] = "Le message a été enregistré mais l'email de notification n'a pas pu être envoyé."
        
        return response_data
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'envoi du message: {str(e)}"
        )

@router.get("/", response_model=ContactListResponse)
async def get_contacts(
    skip: int = 0,
    limit: int = 50,
    status_filter: Optional[StatusContact] = None,
    type_filter: Optional[TypeMessage] = None,
    db: Session = Depends(get_db)
):
    """
    Récupérer la liste des messages de contact (endpoint admin).
    """
    query = db.query(Contact)
    
    # Filtres
    if status_filter:
        query = query.filter(Contact.status == status_filter)
    if type_filter:
        query = query.filter(Contact.type_message == type_filter)
    
    # Compter le total
    total = query.count()
    
    # Pagination
    contacts = query.order_by(Contact.created_at.desc()).offset(skip).limit(limit).all()
    
    # Formater les réponses
    contact_responses = []
    for contact in contacts:
        contact_responses.append(ContactResponse(
            id=contact.id,
            nom=contact.nom,
            prenom=contact.prenom,
            email=contact.email,
            telephone=contact.telephone,
            entreprise=contact.entreprise,
            poste=contact.poste,
            type_message=contact.type_message,
            sujet=contact.sujet,
            message=contact.message,
            status=contact.status,
            created_at=contact.created_at.strftime("%d/%m/%Y %H:%M")
        ))
    
    return ContactListResponse(
        contacts=contact_responses,
        total=total,
        page=(skip // limit) + 1,
        limit=limit
    )

@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(contact_id: int, db: Session = Depends(get_db)):
    """
    Récupérer un message de contact spécifique.
    """
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message de contact non trouvé"
        )
    
    return ContactResponse(
        id=contact.id,
        nom=contact.nom,
        prenom=contact.prenom,
        email=contact.email,
        telephone=contact.telephone,
        entreprise=contact.entreprise,
        poste=contact.poste,
        type_message=contact.type_message,
        sujet=contact.sujet,
        message=contact.message,
        status=contact.status,
        created_at=contact.created_at.strftime("%d/%m/%Y %H:%M")
    )

@router.patch("/{contact_id}/status")
async def update_contact_status(
    contact_id: int,
    new_status: StatusContact,
    reponse: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Mettre à jour le statut d'un message de contact.
    """
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message de contact non trouvé"
        )
    
    # Mettre à jour le statut
    if new_status == StatusContact.RESOLU and reponse:
        contact.marquer_resolu(reponse)
    else:
        contact.status = new_status
    
    db.commit()
    
    return {
        "success": True,
        "message": f"Statut mis à jour vers {new_status.value}",
        "contact_id": contact_id
    }