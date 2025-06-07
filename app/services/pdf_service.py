# app/services/pdf_service.py
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from io import BytesIO
import base64
from datetime import datetime
from typing import Any

from app.models.evaluation import Certificat

class PDFService:
    """Service pour générer des PDF de certificats."""

    @staticmethod
    def generer_certificat_pdf(certificat: Certificat) -> bytes:
        """Génère un PDF de certificat à la demande."""
        
        # Créer un buffer en mémoire
        buffer = BytesIO()
        
        # Configuration du document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=inch,
            leftMargin=inch,
            topMargin=inch,
            bottomMargin=inch
        )

        # Styles
        styles = getSampleStyleSheet()
        
        # Styles personnalisés
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )

        content_style = ParagraphStyle(
            'CustomContent',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=12,
            alignment=TA_LEFT
        )
        
        center_style = ParagraphStyle(
            'CustomCenter',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=12,
            alignment=TA_CENTER
        )
        
        # Contenu du PDF
        story = []

        # En-tête
        story.append(Paragraph("CERTIFICAT DE STAGE", title_style))
        story.append(Spacer(1, 20))
        
        # Informations de l'entreprise
        story.append(Paragraph(f"<b>{certificat.nom_entreprise}</b>", subtitle_style))
        story.append(Paragraph(f"Secteur: {certificat.secteur_entreprise}", center_style))
        story.append(Spacer(1, 30))

        # Corps du certificat
        story.append(Paragraph("certifie que", center_style))
        story.append(Spacer(1, 10))
        
        # Nom du stagiaire (en gras et plus grand)
        nom_complet = f"<b>{certificat.prenom_stagiaire} {certificat.nom_stagiaire}</b>"
        nom_style = ParagraphStyle(
            'NomStagiaire',
            parent=styles['Normal'],
            fontSize=18,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        story.append(Paragraph(nom_complet, nom_style))

        # Détails du stage
        story.append(Paragraph("a effectué un stage d'une durée de", center_style))
        story.append(Spacer(1, 10))
        
        # Durée du stage
        duree_text = f"<b>{certificat.duree_stage_jours} jours</b>"
        story.append(Paragraph(duree_text, center_style))
        story.append(Spacer(1, 20))

        # Tableau des informations du stage
        stage_data = [
            ['Titre du stage:', certificat.titre_stage],
            ['Période:', f"Du {certificat.date_debut_stage.strftime('%d/%m/%Y')} au {certificat.date_fin_stage.strftime('%d/%m/%Y')}"],
            ['Note finale:', f"{certificat.note_finale}/10"],
            ['Mention:', certificat.mention or 'Non attribuée'],
        ]
        
        stage_table = Table(stage_data, colWidths=[2*inch, 4*inch])
        stage_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        story.append(stage_table)
        story.append(Spacer(1, 30))
        
        # QR Code si disponible
        if certificat.qr_code_data:
            try:
                # Décoder le QR code base64
                qr_image_data = base64.b64decode(certificat.qr_code_data)
                qr_buffer = BytesIO(qr_image_data)
                
                # Créer l'image pour ReportLab
                qr_image = Image(qr_buffer, width=1.5*inch, height=1.5*inch)
                
                # Tableau pour centrer le QR code avec texte
                qr_data = [
                    [qr_image, 'Scannez ce QR code pour vérifier l\'authenticité du certificat'],
                    ['', f'Code de vérification: {certificat.code_unique}']
                ]
                
                qr_table = Table(qr_data, colWidths=[2*inch, 4*inch])
                qr_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (0, 0), 'CENTER'),
                    ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                    ('FONTSIZE', (1, 0), (1, -1), 10),
                ]))
                
                story.append(qr_table)
                story.append(Spacer(1, 20))

            except Exception as e:
                # Si erreur avec le QR code, juste afficher le code
                story.append(Paragraph(f"Code de vérification: {certificat.code_unique}", center_style))
                story.append(Spacer(1, 20))

        # Signature
        story.append(Spacer(1, 30))
        signature_data = [
            ['Délivré le:', datetime.now().strftime('%d/%m/%Y')],
            ['Par:', f"{certificat.prenom_evaluateur} {certificat.nom_evaluateur}"],
            ['Fonction:', certificat.poste_evaluateur],
        ]

        signature_table = Table(signature_data, colWidths=[1.5*inch, 3*inch])
        signature_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))

        # Aligner la signature à droite
        signature_style = ParagraphStyle(
            'SignatureStyle',
            parent=styles['Normal'],
            alignment=TA_RIGHT
        )

        story.append(Spacer(1, 1*inch))  # Espace pour signature manuscrite
        story.append(signature_table)
        
        # Footer avec informations de sécurité
        story.append(Spacer(1, 30))
        footer_text = f"""
        <font size="8" color="grey">
        Ce certificat est généré électroniquement et peut être vérifié en scannant le QR code ci-dessus.<br/>
        Code unique: {certificat.code_unique}<br/>
        Date de génération: {certificat.date_generation.strftime('%d/%m/%Y à %H:%M')}
        </font>
        """
        story.append(Paragraph(footer_text, center_style))
        
        # Construire le PDF
        doc.build(story)
        
        # Récupérer les bytes
        buffer.seek(0)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes
    
    @staticmethod
    def generer_certificat_simple(certificat: Certificat) -> bytes:
        """Version simplifiée du certificat PDF (sans QR code)."""
        
        buffer = BytesIO()
        
        # Configuration plus simple
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Titre simple
        story.append(Paragraph("CERTIFICAT DE STAGE", styles['Title']))
        story.append(Spacer(1, 20))
        
        # Contenu basique
        content = f"""
        <para align="center">
        <b>{certificat.nom_entreprise}</b><br/>
        certifie que<br/><br/>
        <b>{certificat.prenom_stagiaire} {certificat.nom_stagiaire}</b><br/><br/>
        a effectué un stage de {certificat.duree_stage_jours} jours<br/>
        du {certificat.date_debut_stage.strftime('%d/%m/%Y')} au {certificat.date_fin_stage.strftime('%d/%m/%Y')}<br/><br/>
        Note finale: {certificat.note_finale}/10<br/>
        Mention: {certificat.mention}<br/><br/>
        Code de vérification: {certificat.code_unique}
        </para>
        """
        
        story.append(Paragraph(content, styles['Normal']))
        
        doc.build(story)
        buffer.seek(0)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes