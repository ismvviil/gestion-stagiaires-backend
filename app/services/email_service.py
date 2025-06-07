# app/services/email_service.py
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional
from datetime import datetime
import os
from jinja2 import Template

class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.email_username = os.getenv("EMAIL_USERNAME", "votre-email@gmail.com")
        self.email_password = os.getenv("EMAIL_PASSWORD", "votre-mot-de-passe-app")
        self.from_email = os.getenv("FROM_EMAIL", "noreply@votre-plateforme.com")
        
    def send_contact_notification(self, contact_data: dict) -> bool:
        """Envoie une notification email lors d'un nouveau message de contact."""
        try:
            # Email vers l'administrateur
            admin_subject = f"[Contact] Nouveau message de {contact_data['nom']} {contact_data['prenom']}"
            admin_body = self._generate_admin_notification_body(contact_data)
            
            # Envoyer à l'admin
            self._send_email(
                to_email="souifiiismail@gmail.com",
                subject=admin_subject,
                body=admin_body,
                is_html=True
            )
            
            # Email de confirmation à l'expéditeur
            user_subject = "Confirmation de réception de votre message"
            user_body = self._generate_user_confirmation_body(contact_data)
            
            # Envoyer à l'utilisateur
            self._send_email(
                to_email=contact_data['email'],
                subject=user_subject,
                body=user_body,
                is_html=True
            )
            
            return True
            
        except Exception as e:
            print(f"Erreur lors de l'envoi d'email: {e}")
            return False
    
    def _generate_admin_notification_body(self, contact_data: dict) -> str:
        """Génère le corps de l'email pour l'administrateur."""
        template = Template("""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%); color: white; padding: 30px; border-radius: 12px 12px 0 0; text-align: center; }
                .content { background: white; padding: 30px; border: 1px solid #e5e7eb; }
                .footer { background: #f8fafc; padding: 20px; border-radius: 0 0 12px 12px; text-align: center; font-size: 14px; color: #6b7280; }
                .info-row { display: flex; margin-bottom: 15px; }
                .info-label { font-weight: 600; min-width: 120px; color: #374151; }
                .info-value { color: #6b7280; }
                .message-box { background: #f8fafc; padding: 20px; border-radius: 8px; border-left: 4px solid #3b82f6; margin: 20px 0; }
                .urgent { border-left-color: #ef4444; background: #fef2f2; }
                .type-badge { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; text-transform: uppercase; }
                .type-question { background: #dbeafe; color: #1e40af; }
                .type-support { background: #fef3c7; color: #92400e; }
                .type-demo { background: #d1fae5; color: #065f46; }
                .type-partenariat { background: #e0e7ff; color: #3730a3; }
                .type-autre { background: #f3f4f6; color: #374151; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📧 Nouveau Message de Contact</h1>
                    <p>Plateforme de Gestion des Stagiaires</p>
                </div>
                
                <div class="content">
                    <h2>Informations du Contact</h2>
                    
                    <div class="info-row">
                        <span class="info-label">Nom complet :</span>
                        <span class="info-value">{{ nom }} {{ prenom }}</span>
                    </div>
                    
                    <div class="info-row">
                        <span class="info-label">Email :</span>
                        <span class="info-value">{{ email }}</span>
                    </div>
                    
                    {% if telephone %}
                    <div class="info-row">
                        <span class="info-label">Téléphone :</span>
                        <span class="info-value">{{ telephone }}</span>
                    </div>
                    {% endif %}
                    
                    {% if entreprise %}
                    <div class="info-row">
                        <span class="info-label">Entreprise :</span>
                        <span class="info-value">{{ entreprise }}</span>
                    </div>
                    {% endif %}
                    
                    {% if poste %}
                    <div class="info-row">
                        <span class="info-label">Poste :</span>
                        <span class="info-value">{{ poste }}</span>
                    </div>
                    {% endif %}
                    
                    <div class="info-row">
                        <span class="info-label">Type :</span>
                        <span class="type-badge type-{{ type_message }}">{{ type_message_label }}</span>
                    </div>
                    
                    <div class="info-row">
                        <span class="info-label">Date :</span>
                        <span class="info-value">{{ date_envoi }}</span>
                    </div>
                    
                    <h3>Sujet : {{ sujet }}</h3>
                    
                    <div class="message-box {% if type_message == 'support' %}urgent{% endif %}">
                        <h4>Message :</h4>
                        <p>{{ message }}</p>
                    </div>
                    
                    <p><strong>💡 Action recommandée :</strong> Répondre dans les 24h pour maintenir une excellente expérience client.</p>
                </div>
                
                <div class="footer">
                    <p>Message reçu via la plateforme de gestion des stagiaires</p>
                    <p>Développé par SOUIFI ISMAIL & MOUATE Alaa eddine</p>
                </div>
            </div>
        </body>
        </html>
        """)
        
        type_labels = {
            'question': 'Question générale',
            'support': 'Support technique',
            'demo': 'Demande de démo',
            'partenariat': 'Partenariat',
            'autre': 'Autre'
        }
        
        return template.render(
            **contact_data,
            type_message_label=type_labels.get(contact_data['type_message'], 'Autre'),
            date_envoi=datetime.now().strftime("%d/%m/%Y à %H:%M")
        )
    
    def _generate_user_confirmation_body(self, contact_data: dict) -> str:
        """Génère le corps de l'email de confirmation pour l'utilisateur."""
        template = Template("""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 30px; border-radius: 12px 12px 0 0; text-align: center; }
                .content { background: white; padding: 30px; border: 1px solid #e5e7eb; }
                .footer { background: #f8fafc; padding: 20px; border-radius: 0 0 12px 12px; text-align: center; font-size: 14px; color: #6b7280; }
                .success-icon { font-size: 48px; margin-bottom: 20px; }
                .message-summary { background: #f0fdf4; padding: 20px; border-radius: 8px; border-left: 4px solid #10b981; margin: 20px 0; }
                .next-steps { background: #eff6ff; padding: 20px; border-radius: 8px; margin: 20px 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="success-icon">✅</div>
                    <h1>Message bien reçu !</h1>
                    <p>Merci pour votre contact</p>
                </div>
                
                <div class="content">
                    <h2>Bonjour {{ prenom }},</h2>
                    
                    <p>Nous avons bien reçu votre message concernant "<strong>{{ sujet }}</strong>" et nous vous remercions de votre intérêt pour notre plateforme de gestion des stagiaires.</p>
                    
                    <div class="message-summary">
                        <h3>📋 Récapitulatif de votre demande</h3>
                        <p><strong>Type :</strong> {{ type_message_label }}</p>
                        <p><strong>Date d'envoi :</strong> {{ date_envoi }}</p>
                        <p><strong>Votre message :</strong></p>
                        <p style="font-style: italic; color: #6b7280;">{{ message | truncate(200) }}...</p>
                    </div>
                    
                    <div class="next-steps">
                        <h3>🚀 Prochaines étapes</h3>
                        <p>Notre équipe va examiner votre demande et vous répondra dans les <strong>24 heures</strong>.</p>
                        <p>En attendant, vous pouvez :</p>
                        <ul>
                            <li>Consulter notre <a href="#" style="color: #3b82f6;">documentation</a></li>
                            <li>Découvrir nos <a href="#" style="color: #3b82f6;">fonctionnalités</a></li>
                            <li>Suivre nos actualités sur nos réseaux sociaux</li>
                        </ul>
                    </div>
                    
                    <p>Si vous avez des questions urgentes, n'hésitez pas à nous contacter directement à <a href="mailto:souifiiismail@gmail.com" style="color: #3b82f6;">souifiiismail@gmail.com</a>.</p>
                    
                    <p>Cordialement,<br>
                    L'équipe de la Plateforme de Gestion des Stagiaires</p>
                </div>
                
                <div class="footer">
                    <p>Cet email a été envoyé automatiquement, merci de ne pas y répondre.</p>
                    <p>Développé par SOUIFI ISMAIL & MOUATE Alaa eddine</p>
                </div>
            </div>
        </body>
        </html>
        """)
        
        type_labels = {
            'question': 'Question générale',
            'support': 'Support technique', 
            'demo': 'Demande de démonstration',
            'partenariat': 'Proposition de partenariat',
            'autre': 'Autre demande'
        }
        
        return template.render(
            **contact_data,
            type_message_label=type_labels.get(contact_data['type_message'], 'Autre'),
            date_envoi=datetime.now().strftime("%d/%m/%Y à %H:%M")
        )
    
    def _send_email(self, to_email: str, subject: str, body: str, is_html: bool = False) -> bool:
        """Envoie un email via SMTP."""
        try:
            # Créer le message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.from_email
            message["To"] = to_email
            
            # Ajouter le corps du message
            if is_html:
                part = MIMEText(body, "html", "utf-8")
            else:
                part = MIMEText(body, "plain", "utf-8")
            
            message.attach(part)
            
            # Créer une connexion sécurisée et envoyer l'email
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.email_username, self.email_password)
                server.sendmail(self.from_email, to_email, message.as_string())
            
            return True
            
        except Exception as e:
            print(f"Erreur lors de l'envoi d'email: {e}")
            return False