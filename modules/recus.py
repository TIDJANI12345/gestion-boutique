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
from config import RECUS_DIR, BOUTIQUE_NOM, BOUTIQUE_ADRESSE, BOUTIQUE_TELEPHONE, BOUTIQUE_EMAIL
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


def _dessiner_cachet(canvas, statut: str):
    """
    Dessine un tampon diagonal style Odoo dans le coin haut-droit.
    Positionné dans la zone d'en-tête (fond transparent) pour rester visible.
    """
    configs = {
        'paye':   ('PAYE',     (0.06, 0.56, 0.31)),
        'credit': ('A CREDIT', (0.93, 0.40, 0.00)),
        'solde':  ('SOLDE',    (0.06, 0.56, 0.31)),
    }
    if statut not in configs:
        return
    texte, (r, g, b) = configs[statut]
    page_width, page_height = A4
    canvas.saveState()
    # Coin haut-droit — zone d'en-tête sans fond de tableau
    canvas.translate(page_width - 3 * cm, page_height - 3 * cm)
    canvas.rotate(20)
    font_size = 30
    canvas.setFont("Helvetica-Bold", font_size)
    padding_x, padding_y = 14, 8
    text_w = canvas.stringWidth(texte, "Helvetica-Bold", font_size)
    rect_w = text_w + 2 * padding_x
    rect_h = font_size + 2 * padding_y
    # Bordure colorée (pas de fond pour ne pas masquer le contenu)
    canvas.setStrokeColorRGB(r, g, b)
    canvas.setLineWidth(2.0)
    canvas.roundRect(-rect_w / 2, -rect_h / 2, rect_w, rect_h, 6, fill=0, stroke=1)
    # Texte
    canvas.setFillColorRGB(r, g, b)
    canvas.drawCentredString(0, -font_size * 0.30, texte)
    canvas.restoreState()


def _make_page_callback(cachet=None):
    """Retourne un callback onFirstPage/onLaterPages avec cachet optionnel."""
    def _cb(canvas, doc):
        ajouter_filigrane_footer(canvas, doc)
        if cachet:
            _dessiner_cachet(canvas, cachet)
    return _cb


