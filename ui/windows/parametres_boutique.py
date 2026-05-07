"""
Paramètres boutique — admin seulement.
Infos boutique, logo, fiscal, cachets PDF, session timeout par rôle.
"""
import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QPushButton, QCheckBox, QScrollArea, QLineEdit,
    QComboBox, QFileDialog, QSpinBox, QTabWidget, QWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

from ui.theme import Theme
from ui.components.dialogs import information, erreur
from database import db


class ParametresBoutiqueWindow(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Paramètres boutique")
        self.setMinimumSize(720, 620)
        self._modifie = False
        self._setup_ui()
        self._charger()
        self._modifie = False  # reset après chargement

        # Connecter les champs texte
        for w in self.findChildren(QLineEdit):
            w.textChanged.connect(self._marquer)
        for w in self.findChildren(QComboBox):
            w.currentIndexChanged.connect(self._marquer)
        for w in self.findChildren(QSpinBox):
            w.valueChanged.connect(self._marquer)
        for w in self.findChildren(QCheckBox):
            w.stateChanged.connect(self._marquer)

    def _marquer(self, *_):
        self._modifie = True
        if hasattr(self, '_btn_save'):
            self._btn_save.setStyleSheet(self._style_actif())

    def _style_actif(self):
        return (f"QPushButton {{ background:{Theme.c('success')}; color:white; "
                f"padding:10px 28px; font-size:11pt; font-weight:bold; border-radius:6px; border:none; }}"
                f"QPushButton:hover {{ background:{Theme.c('success_hover')}; }}")

    def _style_neutre(self):
        return (f"QPushButton {{ background:{Theme.c('card_border')}; color:{Theme.c('text_secondary')}; "
                f"padding:10px 28px; font-size:11pt; font-weight:bold; border-radius:6px; border:none; }}")

    def _section(self, titre):
        lbl = QLabel(titre)
        lbl.setStyleSheet(f"font-size:13pt; font-weight:bold; color:{Theme.c('text')};")
        return lbl

    def _champ(self, layout, label_txt, placeholder, width=130):
        row = QHBoxLayout()
        lbl = QLabel(label_txt)
        lbl.setFixedWidth(width)
        lbl.setStyleSheet("font-size:10pt;")
        row.addWidget(lbl)
        entry = QLineEdit()
        entry.setPlaceholderText(placeholder)
        entry.setStyleSheet(f"padding:6px; border:1px solid {Theme.c('gray')}; border-radius:4px;")
        row.addWidget(entry)
        layout.addLayout(row)
        return entry

    def _frame(self):
        f = QFrame()
        f.setStyleSheet(f"background:{Theme.c('light')}; border-radius:8px; padding:16px;")
        return f

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header
        header = QFrame()
        header.setStyleSheet(f"background:{Theme.c('primary')};")
        header.setFixedHeight(65)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(30, 0, 30, 0)
        t = QLabel("Paramètres boutique")
        t.setStyleSheet("color:white; font-size:17pt; font-weight:bold;")
        hl.addWidget(t)
        root.addWidget(header)

        # Tabs
        self._tabs = QTabWidget()
        self._tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border:none; background:{Theme.c('bg')}; }}
            QTabBar::tab {{ padding:10px 20px; font-size:10pt; color:{Theme.c('text_secondary')}; }}
            QTabBar::tab:selected {{ color:{Theme.c('primary')}; font-weight:bold;
                border-bottom:2px solid {Theme.c('primary')}; }}
        """)

        self._tabs.addTab(self._onglet_boutique(), "Boutique")
        self._tabs.addTab(self._onglet_fiscal(), "Fiscal & Stock")
        self._tabs.addTab(self._onglet_recus(), "Reçus & Cachets")
        self._tabs.addTab(self._onglet_securite(), "Sécurité")
        root.addWidget(self._tabs)

        # Footer boutons
        foot = QFrame()
        foot.setStyleSheet(f"background:{Theme.c('bg')}; border-top:1px solid {Theme.c('card_border')};")
        fl = QHBoxLayout(foot)
        fl.setContentsMargins(20, 12, 20, 12)
        fl.addStretch()

        btn_fermer = QPushButton("Fermer")
        btn_fermer.setStyleSheet(f"padding:10px 24px; border:1px solid {Theme.c('card_border')}; border-radius:6px;")
        btn_fermer.setCursor(Qt.PointingHandCursor)
        btn_fermer.clicked.connect(self.reject)
        fl.addWidget(btn_fermer)

        self._btn_save = QPushButton("Enregistrer")
        self._btn_save.setStyleSheet(self._style_neutre())
        self._btn_save.setCursor(Qt.PointingHandCursor)
        self._btn_save.clicked.connect(self._enregistrer)
        fl.addWidget(self._btn_save)

        root.addWidget(foot)

    # ── Onglet Boutique ───────────────────────────────────────────────────────

    def _onglet_boutique(self):
        page = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border:none; }")

        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(30, 24, 30, 24)
        cl.setSpacing(18)

        # Infos boutique
        cl.addWidget(self._section("Informations boutique"))
        desc = QLabel("Ces informations apparaissent sur les reçus PDF et tickets thermiques.")
        desc.setStyleSheet(f"color:{Theme.c('text_secondary')}; font-size:10pt;")
        cl.addWidget(desc)

        f = self._frame()
        fl = QVBoxLayout(f)
        fl.setSpacing(8)
        self.input_nom      = self._champ(fl, "Nom :",       "Ma Boutique", 130)
        self.input_adresse  = self._champ(fl, "Adresse :",   "Cotonou, Bénin", 130)
        self.input_tel      = self._champ(fl, "Téléphone :", "+229 XX XX XX XX", 130)
        self.input_email    = self._champ(fl, "Email :",     "contact@maboutique.bj", 130)
        self.input_ifu      = self._champ(fl, "IFU :",       "1234567890123", 130)
        self.input_rccm     = self._champ(fl, "RCCM :",      "RB/ABC/24 B 12345", 130)
        fl.addSpacing(6)
        rs = QLabel("Réseaux sociaux (optionnel) :")
        rs.setStyleSheet("font-size:10pt; font-weight:bold;")
        fl.addWidget(rs)
        self.input_facebook  = self._champ(fl, "Facebook :",  "fb.com/maboutique", 130)
        self.input_instagram = self._champ(fl, "Instagram :", "@maboutique", 130)
        self.input_whatsapp  = self._champ(fl, "WhatsApp :",  "+229 XX XX XX XX", 130)
        fl.addSpacing(4)
        msg_lbl = QLabel("Message pied de page :")
        msg_lbl.setStyleSheet("font-size:10pt;")
        fl.addWidget(msg_lbl)
        self.input_message = QLineEdit()
        self.input_message.setPlaceholderText("Ex: Retour accepté sous 7 jours avec ticket de caisse")
        self.input_message.setStyleSheet(f"padding:6px; border:1px solid {Theme.c('gray')}; border-radius:4px;")
        fl.addWidget(self.input_message)
        cl.addWidget(f)

        # Logo
        cl.addWidget(self._section("Logo boutique"))
        lf = self._frame()
        ll = QVBoxLayout(lf)
        logo_row = QHBoxLayout()
        self._logo_preview = QLabel("Aucun\nlogo")
        self._logo_preview.setFixedSize(80, 80)
        self._logo_preview.setAlignment(Qt.AlignCenter)
        self._logo_preview.setStyleSheet(
            f"border:1px dashed {Theme.c('gray')}; border-radius:4px; "
            f"background:white; color:{Theme.c('gray')}; font-size:9pt;")
        logo_row.addWidget(self._logo_preview)

        logo_btns = QVBoxLayout()
        btn_logo = QPushButton("Choisir un logo…")
        btn_logo.setStyleSheet(f"background:{Theme.c('info')}; color:white; padding:8px 12px; border-radius:4px; font-weight:bold;")
        btn_logo.clicked.connect(self._choisir_logo)
        logo_btns.addWidget(btn_logo)
        btn_del_logo = QPushButton("Supprimer")
        btn_del_logo.setStyleSheet(f"background:{Theme.c('danger')}; color:white; padding:8px 12px; border-radius:4px;")
        btn_del_logo.clicked.connect(self._supprimer_logo)
        logo_btns.addWidget(btn_del_logo)
        logo_btns.addStretch()
        logo_row.addLayout(logo_btns)
        logo_row.addStretch()
        ll.addLayout(logo_row)
        hint = QLabel("PNG ou JPG recommandé · Affiché sur les reçus PDF.")
        hint.setStyleSheet(f"color:{Theme.c('gray')}; font-size:9pt;")
        ll.addWidget(hint)
        cl.addWidget(lf)

        cl.addStretch()
        scroll.setWidget(content)

        pl = QVBoxLayout(page)
        pl.setContentsMargins(0, 0, 0, 0)
        pl.addWidget(scroll)
        return page

    # ── Onglet Fiscal & Stock ─────────────────────────────────────────────────

    def _onglet_fiscal(self):
        page = QWidget()
        cl = QVBoxLayout(page)
        cl.setContentsMargins(30, 24, 30, 24)
        cl.setSpacing(18)

        cl.addWidget(self._section("Paramètres fiscaux"))

        f = self._frame()
        fl = QVBoxLayout(f)
        fl.setSpacing(12)

        # TVA
        tva_row = QHBoxLayout()
        tva_lbl = QLabel("TVA par défaut :")
        tva_lbl.setFixedWidth(160)
        tva_row.addWidget(tva_lbl)
        self._combo_tva = QComboBox()
        for label, val in [("Pas de TVA (0 %)", "0"), ("TVA 10 %", "10"), ("TVA 18 % — Bénin", "18")]:
            self._combo_tva.addItem(label, val)
        tva_row.addWidget(self._combo_tva)
        tva_row.addStretch()
        fl.addLayout(tva_row)
        tva_info = QLabel("Appliquée sur les reçus lorsque la TVA est activée sur la vente.")
        tva_info.setStyleSheet(f"color:{Theme.c('text_secondary')}; font-size:9pt;")
        fl.addWidget(tva_info)

        fl.addSpacing(8)

        # Code-barres par défaut
        cb_lbl = QLabel("Code-barres produit par défaut :")
        cb_lbl.setStyleSheet("font-size:10pt; font-weight:bold;")
        fl.addWidget(cb_lbl)
        self._combo_cb = QComboBox()
        self._combo_cb.addItem("Automatique — générer un code (produits sans étiquette)", "auto")
        self._combo_cb.addItem("Manuel — saisir ou scanner le code existant (EAN-13 importé)", "manuel")
        fl.addWidget(self._combo_cb)
        fl.addWidget(f)

        cl.addWidget(f)

        # Alerte stock
        cl.addWidget(self._section("Alertes stock"))
        af = self._frame()
        al = QVBoxLayout(af)
        alerte_row = QHBoxLayout()
        alerte_lbl = QLabel("Seuil alerte stock faible :")
        alerte_lbl.setFixedWidth(200)
        alerte_row.addWidget(alerte_lbl)
        self._spin_alerte = QSpinBox()
        self._spin_alerte.setRange(0, 9999)
        self._spin_alerte.setSuffix(" unités")
        self._spin_alerte.setFixedWidth(130)
        self._spin_alerte.setStyleSheet(f"padding:4px; border:1px solid {Theme.c('gray')}; border-radius:4px;")
        alerte_row.addWidget(self._spin_alerte)
        alerte_row.addStretch()
        al.addLayout(alerte_row)
        al.addWidget(QLabel("Les produits sous ce seuil s'affichent en rouge dans l'inventaire."))
        cl.addWidget(af)

        cl.addStretch()
        return page

    # ── Onglet Reçus & Cachets ────────────────────────────────────────────────

    def _onglet_recus(self):
        page = QWidget()
        cl = QVBoxLayout(page)
        cl.setContentsMargins(30, 24, 30, 24)
        cl.setSpacing(18)

        cl.addWidget(self._section("Cachets sur le reçu PDF"))
        desc = QLabel("Affiche un tampon diagonal (PAYÉ / À CRÉDIT) sur les reçus PDF générés.")
        desc.setStyleSheet(f"color:{Theme.c('text_secondary')}; font-size:10pt;")
        desc.setWordWrap(True)
        cl.addWidget(desc)

        f = self._frame()
        fl = QVBoxLayout(f)
        fl.setSpacing(10)
        self.chk_cachet_vente = self._chk_item("Afficher 'PAYÉ' sur les reçus de vente normale")
        self.chk_cachet_credit = self._chk_item("Afficher 'À CRÉDIT' sur les reçus de vente à crédit")
        self.chk_cachet_encaissement = self._chk_item("Afficher 'SOLDÉ' / 'À CRÉDIT' sur les remboursements ardoise")
        fl.addWidget(self.chk_cachet_vente)
        fl.addWidget(self.chk_cachet_credit)
        fl.addWidget(self.chk_cachet_encaissement)
        cl.addWidget(f)

        cl.addStretch()
        return page

    # ── Onglet Sécurité ───────────────────────────────────────────────────────

    def _onglet_securite(self):
        page = QWidget()
        cl = QVBoxLayout(page)
        cl.setContentsMargins(30, 24, 30, 24)
        cl.setSpacing(18)

        cl.addWidget(self._section("Déconnexion automatique par rôle"))
        desc = QLabel(
            "Déconnecte l'utilisateur après une période d'inactivité.\n"
            "Recommandé si plusieurs personnes partagent le même poste."
        )
        desc.setStyleSheet(f"color:{Theme.c('text_secondary')}; font-size:10pt;")
        desc.setWordWrap(True)
        cl.addWidget(desc)

        f = self._frame()
        fl = QVBoxLayout(f)
        fl.setSpacing(14)

        options = [("Jamais", "0"), ("15 min", "900"), ("30 min", "1800"),
                   ("1 heure", "3600"), ("2 heures", "7200")]

        for role_lbl, param_key, attr in [
            ("Caissier :",      "session_timeout_caissier",     '_combo_timeout_caissier'),
            ("Gestionnaire :",  "session_timeout_gestionnaire", '_combo_timeout_gestionnaire'),
            ("Patron :",        "session_timeout_patron",       '_combo_timeout_patron'),
        ]:
            row = QHBoxLayout()
            lbl = QLabel(role_lbl)
            lbl.setFixedWidth(150)
            lbl.setStyleSheet("font-size:10pt;")
            row.addWidget(lbl)
            combo = QComboBox()
            for lbl_opt, val in options:
                combo.addItem(lbl_opt, val)
            combo.currentIndexChanged.connect(self._marquer)
            row.addWidget(combo)
            row.addStretch()
            fl.addLayout(row)
            setattr(self, attr, combo)

        cl.addWidget(f)

        info = QLabel("Le patron est déconnecté par défaut sur 'Jamais'. Modifier uniquement si nécessaire.")
        info.setStyleSheet(f"color:{Theme.c('info')}; font-size:9pt; font-style:italic;")
        info.setWordWrap(True)
        cl.addWidget(info)

        cl.addStretch()
        return page

    def _chk_item(self, texte):
        cb = QCheckBox(texte)
        cb.setStyleSheet(f"""
            QCheckBox {{ color:{Theme.c('text')}; font-size:11pt; spacing:8px; }}
            QCheckBox::indicator {{ width:18px; height:18px; border-radius:4px;
                border:2px solid {Theme.c('input_border')}; background:{Theme.c('input_bg')}; }}
            QCheckBox::indicator:checked {{ background:{Theme.c('primary')}; border-color:{Theme.c('primary')}; }}
        """)
        cb.stateChanged.connect(self._marquer)
        return cb

    # ── Chargement ────────────────────────────────────────────────────────────

    def _charger(self):
        from config import BOUTIQUE_NOM, BOUTIQUE_ADRESSE, BOUTIQUE_TELEPHONE, BOUTIQUE_EMAIL
        self.input_nom.setText(db.get_parametre('boutique_nom', BOUTIQUE_NOM))
        self.input_adresse.setText(db.get_parametre('boutique_adresse', BOUTIQUE_ADRESSE))
        self.input_tel.setText(db.get_parametre('boutique_telephone', BOUTIQUE_TELEPHONE))
        self.input_email.setText(db.get_parametre('boutique_email', BOUTIQUE_EMAIL))
        self.input_ifu.setText(db.get_parametre('boutique_ifu', ''))
        self.input_rccm.setText(db.get_parametre('boutique_rccm', ''))
        self.input_facebook.setText(db.get_parametre('boutique_facebook', ''))
        self.input_instagram.setText(db.get_parametre('boutique_instagram', ''))
        self.input_whatsapp.setText(db.get_parametre('boutique_whatsapp', ''))
        self.input_message.setText(db.get_parametre('recu_message_pied', ''))
        self._actualiser_logo(db.get_parametre('boutique_logo_path', ''))

        # TVA
        tva_val = db.get_parametre('tva_taux_defaut', '18')
        for i in range(self._combo_tva.count()):
            if self._combo_tva.itemData(i) == tva_val:
                self._combo_tva.setCurrentIndex(i)
                break

        # Code-barres
        cb_val = db.get_parametre('barcode_mode_defaut', 'auto')
        for i in range(self._combo_cb.count()):
            if self._combo_cb.itemData(i) == cb_val:
                self._combo_cb.setCurrentIndex(i)
                break

        # Alerte stock
        try:
            self._spin_alerte.setValue(int(db.get_parametre('stock_alerte_seuil_defaut', '5')))
        except ValueError:
            self._spin_alerte.setValue(5)

        # Cachets
        self.chk_cachet_vente.setChecked(db.get_parametre('cachet_recu_vente', '1') == '1')
        self.chk_cachet_credit.setChecked(db.get_parametre('cachet_recu_credit', '1') == '1')
        self.chk_cachet_encaissement.setChecked(db.get_parametre('cachet_recu_encaissement', '1') == '1')

        # Session timeouts
        for param, attr in [
            ('session_timeout_caissier',     '_combo_timeout_caissier'),
            ('session_timeout_gestionnaire', '_combo_timeout_gestionnaire'),
            ('session_timeout_patron',       '_combo_timeout_patron'),
        ]:
            defaults = {'session_timeout_caissier': '1800', 'session_timeout_gestionnaire': '3600',
                        'session_timeout_patron': '0'}
            val = db.get_parametre(param, defaults[param])
            combo = getattr(self, attr)
            for i in range(combo.count()):
                if combo.itemData(i) == val:
                    combo.setCurrentIndex(i)
                    break

    # ── Enregistrement ────────────────────────────────────────────────────────

    def _enregistrer(self):
        nom = self.input_nom.text().strip()
        if nom:
            db.set_parametre('boutique_nom', nom)
        db.set_parametre('boutique_adresse',   self.input_adresse.text().strip())
        db.set_parametre('boutique_telephone', self.input_tel.text().strip())
        db.set_parametre('boutique_email',     self.input_email.text().strip())
        db.set_parametre('boutique_ifu',       self.input_ifu.text().strip())
        db.set_parametre('boutique_rccm',      self.input_rccm.text().strip())
        db.set_parametre('boutique_facebook',  self.input_facebook.text().strip())
        db.set_parametre('boutique_instagram', self.input_instagram.text().strip())
        db.set_parametre('boutique_whatsapp',  self.input_whatsapp.text().strip())
        db.set_parametre('recu_message_pied',  self.input_message.text().strip())

        db.set_parametre('tva_taux_defaut', self._combo_tva.currentData())
        db.set_parametre('barcode_mode_defaut', self._combo_cb.currentData())
        db.set_parametre('stock_alerte_seuil_defaut', str(self._spin_alerte.value()))

        db.set_parametre('cachet_recu_vente',        '1' if self.chk_cachet_vente.isChecked()        else '0')
        db.set_parametre('cachet_recu_credit',       '1' if self.chk_cachet_credit.isChecked()       else '0')
        db.set_parametre('cachet_recu_encaissement', '1' if self.chk_cachet_encaissement.isChecked() else '0')

        db.set_parametre('session_timeout_caissier',     self._combo_timeout_caissier.currentData())
        db.set_parametre('session_timeout_gestionnaire', self._combo_timeout_gestionnaire.currentData())
        db.set_parametre('session_timeout_patron',       self._combo_timeout_patron.currentData())
        # Rétrocompatibilité : session_timeout = valeur caissier
        db.set_parametre('session_timeout', self._combo_timeout_caissier.currentData())

        self._modifie = False
        self._btn_save.setStyleSheet(self._style_neutre())
        information(self, "Enregistré", "Paramètres boutique sauvegardés.")
        self.accept()

    def reject(self):
        if self._modifie:
            from PySide6.QtWidgets import QMessageBox
            rep = QMessageBox.question(
                self, "Modifications non sauvegardées",
                "Voulez-vous enregistrer avant de fermer ?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save
            )
            if rep == QMessageBox.Save:
                self._enregistrer()
                return
            elif rep == QMessageBox.Cancel:
                return
        super().reject()

    def closeEvent(self, event):
        if self._modifie:
            from PySide6.QtWidgets import QMessageBox
            rep = QMessageBox.question(
                self, "Modifications non sauvegardées",
                "Voulez-vous enregistrer avant de fermer ?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save
            )
            if rep == QMessageBox.Save:
                self._enregistrer()
                event.accept()
            elif rep == QMessageBox.Discard:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    # ── Logo ──────────────────────────────────────────────────────────────────

    def _choisir_logo(self):
        chemin, _ = QFileDialog.getOpenFileName(
            self, "Choisir un logo", "", "Images (*.png *.jpg *.jpeg *.bmp *.webp)")
        if not chemin:
            return
        from config import IMAGES_DIR
        dest = os.path.join(IMAGES_DIR, 'logo_boutique.png')
        try:
            px = QPixmap(chemin)
            if px.isNull():
                erreur(self, "Erreur", "Impossible de lire cette image.")
                return
            px.save(dest, 'PNG')
            db.set_parametre('boutique_logo_path', dest)
            self._actualiser_logo(dest)
            information(self, "Logo enregistré", "Logo enregistré avec succès.")
        except Exception as e:
            erreur(self, "Erreur", f"Impossible d'enregistrer le logo : {e}")

    def _supprimer_logo(self):
        db.set_parametre('boutique_logo_path', '')
        self._actualiser_logo('')
        information(self, "Logo supprimé", "Logo supprimé.")

    def _actualiser_logo(self, path):
        if path and os.path.exists(path):
            px = QPixmap(path).scaled(76, 76, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self._logo_preview.setPixmap(px)
            self._logo_preview.setText('')
        else:
            self._logo_preview.clear()
            self._logo_preview.setText("Aucun\nlogo")
