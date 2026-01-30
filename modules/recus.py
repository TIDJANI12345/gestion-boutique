"""
Module de génération de reçus PDF - Version améliorée
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm, mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
import os
from config import RECUS_DIR, BOUTIQUE_NOM, BOUTIQUE_ADRESSE, BOUTIQUE_TELEPHONE
from database import db
from modules.ventes import Vente
from reportlab.pdfgen import canvas

def ajouter_filigrane_footer(canvas, doc):
    """Ajoute le logo en filigrane et le footer sur chaque page"""
    canvas.saveState()
    
    # 1. WATERMARK (Logo en fond)
    try:
        logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'images', 'logo.png')
        if os.path.exists(logo_path):
            canvas.setFillAlpha(0.1)  # Transparence très faible (10%)
            # Centrer l'image (calcul approximatif pour A4)
            page_width, page_height = A4
            img_size = 10 * cm
            x_pos = (page_width - img_size) / 2
            y_pos = (page_height - img_size) / 2
            canvas.drawImage(logo_path, x_pos, y_pos, width=img_size, height=img_size, mask='auto', preserveAspectRatio=True)
            canvas.setFillAlpha(1)  # Rétablir l'opacité
    except Exception as e:
        print(f"Erreur watermark: {e}")

    canvas.restoreState()

def generer_recu_pdf(vente_id):
    """
    Générer un reçu PDF professionnel pour une vente
    """
    try:
        # Récupérer les informations de la vente
        vente = Vente.obtenir_vente(vente_id)
        if not vente:
            print("❌ Vente introuvable")
            return None
        
        details = Vente.obtenir_details_vente(vente_id)
        if not details:
            print("❌ Aucun détail de vente")
            return None
        
        # Informations vente
        numero_vente = vente[1]
        date_vente = vente[2]
        total = vente[3]
        client = vente[4] if len(vente) > 4 and vente[4] else ""
        
        # Informations boutique
        nom_boutique = db.get_parametre('boutique_nom', BOUTIQUE_NOM)
        adresse = db.get_parametre('boutique_adresse', BOUTIQUE_ADRESSE)
        telephone = db.get_parametre('boutique_telephone', BOUTIQUE_TELEPHONE)
        
        # Créer le PDF
        filename = f"recu_{numero_vente}.pdf"
        filepath = os.path.join(RECUS_DIR, filename)
        
        # Configuration du document (format ticket de caisse)
        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=1.5*cm,
            bottomMargin=1.5*cm
        )
        
        elements = []
        styles = getSampleStyleSheet()
        
        # ==========================================
        # STYLES PERSONNALISÉS
        # ==========================================
        
        # Style titre boutique
        style_boutique = ParagraphStyle(
            'Boutique',
            parent=styles['Heading1'],
            fontSize=20,
            textColor=colors.HexColor('#1F2937'),
            spaceAfter=5,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        # Style info boutique
        style_info = ParagraphStyle(
            'Info',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#6B7280'),
            alignment=TA_CENTER,
            spaceAfter=3
        )
        
        # Style numéro reçu
        style_numero = ParagraphStyle(
            'Numero',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#10B981'),
            spaceAfter=10,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        # Style détails vente
        style_detail = ParagraphStyle(
            'Detail',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#374151'),
            spaceAfter=4
        )
        
        # ==========================================
        # EN-TÊTE AVEC LOGO
        # ==========================================
        
        # Vérifier si un logo existe
        logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'images', 'logo.png')

        if os.path.exists(logo_path):
            # AVEC LOGO : Disposition logo à gauche + infos à droite
            
            # Tableau en-tête avec 2 colonnes
            logo_img = Image(logo_path, width=3*cm, height=3*cm)
            
            # Infos boutique (colonne droite)
            info_boutique = [
                [Paragraph(nom_boutique.upper(), style_boutique)],
                [Paragraph(adresse, style_info)],
                [Paragraph(f"Tél: {telephone}", style_info)]
            ]
            
            info_table = Table(info_boutique, colWidths=[13*cm])
            info_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            # Tableau principal : logo + infos
            header_data = [[logo_img, info_table]]
            header_table = Table(header_data, colWidths=[3*cm, 13*cm])
            header_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (0, -1), 0),
                ('RIGHTPADDING', (1, 0), (-1, -1), 0),
            ]))
            
            elements.append(header_table)
        
        else:
            # SANS LOGO : Disposition classique centrée
            elements.append(Paragraph(nom_boutique.upper(), style_boutique))
            elements.append(Paragraph(adresse, style_info))
            elements.append(Paragraph(f"Tél: {telephone}", style_info))
        
        elements.append(Spacer(1, 0.7*cm))
        
        # Titre "REÇU DE VENTE"
        titre_recu = ParagraphStyle(
            'TitreRecu',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1F2937'),
            spaceAfter=15,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        elements.append(Paragraph("REÇU DE VENTE", titre_recu))
        
        # Ligne de séparation décorative
        sep_table = Table([['']], colWidths=[16*cm])
        sep_table.setStyle(TableStyle([
            ('LINEABOVE', (0, 0), (-1, 0), 2, colors.HexColor('#E5E7EB')),
            ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#E5E7EB')),
        ]))
        elements.append(sep_table)
        
        elements.append(Spacer(1, 0.5*cm))
        
        # ==========================================
        # NUMÉRO DE REÇU ET BADGE SUCCÈS
        # ==========================================
        
        elements.append(Paragraph(f"REÇU N° {numero_vente}", style_numero))
        
        # Badge "Vente enregistrée"
        badge_style = ParagraphStyle(
            'Badge',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#059669'),
            alignment=TA_CENTER,
            spaceAfter=15,
            fontName='Helvetica-Bold'
        )
        elements.append(Paragraph("✓ VENTE ENREGISTRÉE", badge_style))
        
        elements.append(Spacer(1, 0.3*cm))
        
        # ==========================================
        # INFORMATIONS VENTE (tableau simple)
        # ==========================================
        
        # Formater la date ✅ AJOUTER CETTE PARTIE
        try:
            dt = datetime.strptime(date_vente, "%Y-%m-%d %H:%M:%S")
            date_formatee = dt.strftime("%d/%m/%Y %H:%M")
        except:
            date_formatee = date_vente

        # Tableau des infos basiques
        info_data = [
            ['Numéro de vente:', numero_vente],
            ['Date:', date_formatee]
        ]
        
        if client:
            info_data.append(['Client:', client])
        
        info_table = Table(info_data, colWidths=[5*cm, 11*cm])
        info_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (-1, -1), 'Helvetica'),
        ]))
        elements.append(info_table)
        
        elements.append(Spacer(1, 0.7*cm))
        
        # ==========================================
        # TITRE "ARTICLES VENDUS"
        # ==========================================
        
        titre_articles = ParagraphStyle(
            'TitreArticles',
            parent=styles['Heading3'],
            fontSize=13,
            textColor=colors.HexColor('#1F2937'),
            spaceAfter=10,
            fontName='Helvetica-Bold'
        )
        elements.append(Paragraph("ARTICLES VENDUS", titre_articles))
        
        # ==========================================
        # TABLEAU DES PRODUITS (style PHP)
        # ==========================================
        
        # En-tête du tableau
        data = [['Article', 'Qté', 'Prix unit.', 'Total']]
        
        # Lignes de produits
        for detail in details:
            nom = detail[1]
            quantite = detail[2]
            prix_unit = detail[3]
            sous_total = detail[4]
            
            data.append([
                nom,
                str(quantite),
                f"{prix_unit:,.0f} FCFA",
                f"{sous_total:,.0f} FCFA"
            ])
        
        # Créer le tableau
        table = Table(data, colWidths=[8*cm, 2*cm, 3*cm, 3*cm])
        table.setStyle(TableStyle([
            # En-tête (bleu)
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3B82F6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            
            # Corps
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            
            # Bordures
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.black),
            
            # Padding
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        elements.append(table)
        
        elements.append(Spacer(1, 0.3*cm))
        
        # ==========================================
        # TOTAL (style PHP - fond vert)
        # ==========================================
        
        total_data = [['TOTAL A PAYER', f"{total:,.0f} FCFA"]]
        
        total_table = Table(total_data, colWidths=[13*cm, 3*cm])
        total_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#10B981')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        elements.append(total_table)
        
       # ==========================================
        # PIED DE PAGE
        # ==========================================
        
        elements.append(Spacer(1, 1*cm))
        
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=10,
            alignment=TA_CENTER,
            spaceAfter=3
        )
        
        elements.append(Paragraph("Merci pour votre confiance !", footer_style))
        elements.append(Paragraph(f"Ce reçu a été généré automatiquement par {nom_boutique}", footer_style))
        
        # ==========================================
        # CONSTRUIRE LE PDF
        # ==========================================
        
       # Génération avec callbacks pour le watermark et footer
        doc.build(
            elements, 
            onFirstPage=ajouter_filigrane_footer, 
            onLaterPages=ajouter_filigrane_footer
        )
        
        print(f"✅ Reçu PDF généré: {filepath}")
        return filepath
        
    except Exception as e:
        print(f"❌ Erreur lors de la génération du reçu: {e}")
        import traceback
        traceback.print_exc()
        return None