def ajouter_filigrane_footer(canvas, doc):
    """Ajoute le logo en filigrane et le footer sur chaque page"""
    canvas.saveState()

    # 1. WATERMARK (Logo en fond)
    try:
        logo_path = db.get_parametre('boutique_logo_path', '')
        if logo_path and os.path.exists(logo_path):
            canvas.setFillAlpha(0.1)
            page_width, page_height = A4
            img_size = 10 * cm
            x_pos = (page_width - img_size) / 2
            y_pos = (page_height - img_size) / 2
            canvas.drawImage(logo_path, x_pos, y_pos, width=img_size, height=img_size, mask='auto', preserveAspectRatio=True)
            canvas.setFillAlpha(1)
    except Exception as e:
        logger.warning(f"Erreur watermark: {e}")

    # 2. WATERMARK DEMO
    try:
        from modules.features import est_demo
        if est_demo():
            page_width, page_height = A4
            canvas.saveState()
            canvas.setFont("Helvetica-Bold", 72)
            canvas.setFillColorRGB(0.85, 0.85, 0.85)
            canvas.translate(page_width / 2, page_height / 2)
            canvas.rotate(45)
            canvas.drawCentredString(0, 0, "DEMONSTRATION")
            canvas.restoreState()
    except Exception:
        pass

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
        numero_vente = vente['numero_vente']
        date_vente = vente['date_vente']
        total = vente['total']
        client = vente['client'] if vente['client'] else ""

        # Informations boutique
        nom_boutique = db.get_parametre('boutique_nom', BOUTIQUE_NOM)
        adresse = db.get_parametre('boutique_adresse', BOUTIQUE_ADRESSE)
        telephone = db.get_parametre('boutique_telephone', BOUTIQUE_TELEPHONE)
        email_boutique = db.get_parametre('boutique_email', BOUTIQUE_EMAIL)
        ifu = db.get_parametre('boutique_ifu', '')
        rccm = db.get_parametre('boutique_rccm', '')
        message_pied = db.get_parametre('recu_message_pied', '')
        from modules.fiscalite import get_devise
        devise = get_devise()

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
        logo_path = db.get_parametre('boutique_logo_path', '')

        if logo_path and os.path.exists(logo_path):
            # AVEC LOGO : Disposition logo à gauche + infos à droite
            logo_img = Image(logo_path, width=3*cm, height=3*cm)

            info_boutique = [
                [Paragraph(nom_boutique.upper(), style_boutique)],
                [Paragraph(adresse, style_info)],
                [Paragraph(f"Tél: {telephone}", style_info)],
            ]
            if email_boutique:
                info_boutique.append([Paragraph(email_boutique, style_info)])
            if ifu:
                info_boutique.append([Paragraph(f"IFU: {ifu}", style_info)])
            if rccm:
                info_boutique.append([Paragraph(f"RCCM: {rccm}", style_info)])

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
            if email_boutique:
                elements.append(Paragraph(email_boutique, style_info))
            if ifu:
                elements.append(Paragraph(f"IFU: {ifu}", style_info))
            if rccm:
                elements.append(Paragraph(f"RCCM: {rccm}", style_info))

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
            if client_info['telephone']:
                info_data.append(['Tel. client:', client_info['telephone']])
            info_data.append(['Points fidelite:', str(client_info['points_fidelite'])])

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
            nom = detail['nom']
            quantite = detail['quantite']
            prix_unit = detail['prix_unitaire']
            sous_total = detail['sous_total']
            try:
                is_gros = bool(detail['is_prix_gros'])
            except Exception:
                is_gros = False

            try:
                unite = detail['unite_mesure'] or 'pièce'
            except Exception:
                unite = 'pièce'
            nom_affiche = f"{nom} ★" if is_gros else nom
            data.append([
                nom_affiche,
                f"{quantite} {unite}",
                f"{prix_unit:,.0f} {devise}",
                f"{sous_total:,.0f} {devise}"
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

        # Légende prix gros si au moins un article concerné
        if any(bool(d['is_prix_gros']) for d in details if 'is_prix_gros' in d.keys()):
            legende_gros = ParagraphStyle(
                'LégendeGros',
                parent=styles['Normal'],
                fontSize=8,
                textColor=colors.HexColor('#059669'),
                spaceBefore=3,
                fontName='Helvetica-Oblique'
            )
            elements.append(Paragraph("★ Prix gros appliqué", legende_gros))

        elements.append(Spacer(1, 0.3*cm))

        # ==========================================
        # TVA (si active)
        # ==========================================

        from modules.fiscalite import Fiscalite

        if Fiscalite.tva_active():
            decomp = Fiscalite.calculer_tva(total)
            tva_data = [
                ['Sous-total HT', f"{decomp['ht']:,.0f} {devise}"],
                [f"TVA ({decomp['taux']:.0f}%)", f"{decomp['tva']:,.0f} {devise}"],
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

        try:
            remise = float(vente['remise'] or 0)
        except Exception:
            remise = 0
        if remise > 0:
            sous_total_brut = total + remise
            remise_data = [
                ["Sous-total:", f"{sous_total_brut:,.0f} {devise}"],
                ["Remise:", f"- {remise:,.0f} {devise}"],
            ]
            remise_table = Table(remise_data, colWidths=[13*cm, 3*cm])
            remise_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('TEXTCOLOR', (1, 1), (1, 1), colors.HexColor('#EF4444')),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(remise_table)
            elements.append(Spacer(1, 0.1*cm))

        total_label = "TOTAL TTC" if Fiscalite.tva_active() else "TOTAL A PAYER"
        total_data = [[total_label, f"{total:,.0f} {devise}"]]

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
                'mobile_money': 'Mobile Money',
                'virement': 'Virement bancaire',
                'cheque': 'Chèque',
                'mixte': 'Paiement mixte',
                'orange_money': 'Orange Money',
                'mtn_momo': 'MTN MoMo',
                'moov_money': 'Moov Money',
                'wave': 'Wave',
            }

            paiement_data = []
            for p in paiements:
                mode_key = p['mode']
                mode = mode_labels.get(mode_key, mode_key)
                # For mobile_money, extract operator from reference if present
                if mode_key == 'mobile_money' and p['reference'] and p['reference'].startswith('['):
                    end = p['reference'].find(']')
                    if end > 0:
                        mode = p['reference'][1:end]
                montant = p['montant']
                montant_recu = p['montant_recu']
                monnaie_rendue = p['monnaie_rendue']
                reference = p['reference']

                paiement_data.append([f"Paiement {mode}:", f"{montant:,.0f} {devise}"])
                if mode_key == 'especes' and montant_recu and monnaie_rendue:
                    paiement_data.append(["Montant reçu:", f"{montant_recu:,.0f} {devise}"])
                    paiement_data.append(["Monnaie rendue:", f"{monnaie_rendue:,.0f} {devise}"])
                ref_display = reference
                if mode_key == 'mobile_money' and reference and reference.startswith('['):
                    end = reference.find(']')
                    ref_display = reference[end + 1:].strip() if end > 0 else reference
                if ref_display:
                    paiement_data.append(["Référence:", ref_display])

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

        # Infos ardoise (crédit avec acompte)
        ardoise_info = db.fetch_one(
            "SELECT montant_initial, montant_restant FROM ardoise WHERE vente_id = ? AND statut != 'solde'",
            (vente_id,)
        )
        if ardoise_info:
            ardoise_info = dict(ardoise_info)
            acompte = ardoise_info['montant_initial'] - ardoise_info['montant_restant']
            elements.append(Spacer(1, 0.4*cm))
            credit_data = []
            if acompte > 0:
                credit_data.append(["Acompte versé :", f"{acompte:,.0f} {devise}"])
            credit_data.append(["Montant en ardoise :", f"{ardoise_info['montant_restant']:,.0f} {devise}"])
            c_table = Table(credit_data, colWidths=[5*cm, 11*cm])
            c_table.setStyle(TableStyle([
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#FCD34D')),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#FCD34D')),
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FFFBEB')),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('TEXTCOLOR', (1, len(credit_data)-1), (1, len(credit_data)-1), colors.HexColor('#B45309')),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (1, 0), (-1, -1), 'LEFT'),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(c_table)

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

        # Réseaux sociaux
        facebook  = db.get_parametre('boutique_facebook', '')
        instagram = db.get_parametre('boutique_instagram', '')
        whatsapp  = db.get_parametre('boutique_whatsapp', '')
        rs_parts = []
        if facebook:
            rs_parts.append(f"Facebook: {facebook}")
        if instagram:
            rs_parts.append(f"Instagram: {instagram}")
        if whatsapp:
            rs_parts.append(f"WhatsApp: {whatsapp}")
        if rs_parts:
            style_rs = ParagraphStyle(
                'Socials',
                parent=styles['Normal'],
                fontSize=9,
                alignment=TA_CENTER,
                textColor=colors.HexColor('#3B82F6'),
                spaceBefore=4,
            )
            elements.append(Paragraph("  |  ".join(rs_parts), style_rs))

        if message_pied:
            style_msg_pied = ParagraphStyle(
                'MsgPied',
                parent=styles['Normal'],
                fontSize=9,
                alignment=TA_CENTER,
                textColor=colors.HexColor('#6B7280'),
                spaceBefore=6,
                fontName='Helvetica-Oblique'
            )
            elements.append(Paragraph(message_pied, style_msg_pied))

        # ==========================================
        # CONSTRUIRE LE PDF
        # ==========================================

        # Cachet statut paiement
        has_credit = bool(db.fetch_one(
            "SELECT 1 FROM ardoise WHERE vente_id = ? AND statut != 'solde'", (vente_id,)
        ))
        if has_credit and db.get_parametre('cachet_recu_credit', '1') == '1':
            cachet = 'credit'
        elif not has_credit and db.get_parametre('cachet_recu_vente', '1') == '1':
            cachet = 'paye'
        else:
            cachet = None

        doc.build(
            elements,
            onFirstPage=_make_page_callback(cachet),
            onLaterPages=_make_page_callback(cachet),
        )

        logger.info(f"Recu PDF genere: {filepath}")
        return filepath

    except Exception as e:
        logger.error(f"Erreur lors de la generation du recu: {e}")
        import traceback
        traceback.print_exc()
        return None


def generer_recu_encaissement(ardoise_id: int, encaissement: dict) -> str | None:
    """
    Génère un reçu PDF de paiement sur ardoise.
    encaissement : dict avec montant, mode_paiement, reference, date_encaissement
    """
    try:
        ardoise = db.fetch_one(
            """SELECT a.*, c.nom as client_nom, c.telephone as client_tel,
                      v.numero_vente
               FROM ardoise a
               JOIN clients c ON a.client_id = c.id
               LEFT JOIN ventes v ON a.vente_id = v.id
               WHERE a.id = ?""",
            (ardoise_id,)
        )
        if not ardoise:
            return None
        ardoise = dict(ardoise)

        from modules.fiscalite import get_devise
        devise = get_devise()
        nom_boutique = db.get_parametre('boutique_nom', BOUTIQUE_NOM)
        adresse      = db.get_parametre('boutique_adresse', BOUTIQUE_ADRESSE)
        telephone    = db.get_parametre('boutique_telephone', BOUTIQUE_TELEPHONE)

        filename = f"encaissement_ardoise_{ardoise_id}_{encaissement.get('id', 'x')}.pdf"
        filepath = os.path.join(RECUS_DIR, filename)

        doc = SimpleDocTemplate(
            filepath, pagesize=A4,
            rightMargin=2*cm, leftMargin=2*cm,
            topMargin=1.5*cm, bottomMargin=1.5*cm
        )
        styles = getSampleStyleSheet()
        elements = []

        def _st(name, **kw):
            return ParagraphStyle(name, parent=styles['Normal'], **kw)

        # En-tête boutique
        s_titre = _st('BT', fontSize=18, fontName='Helvetica-Bold',
                      alignment=TA_CENTER, textColor=colors.HexColor('#1F2937'), spaceAfter=4)
        s_info  = _st('BI', fontSize=10, alignment=TA_CENTER,
                      textColor=colors.HexColor('#6B7280'), spaceAfter=2)
        elements.append(Paragraph(nom_boutique.upper(), s_titre))
        elements.append(Paragraph(adresse, s_info))
        elements.append(Paragraph(f"Tél : {telephone}", s_info))
        elements.append(Spacer(1, 0.5*cm))

        # Titre document
        s_doc = _st('DOC', fontSize=16, fontName='Helvetica-Bold',
                    alignment=TA_CENTER, textColor=colors.HexColor('#1F2937'), spaceAfter=4)
        elements.append(Paragraph("REÇU DE PAIEMENT", s_doc))

        sep = Table([['']], colWidths=[16*cm])
        sep.setStyle(TableStyle([('LINEBELOW', (0,0),(-1,0), 2, colors.HexColor('#E5E7EB'))]))
        elements.append(sep)
        elements.append(Spacer(1, 0.5*cm))

        # Infos
        try:
            dt = datetime.strptime(str(encaissement.get('date_encaissement', '')), "%Y-%m-%d %H:%M:%S")
            date_fmt = dt.strftime("%d/%m/%Y %H:%M")
        except Exception:
            date_fmt = str(encaissement.get('date_encaissement', ''))

        mode_labels = {
            'especes': 'Espèces', 'mobile_money': 'Mobile Money',
            'virement': 'Virement', 'autre': 'Autre',
        }
        mode_affiche = mode_labels.get(encaissement.get('mode_paiement', ''), encaissement.get('mode_paiement', ''))

        montant_paye  = float(encaissement.get('montant', 0))
        montant_restant = float(ardoise['montant_restant'])
        montant_initial = float(ardoise['montant_initial'])

        info_rows = [
            ['Client :', ardoise['client_nom']],
            ['Téléphone :', ardoise['client_tel'] or '—'],
            ['Date :', date_fmt],
            ['Mode :', mode_affiche],
        ]
        if encaissement.get('reference'):
            info_rows.append(['Référence :', encaissement['reference']])
        if ardoise.get('numero_vente'):
            info_rows.append(['Vente N° :', ardoise['numero_vente']])

        info_table = Table(info_rows, colWidths=[4*cm, 12*cm])
        info_table.setStyle(TableStyle([
            ('BOX', (0,0),(-1,-1), 1, colors.HexColor('#E5E7EB')),
            ('INNERGRID', (0,0),(-1,-1), 0.5, colors.HexColor('#E5E7EB')),
            ('FONTNAME', (0,0),(0,-1), 'Helvetica-Bold'),
            ('LEFTPADDING', (0,0),(-1,-1), 10),
            ('RIGHTPADDING', (0,0),(-1,-1), 10),
            ('TOPPADDING', (0,0),(-1,-1), 7),
            ('BOTTOMPADDING', (0,0),(-1,-1), 7),
            ('BACKGROUND', (0,0),(-1,-1), colors.HexColor('#F9FAFB')),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 0.6*cm))

        # Tableau montants
        montant_rows = [
            ['Montant total de l\'ardoise :', f"{montant_initial:,.0f} {devise}"],
            ['Montant payé ce jour :', f"{montant_paye:,.0f} {devise}"],
            ['Solde restant :', f"{montant_restant:,.0f} {devise}"],
        ]
        bg_restant = colors.HexColor('#D1FAE5') if montant_restant <= 0.01 else colors.HexColor('#FEF3C7')

        m_table = Table(montant_rows, colWidths=[10*cm, 6*cm])
        m_table.setStyle(TableStyle([
            ('BOX', (0,0),(-1,-1), 1, colors.black),
            ('INNERGRID', (0,0),(-1,-1), 0.5, colors.black),
            ('FONTNAME', (0,0),(0,-1), 'Helvetica-Bold'),
            ('FONTNAME', (1,0),(-1,-1), 'Helvetica-Bold'),
            ('ALIGN', (1,0),(-1,-1), 'RIGHT'),
            ('LEFTPADDING', (0,0),(-1,-1), 12),
            ('RIGHTPADDING', (0,0),(-1,-1), 12),
            ('TOPPADDING', (0,0),(-1,-1), 10),
            ('BOTTOMPADDING', (0,0),(-1,-1), 10),
            ('FONTSIZE', (0,0),(-1,-1), 11),
            # Ligne du solde colorée
            ('BACKGROUND', (0,2),(-1,2), bg_restant),
            ('TEXTCOLOR', (1,1),(1,1), colors.HexColor('#059669')),
        ]))
        elements.append(m_table)
        elements.append(Spacer(1, 0.6*cm))

        # Message de solde
        s_msg = _st('MSG', fontSize=11, alignment=TA_CENTER, spaceAfter=4, fontName='Helvetica-Bold')
        if montant_restant <= 0.01:
            s_msg_c = _st('MSG2', fontSize=11, alignment=TA_CENTER, fontName='Helvetica-Bold',
                          textColor=colors.HexColor('#059669'))
            elements.append(Paragraph("✓ Ardoise entièrement soldée", s_msg_c))
        else:
            s_msg_w = _st('MSG3', fontSize=10, alignment=TA_CENTER,
                          textColor=colors.HexColor('#B45309'))
            elements.append(Paragraph(
                f"Il reste {montant_restant:,.0f} {devise} à régler.", s_msg_w
            ))

        elements.append(Spacer(1, 1*cm))

        # Signatures
        sig_data = [['Signature client', 'Signature vendeur']]
        sig_table = Table(sig_data, colWidths=[8*cm, 8*cm])
        sig_table.setStyle(TableStyle([
            ('ALIGN', (0,0),(-1,-1), 'CENTER'),
            ('FONTNAME', (0,0),(-1,-1), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0),(-1,-1), 10),
            ('TOPPADDING', (0,0),(-1,-1), 40),
            ('BOX', (0,0),(0,-1), 0.5, colors.HexColor('#9CA3AF')),
            ('BOX', (1,0),(1,-1), 0.5, colors.HexColor('#9CA3AF')),
        ]))
        elements.append(sig_table)

        # Statut cachet (selon préférence)
        if db.get_parametre('cachet_recu_encaissement', '1') == '1':
            cachet = 'solde' if montant_restant <= 0.01 else 'credit'
        else:
            cachet = None

        doc.build(
            elements,
            onFirstPage=_make_page_callback(cachet),
            onLaterPages=_make_page_callback(cachet),
        )

        logger.info(f"Reçu encaissement généré : {filepath}")
        return filepath

    except Exception as e:
        logger.error(f"Erreur reçu encaissement : {e}")
        import traceback
        traceback.print_exc()
        return None


def nettoyer_recus_vente():
    """
    Supprime les PDFs de reçus de vente dans RECUS_DIR.
    Garde uniquement les rapports Z (rapport_z_*.pdf) et encaissements ardoise.
    """
    if not os.path.isdir(RECUS_DIR):
        return 0
    supprimes = 0
    for f in os.listdir(RECUS_DIR):
        if f.startswith('recu_') and f.endswith('.pdf'):
            try:
                os.remove(os.path.join(RECUS_DIR, f))
                supprimes += 1
            except Exception:
                pass
    logger.info(f"Nettoyage RECUS_DIR : {supprimes} reçu(s) de vente supprimé(s)")
    return supprimes
