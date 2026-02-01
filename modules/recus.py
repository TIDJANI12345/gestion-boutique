"""
Module de génération de reçus PDF - Version améliorée avec QR code
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm, mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from datetime import datetime
import os
import io
from config import RECUS_DIR, BOUTIQUE_NOM, BOUTIQUE_ADRESSE, BOUTIQUE_TELEPHONE
from database import db
from modules.ventes import Vente
from modules.logger import get_logger

logger = get_logger('recus')

# Import conditionnel QR code
try:
    import qrcode
    QRCODE_DISPONIBLE = True
except ImportError:
    QRCODE_DISPONIBLE = False
    logger.warning("qrcode non installe - QR codes indisponibles sur les recus PDF")


def generer_qr_code_image(contenu, taille=4*cm):
    """Generer une image QR code pour ReportLab"""
    if not QRCODE_DISPONIBLE:
        return None
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=2,
        )
        qr.add_data(contenu)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        # Convertir en bytes pour ReportLab
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        return Image(buffer, width=taille, height=taille)
    except Exception as e:
        logger.warning(f"Erreur generation QR code: {e}")
        return None


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
        logger.warning(f"Erreur watermark: {e}")

    canvas.restoreState()


def _obtenir_infos_paiement(vente_id):
    """Recuperer les informations de paiement d'une vente (si disponibles)"""
    try:
        paiements = db.fetch_all(
            "SELECT mode, montant, montant_recu, monnaie_rendue, reference FROM paiements WHERE vente_id = ?",
            (vente_id,)
        )
        return paiements
    except Exception:
        return []


def generer_recu_pdf(vente_id):
    """
    Générer un reçu PDF professionnel pour une vente
    """
    try:
        # Récupérer les informations de la vente
        vente = Vente.obtenir_vente(vente_id)
        if not vente:
            logger.error("Vente introuvable")
            return None

        details = Vente.obtenir_details_vente(vente_id)
        if not details:
            logger.error("Aucun detail de vente")
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

        # ==========================================
        # EN-TÊTE AVEC LOGO
        # ==========================================

        # Vérifier si un logo existe
        logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'images', 'logo.png')

        if os.path.exists(logo_path):
            # AVEC LOGO : Disposition logo à gauche + infos à droite
            logo_img = Image(logo_path, width=3*cm, height=3*cm)

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

        try:
            dt = datetime.strptime(date_vente, "%Y-%m-%d %H:%M:%S")
            date_formatee = dt.strftime("%d/%m/%Y %H:%M")
        except Exception:
            date_formatee = date_vente

        info_data = [
            ['Numéro de vente:', numero_vente],
            ['Date:', date_formatee]
        ]

        if client:
            info_data.append(['Client:', client])

        # Informations client enrichies (telephone, points fidelite)
        client_info = db.fetch_one(
            "SELECT c.nom, c.telephone, c.points_fidelite FROM clients c "
            "JOIN ventes v ON v.client_id = c.id WHERE v.id = ?", (vente_id,))
        if client_info:
            if client_info[1]:
                info_data.append(['Tel. client:', client_info[1]])
            info_data.append(['Points fidelite:', str(client_info[2])])

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
        # TABLEAU DES PRODUITS
        # ==========================================

        data = [['Article', 'Qté', 'Prix unit.', 'Total']]

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

        table = Table(data, colWidths=[8*cm, 2*cm, 3*cm, 3*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3B82F6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 0.3*cm))

        # ==========================================
        # TVA (si active)
        # ==========================================

        from modules.fiscalite import Fiscalite

        if Fiscalite.tva_active():
            decomp = Fiscalite.calculer_tva(total)
            tva_data = [
                ['Sous-total HT', f"{decomp['ht']:,.0f} FCFA"],
                [f"TVA ({decomp['taux']:.0f}%)", f"{decomp['tva']:,.0f} FCFA"],
            ]

            tva_table = Table(tva_data, colWidths=[13*cm, 3*cm])
            tva_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
            ]))
            elements.append(tva_table)
            elements.append(Spacer(1, 0.1*cm))

        # ==========================================
        # TOTAL (fond vert)
        # ==========================================

        total_label = "TOTAL TTC" if Fiscalite.tva_active() else "TOTAL A PAYER"
        total_data = [[total_label, f"{total:,.0f} FCFA"]]

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
        # INFORMATIONS DE PAIEMENT
        # ==========================================

        paiements = _obtenir_infos_paiement(vente_id)
        if paiements:
            elements.append(Spacer(1, 0.5*cm))

            style_paiement_titre = ParagraphStyle(
                'PaiementTitre',
                parent=styles['Heading3'],
                fontSize=12,
                textColor=colors.HexColor('#1F2937'),
                spaceAfter=8,
                fontName='Helvetica-Bold'
            )
            elements.append(Paragraph("MODE DE PAIEMENT", style_paiement_titre))

            mode_labels = {
                'especes': 'Espèces',
                'orange_money': 'Orange Money',
                'mtn_momo': 'MTN MoMo',
                'moov_money': 'Moov Money',
            }

            paiement_data = []
            for p in paiements:
                mode = mode_labels.get(p[0], p[0])
                montant = p[1]
                montant_recu = p[2]
                monnaie_rendue = p[3]
                reference = p[4]

                paiement_data.append([f"Paiement {mode}:", f"{montant:,.0f} FCFA"])
                if p[0] == 'especes' and montant_recu and monnaie_rendue:
                    paiement_data.append(["Montant reçu:", f"{montant_recu:,.0f} FCFA"])
                    paiement_data.append(["Monnaie rendue:", f"{monnaie_rendue:,.0f} FCFA"])
                if reference:
                    paiement_data.append(["Référence:", reference])

            if paiement_data:
                p_table = Table(paiement_data, colWidths=[5*cm, 11*cm])
                p_table.setStyle(TableStyle([
                    ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#E5E7EB')),
                    ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
                    ('LEFTPADDING', (0, 0), (-1, -1), 10),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTNAME', (1, 0), (-1, -1), 'Helvetica'),
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F9FAFB')),
                ]))
                elements.append(p_table)

        # ==========================================
        # QR CODE
        # ==========================================

        qr_img = generer_qr_code_image(numero_vente, taille=3.5*cm)
        if qr_img:
            elements.append(Spacer(1, 0.5*cm))

            # QR code centre dans un tableau
            qr_label = ParagraphStyle(
                'QRLabel',
                parent=styles['Normal'],
                fontSize=8,
                textColor=colors.HexColor('#9CA3AF'),
                alignment=TA_CENTER,
                spaceBefore=4,
            )

            qr_data = [
                [qr_img],
                [Paragraph("Scannez pour vérifier ce reçu", qr_label)]
            ]
            qr_table = Table(qr_data, colWidths=[16*cm])
            qr_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            elements.append(qr_table)

        # ==========================================
        # PIED DE PAGE
        # ==========================================

        elements.append(Spacer(1, 0.8*cm))

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

        doc.build(
            elements,
            onFirstPage=ajouter_filigrane_footer,
            onLaterPages=ajouter_filigrane_footer
        )

        logger.info(f"Recu PDF genere: {filepath}")
        return filepath

    except Exception as e:
        logger.error(f"Erreur lors de la generation du recu: {e}")
        import traceback
        traceback.print_exc()
        return None
