"""
Dialog de clôture Z — comptage espèces, calcul écart, impression rapport.
"""
from datetime import datetime

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QMessageBox, QScrollArea, QWidget
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QIntValidator

from ui.theme import Theme


def _ligne_rapport(layout, label: str, valeur: str, bold: bool = False, couleur: str = ''):
    row = QHBoxLayout()
    lbl = QLabel(label)
    lbl.setStyleSheet(f"color: {couleur or Theme.c('text_secondary')}; font-size: 11px;")
    val = QLabel(valeur)
    val.setAlignment(Qt.AlignRight)
    if bold:
        val.setFont(QFont("Segoe UI", 11, QFont.Bold))
        lbl.setFont(QFont("Segoe UI", 11, QFont.Bold))
        lbl.setStyleSheet(f"color: {couleur or Theme.c('text')}; font-size: 11px;")
    row.addWidget(lbl)
    row.addStretch()
    row.addWidget(val)
    layout.addLayout(row)


class ClotureZDialog(QDialog):
    """Dialog de clôture Z de fin de journée."""

    cloture_effectuee = Signal(dict)  # rapport_dict

    def __init__(self, utilisateur: dict, parent=None):
        super().__init__(parent)
        self.utilisateur = utilisateur
        self._rapport_data = None
        self.setWindowTitle("Clôture Z — Fin de journée")
        self.setMinimumSize(480, 580)
        self.resize(500, 620)
        self._setup_ui()
        self._charger_rapport_x()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # Titre
        titre = QLabel("Clôture Z — Rapport de caisse")
        titre.setFont(QFont("Segoe UI", 14, QFont.Bold))
        titre.setAlignment(Qt.AlignCenter)
        layout.addWidget(titre)

        # Zone rapport (scrollable)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: 1px solid #E5E7EB; border-radius: 6px; }")
        self._rapport_widget = QWidget()
        self._rapport_layout = QVBoxLayout(self._rapport_widget)
        self._rapport_layout.setSpacing(6)
        self._rapport_layout.setContentsMargins(16, 12, 16, 12)
        scroll.setWidget(self._rapport_widget)
        layout.addWidget(scroll, 1)

        # Séparateur
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color: {Theme.c('card_border')};")
        layout.addWidget(sep)

        # Fond compté réel
        lbl_fond = QLabel("Fond compté réel (FCFA)")
        lbl_fond.setFont(QFont("Segoe UI", 11, QFont.Bold))
        layout.addWidget(lbl_fond)

        self._input_fond = QLineEdit()
        self._input_fond.setPlaceholderText("Comptez vos billets et saisissez le total")
        self._input_fond.setValidator(QIntValidator(0, 99999999))
        self._input_fond.setAlignment(Qt.AlignRight)
        self._input_fond.setMinimumHeight(42)
        self._input_fond.setFont(QFont("Segoe UI", 13))
        self._input_fond.textChanged.connect(self._recalc_ecart)
        layout.addWidget(self._input_fond)

        self._lbl_ecart = QLabel("Écart : —")
        self._lbl_ecart.setAlignment(Qt.AlignRight)
        self._lbl_ecart.setFont(QFont("Segoe UI", 11, QFont.Bold))
        layout.addWidget(self._lbl_ecart)

        # Boutons
        btns = QHBoxLayout()
        btn_annuler = QPushButton("Annuler")
        btn_annuler.setMinimumHeight(40)
        btn_annuler.clicked.connect(self.reject)
        btns.addWidget(btn_annuler)

        self._btn_cloturer = QPushButton("Clôturer + Imprimer Z")
        self._btn_cloturer.setMinimumHeight(40)
        self._btn_cloturer.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self._btn_cloturer.setStyleSheet(
            f"background: {Theme.c('danger')}; color: white; border: none; border-radius: 6px;"
        )
        self._btn_cloturer.setCursor(Qt.PointingHandCursor)
        self._btn_cloturer.clicked.connect(self._cloturer)
        btns.addWidget(self._btn_cloturer)
        layout.addLayout(btns)

    def _charger_rapport_x(self):
        from modules.sessions import rapport_x
        data = rapport_x()
        if not data:
            QLabel("Aucune session ouverte.")
            return
        self._rapport_data = data
        self._afficher_rapport(data)

    def _afficher_rapport(self, data: dict):
        # Vider
        while self._rapport_layout.count():
            item = self._rapport_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        s = data['session']
        devise = 'FCFA'

        try:
            from modules.fiscalite import get_devise
            devise = get_devise()
        except Exception:
            pass

        # Infos session
        try:
            dt_ouv = datetime.strptime(s['date_ouverture'], '%Y-%m-%d %H:%M:%S')
            ouv_str = dt_ouv.strftime('%d/%m/%Y %H:%M')
        except Exception:
            ouv_str = s['date_ouverture']

        _ligne_rapport(self._rapport_layout, "Caisse", s['id_caisse'])
        _ligne_rapport(self._rapport_layout, "Ouverture", ouv_str)

        # Caissier
        try:
            from database import db
            u = db.fetch_one("SELECT nom, prenom FROM utilisateurs WHERE id = ?", (s['id_caissier'],))
            if u:
                _ligne_rapport(self._rapport_layout, "Caissier", f"{u['prenom']} {u['nom']}")
        except Exception:
            pass

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color: {Theme.c('card_border')};")
        self._rapport_layout.addWidget(sep)

        _ligne_rapport(self._rapport_layout, "Nombre de ventes", str(data['nb_ventes']))
        _ligne_rapport(self._rapport_layout, "Ventes annulées", f"{data['total_annule']:,} {devise}")

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet(f"color: {Theme.c('card_border')};")
        self._rapport_layout.addWidget(sep2)

        modes = [
            ("Espèces",       data.get('total_especes', 0)),
            ("Mobile Money",  data.get('total_mobile', 0)),
            ("Virement",      data.get('total_virement', 0)),
            ("Chèque",        data.get('total_cheque', 0)),
            ("Carte",         data.get('total_carte', 0)),
            ("Autre",         data.get('total_autre', 0)),
            ("Crédit (ardoise)", data.get('total_credit', 0)),
        ]
        for label, montant in modes:
            if montant:
                _ligne_rapport(self._rapport_layout, label, f"{montant:,} {devise}")

        sep3 = QFrame()
        sep3.setFrameShape(QFrame.HLine)
        sep3.setStyleSheet(f"color: {Theme.c('card_border')};")
        self._rapport_layout.addWidget(sep3)

        _ligne_rapport(self._rapport_layout,
                       "TOTAL GÉNÉRAL", f"{data['total_general']:,} {devise}",
                       bold=True)
        _ligne_rapport(self._rapport_layout,
                       "Fond d'ouverture", f"{s['fond_ouverture']:,} {devise}")

        self._fond_calcule = data['total_especes'] + s['fond_ouverture']
        _ligne_rapport(self._rapport_layout,
                       "Fond théorique caisse", f"{self._fond_calcule:,} {devise}",
                       bold=True)

        self._rapport_layout.addStretch()

    def _recalc_ecart(self):
        if not hasattr(self, '_fond_calcule'):
            return
        try:
            fond_declare = int(self._input_fond.text() or 0)
        except ValueError:
            return
        ecart = fond_declare - self._fond_calcule
        if ecart == 0:
            self._lbl_ecart.setText("Écart : 0 FCFA ✓")
            self._lbl_ecart.setStyleSheet(f"color: {Theme.c('success')}; font-weight: bold;")
        elif ecart > 0:
            self._lbl_ecart.setText(f"Écart : +{ecart:,} FCFA (excédent)")
            self._lbl_ecart.setStyleSheet("color: #F59E0B; font-weight: bold;")
        else:
            self._lbl_ecart.setText(f"Écart : {ecart:,} FCFA (manquant)")
            self._lbl_ecart.setStyleSheet(f"color: {Theme.c('danger')}; font-weight: bold;")

    def _cloturer(self):
        if not self._rapport_data:
            QMessageBox.warning(self, "Erreur", "Aucune session à clôturer.")
            return

        texte = self._input_fond.text().strip()
        if not texte:
            QMessageBox.warning(self, "Champ requis",
                "Veuillez saisir le montant compté en caisse avant de clôturer.")
            self._input_fond.setFocus()
            return
        try:
            fond_declare = int(texte)
        except ValueError:
            QMessageBox.warning(self, "Valeur invalide", "Le montant saisi est invalide.")
            self._input_fond.setFocus()
            return

        rep = QMessageBox.question(
            self, "Confirmer la clôture Z",
            "Clôturer la session ?\n\n"
            "Après cette opération, aucune vente ne sera possible\n"
            "sans ouvrir une nouvelle session.",
            QMessageBox.Yes | QMessageBox.No
        )
        if rep != QMessageBox.Yes:
            return

        from modules.sessions import cloturer_session
        succes, message, rapport = cloturer_session(fond_declare)

        if not succes:
            QMessageBox.critical(self, "Erreur", message)
            return

        # PDF (archivé, jamais supprimé)
        pdf_path = ClotureZDialog._generer_pdf_z_static(rapport)

        self.cloture_effectuee.emit(rapport)

        msg = (
            f"Session clôturée avec succès.\n\n"
            f"Hash Z : {rapport['hash_cloture']}\n"
            f"Écart : {rapport['ecart']:+,} FCFA"
        )
        if pdf_path:
            msg += "\n\nOuvrir le rapport PDF maintenant ?"
            rep = QMessageBox.question(self, "Clôture Z effectuée", msg,
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if rep == QMessageBox.Yes:
                import os, sys, subprocess
                try:
                    if sys.platform == 'win32':
                        os.startfile(pdf_path)
                    elif sys.platform == 'darwin':
                        subprocess.Popen(['open', pdf_path])
                    else:
                        subprocess.Popen(['xdg-open', pdf_path])
                except Exception as e:
                    QMessageBox.warning(self, "Erreur", f"Impossible d'ouvrir le PDF : {e}")
        else:
            QMessageBox.information(self, "Clôture Z effectuée", msg)
        self.accept()

    @staticmethod
    def _imprimer_rapport_z_static(rapport: dict):
        try:
            from modules.imprimante import ImprimanteThermique
            if not ImprimanteThermique.est_disponible():
                return
            printer = ImprimanteThermique._connecter()
            if not printer:
                return

            from database import db
            nom_boutique = db.get_parametre('boutique_nom', 'Ma Boutique')
            from modules.imprimante import LARGEURS
            largeur = LARGEURS.get(db.get_parametre('imprimante_format', '80mm'), 48)

            printer.set(align='center', bold=True, double_height=True)
            printer.text(f"{nom_boutique}\n")
            printer.set(align='center', bold=False, double_height=False)
            printer.text("=" * largeur + "\n")
            printer.set(align='center', bold=True)
            printer.text("RAPPORT Z — CLOTURE\n")
            printer.set(align='left', bold=False)
            printer.text("=" * largeur + "\n")

            try:
                from datetime import datetime
                dt = datetime.strptime(rapport['date_cloture'], '%Y-%m-%d %H:%M:%S')
                printer.text(f"Date : {dt.strftime('%d/%m/%Y %H:%M')}\n")
            except Exception:
                printer.text(f"Date : {rapport['date_cloture']}\n")

            printer.text(f"Caisse : {rapport['id_caisse']}\n")
            printer.text("-" * largeur + "\n")
            total_general = rapport.get('total_general') or (
                rapport.get('total_especes', 0) + rapport.get('total_mobile', 0) +
                rapport.get('total_virement', 0) + rapport.get('total_cheque', 0) +
                rapport.get('total_carte', 0) + rapport.get('total_autre', 0)
            )
            printer.text(f"Nb ventes    : {rapport.get('nb_ventes', 0)}\n")
            modes_ticket = [
                ("Especes     ", 'total_especes'),
                ("Mobile Money", 'total_mobile'),
                ("Virement    ", 'total_virement'),
                ("Cheque      ", 'total_cheque'),
                ("Carte       ", 'total_carte'),
                ("Autre       ", 'total_autre'),
                ("Credit      ", 'total_credit'),
            ]
            for label, key in modes_ticket:
                val = rapport.get(key, 0) or 0
                if val:
                    printer.text(f"{label} : {val:,} F\n")
            printer.text(f"Annulees     : {rapport.get('total_annule', 0):,} F\n")
            printer.text("-" * largeur + "\n")
            printer.set(bold=True)
            printer.text(f"TOTAL        : {total_general:,} F\n")
            printer.set(bold=False)
            printer.text(f"Fond ouvert  : {rapport.get('fond_ouverture', 0):,} F\n")
            printer.text(f"Fond theoriq : {rapport.get('fond_cloture_calcule', 0):,} F\n")
            printer.text(f"Fond compte  : {rapport.get('fond_cloture_declare', 0):,} F\n")
            printer.set(bold=True)
            ecart = rapport.get('ecart', 0)
            printer.text(f"ECART        : {ecart:+,} F\n")
            printer.set(bold=False)
            printer.text("=" * largeur + "\n")
            printer.text(f"Hash : {rapport['hash_cloture']}\n")
            printer.text("\n\n\n")
            try:
                printer.cut()
            except Exception:
                pass
            printer.close()
        except Exception as e:
            from modules.logger import get_logger
            get_logger('sessions').warning(f"Impression Z échouée : {e}")

    @staticmethod
    def _generer_pdf_z_static(rapport: dict) -> str | None:
        try:
            import os
            import config
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm
            from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
            from database import db

            os.makedirs(config.RECUS_DIR, exist_ok=True)
            date_str = rapport['date_cloture'].replace(':', '').replace(' ', '_')
            pdf_path = os.path.join(config.RECUS_DIR, f"rapport_z_{date_str}.pdf")

            doc = SimpleDocTemplate(pdf_path, pagesize=A4,
                                    leftMargin=2*cm, rightMargin=2*cm,
                                    topMargin=2*cm, bottomMargin=2*cm)
            styles = getSampleStyleSheet()
            elements = []

            nom_boutique = db.get_parametre('boutique_nom', 'Ma Boutique')
            devise = 'FCFA'
            try:
                from modules.fiscalite import get_devise
                devise = get_devise()
            except Exception:
                pass

            # Titre
            elements.append(Paragraph(nom_boutique, ParagraphStyle(
                'Titre', fontSize=16, fontName='Helvetica-Bold', alignment=TA_CENTER)))
            elements.append(Paragraph("RAPPORT Z — CLÔTURE DE CAISSE", ParagraphStyle(
                'Sous', fontSize=13, fontName='Helvetica-Bold', alignment=TA_CENTER,
                textColor=colors.HexColor('#EF4444'))))
            elements.append(Spacer(1, 0.5*cm))

            try:
                from datetime import datetime
                dt = datetime.strptime(rapport['date_cloture'], '%Y-%m-%d %H:%M:%S')
                date_affichage = dt.strftime('%d/%m/%Y %H:%M')
            except Exception:
                date_affichage = rapport['date_cloture']

            total_general = rapport.get('total_general') or (
                rapport.get('total_especes', 0) + rapport.get('total_mobile', 0)
            )
            modes_data = []
            for label, key in [
                ('Espèces', 'total_especes'),
                ('Mobile Money', 'total_mobile'),
                ('Virement', 'total_virement'),
                ('Chèque', 'total_cheque'),
                ('Carte', 'total_carte'),
                ('Autre', 'total_autre'),
                ('Crédit (ardoise)', 'total_credit'),
            ]:
                val = rapport.get(key, 0) or 0
                if val:
                    modes_data.append([label, f"{val:,} {devise}"])

            data = [
                ['Date clôture', date_affichage],
                ['Caisse', rapport['id_caisse']],
                ['Nombre de ventes', str(rapport.get('nb_ventes', 0))],
                ['', ''],
                *modes_data,
                ['Ventes annulées', f"{rapport.get('total_annule', 0):,} {devise}"],
                ['', ''],
                ['TOTAL GÉNÉRAL', f"{total_general:,} {devise}"],
                ['', ''],
                ['Fond d\'ouverture', f"{rapport.get('fond_ouverture', 0):,} {devise}"],
                ['Fond théorique', f"{rapport.get('fond_cloture_calcule', 0):,} {devise}"],
                ['Fond compté', f"{rapport.get('fond_cloture_declare', 0):,} {devise}"],
                ['ÉCART', f"{rapport.get('ecart', 0):+,} {devise}"],
                ['', ''],
                ['Hash Z', rapport['hash_cloture']],
            ]

            # Indices dynamiques
            idx_total = data.index(['TOTAL GÉNÉRAL', f"{total_general:,} {devise}"])
            idx_ecart = data.index(['ÉCART', f"{rapport.get('ecart', 0):+,} {devise}"])

            table = Table(data, colWidths=[7*cm, 8*cm])
            table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTNAME', (0, idx_total), (-1, idx_total), 'Helvetica-Bold'),
                ('FONTNAME', (0, idx_ecart), (-1, idx_ecart), 'Helvetica-Bold'),
                ('BACKGROUND', (0, idx_total), (-1, idx_total), colors.HexColor('#3B82F6')),
                ('TEXTCOLOR', (0, idx_total), (-1, idx_total), colors.white),
                ('BACKGROUND', (0, idx_ecart), (-1, idx_ecart),
                 colors.HexColor('#10B981') if rapport.get('ecart', 0) == 0 else colors.HexColor('#EF4444')),
                ('TEXTCOLOR', (0, idx_ecart), (-1, idx_ecart), colors.white),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.grey),
                ('INNERGRID', (0, 0), (-1, -1), 0.3, colors.lightgrey),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ]))
            elements.append(table)

            doc.build(elements)
            return pdf_path
        except Exception as e:
            from modules.logger import get_logger
            get_logger('sessions').warning(f"PDF Z échoué : {e}")
            import traceback
            get_logger('sessions').warning(traceback.format_exc())
            return None
