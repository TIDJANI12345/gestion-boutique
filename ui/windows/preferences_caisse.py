"""
Fenêtre Paramètres Caisse - Configuration point de vente
"""
import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QPushButton, QRadioButton, QButtonGroup, QCheckBox, QScrollArea, QLineEdit,
    QComboBox, QFileDialog, QColorDialog
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

from ui.theme import Theme
from ui.components.dialogs import information, erreur
from database import db


class PreferencesCaisseWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Paramètres Caisse")
        self.setMinimumSize(650, 550)

        self._setup_ui()
        self._charger_parametres()

        # Centrer la fenêtre sur le parent
        if self.parent():
            self.adjustSize()
            parent_rect = self.parent().frameGeometry()
            center = parent_rect.center()
            dlg_rect = self.frameGeometry()
            dlg_rect.moveCenter(center)
            self.move(dlg_rect.topLeft())

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QFrame()
        header.setStyleSheet(f"background-color: {Theme.c('primary')};")
        header.setFixedHeight(70)

        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(30, 0, 30, 0)

        title = QLabel("⚙️ Paramètres Caisse")
        title.setStyleSheet("color: white; font-size: 18pt; font-weight: bold;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        layout.addWidget(header)

        # Content
        content = QFrame()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(20)

        # === MODE SCAN ===
        mode_label = QLabel("Mode de scan")
        mode_label.setStyleSheet(f"font-size: 14pt; font-weight: bold; color: {Theme.c('dark')};")
        content_layout.addWidget(mode_label)

        desc_label = QLabel(
            "Choisissez comment les produits sont ajoutés au panier lors du scan."
        )
        desc_label.setStyleSheet(f"color: {Theme.c('gray')}; font-size: 10pt;")
        desc_label.setWordWrap(True)
        content_layout.addWidget(desc_label)

        # Radio buttons
        mode_frame = QFrame()
        mode_frame.setStyleSheet(f"background-color: {Theme.c('light')}; border-radius: 8px; padding: 20px;")
        mode_layout = QVBoxLayout(mode_frame)
        mode_layout.setSpacing(15)

        self.radio_group = QButtonGroup(self)

        # Mode AUTO
        self.radio_auto = QRadioButton("🏪 Mode AUTOMATIQUE (supermarché)")
        self.radio_auto.setStyleSheet("font-size: 11pt; font-weight: bold;")
        self.radio_group.addButton(self.radio_auto, 1)
        mode_layout.addWidget(self.radio_auto)

        auto_desc = QLabel(
            "• Ajout direct avec quantité 1 au scan\n"
            "• Pas de popup de confirmation\n"
            "• Re-scan du même produit → quantité s'incrémente\n"
            "• Idéal pour flux rapide comme en supermarché"
        )
        auto_desc.setStyleSheet(f"color: {Theme.c('gray')}; font-size: 9pt; margin-left: 25px;")
        mode_layout.addWidget(auto_desc)

        mode_layout.addSpacing(10)

        # Mode MANUEL
        self.radio_manuel = QRadioButton("✍️ Mode MANUEL (avec quantité)")
        self.radio_manuel.setStyleSheet("font-size: 11pt; font-weight: bold;")
        self.radio_group.addButton(self.radio_manuel, 0)
        mode_layout.addWidget(self.radio_manuel)

        manuel_desc = QLabel(
            "• Demande la quantité à chaque scan\n"
            "• Popup de confirmation systématique\n"
            "• Plus sûr pour éviter les erreurs\n"
            "• Idéal pour produits avec quantités variables"
        )
        manuel_desc.setStyleSheet(f"color: {Theme.c('gray')}; font-size: 9pt; margin-left: 25px;")
        mode_layout.addWidget(manuel_desc)

        content_layout.addWidget(mode_frame)

        # Info F9
        info_f9 = QLabel("💡 Astuce : Appuyez sur F9 dans la fenêtre Ventes pour basculer rapidement")
        info_f9.setStyleSheet(f"color: {Theme.c('info')}; font-size: 9pt; font-style: italic;")
        content_layout.addWidget(info_f9)

        content_layout.addSpacing(20)

        # === SON DE SCAN ===
        son_label = QLabel("Son de confirmation")
        son_label.setStyleSheet(f"font-size: 14pt; font-weight: bold; color: {Theme.c('dark')};")
        content_layout.addWidget(son_label)

        son_desc = QLabel(
            "Jouer un son à chaque produit scanné et ajouté au panier."
        )
        son_desc.setStyleSheet(f"color: {Theme.c('gray')}; font-size: 10pt;")
        son_desc.setWordWrap(True)
        content_layout.addWidget(son_desc)

        # Checkbox son
        son_frame = QFrame()
        son_frame.setStyleSheet(f"background-color: {Theme.c('light')}; border-radius: 8px; padding: 20px;")
        son_layout = QVBoxLayout(son_frame)
        son_layout.setSpacing(10)

        self.checkbox_son = QCheckBox("🔊 Activer le son de scan")
        self.checkbox_son.setStyleSheet("font-size: 11pt; font-weight: bold;")
        son_layout.addWidget(self.checkbox_son)

        son_info = QLabel(
            "Un bip court sera joué à chaque ajout au panier.\n"
            "Utile pour confirmer que le scan a bien été pris en compte."
        )
        son_info.setStyleSheet(f"color: {Theme.c('gray')}; font-size: 9pt; margin-left: 25px;")
        son_layout.addWidget(son_info)

        content_layout.addWidget(son_frame)

        content_layout.addSpacing(20)

        # === CAMÉRA ===
        camera_label = QLabel("Caméra de scan")
        camera_label.setStyleSheet(f"font-size: 14pt; font-weight: bold; color: {Theme.c('dark')};")
        content_layout.addWidget(camera_label)

        camera_desc = QLabel(
            "Configuration de la caméra intégrée pour scanner les codes-barres."
        )
        camera_desc.setStyleSheet(f"color: {Theme.c('gray')}; font-size: 10pt;")
        camera_desc.setWordWrap(True)
        content_layout.addWidget(camera_desc)

        camera_frame = QFrame()
        camera_frame.setStyleSheet(f"background-color: {Theme.c('light')}; border-radius: 8px; padding: 20px;")
        camera_layout = QVBoxLayout(camera_frame)
        camera_layout.setSpacing(10)

        self.checkbox_camera_auto = QCheckBox("📷 Activer la caméra automatiquement")
        self.checkbox_camera_auto.setStyleSheet("font-size: 11pt; font-weight: bold;")
        camera_layout.addWidget(self.checkbox_camera_auto)

        camera_info = QLabel(
            "Si activé, la caméra démarre automatiquement à l'ouverture de la fenêtre Ventes.\n"
            "Sinon, vous devez cliquer sur le bouton 'Afficher caméra' pour l'activer."
        )
        camera_info.setStyleSheet(f"color: {Theme.c('gray')}; font-size: 9pt; margin-left: 25px;")
        camera_layout.addWidget(camera_info)

        camera_layout.addSpacing(15)

        # Source caméra
        source_label = QLabel("📹 Source caméra")
        source_label.setStyleSheet("font-size: 10pt; font-weight: bold;")
        camera_layout.addWidget(source_label)

        source_layout = QHBoxLayout()
        self.input_camera_source = QLineEdit()
        self.input_camera_source.setPlaceholderText("0 (webcam PC) ou http://IP:PORT/video (téléphone)")
        self.input_camera_source.setStyleSheet(f"""
            QLineEdit {{
                padding: 8px;
                border: 1px solid {Theme.c('gray')};
                border-radius: 4px;
                font-size: 10pt;
            }}
        """)
        source_layout.addWidget(self.input_camera_source)

        test_btn = QPushButton("Tester")
        test_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.c('info')};
                color: white;
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #0284C7;
            }}
        """)
        test_btn.clicked.connect(self._tester_camera)
        source_layout.addWidget(test_btn)

        camera_layout.addLayout(source_layout)

        source_info = QLabel(
            "Entrez 0 pour la webcam par défaut, 1 pour une 2ème webcam USB.\n"
            "Pour utiliser votre téléphone : installez DroidCam/IP Webcam et entrez l'URL affichée.\n"
            "Exemple : http://192.168.1.100:8080/video"
        )
        source_info.setStyleSheet(f"color: {Theme.c('gray')}; font-size: 9pt; margin-left: 0px;")
        camera_layout.addWidget(source_info)

        content_layout.addWidget(camera_frame)

        content_layout.addSpacing(20)

        # === IMPRESSION THERMIQUE ===
        imp_label = QLabel("Impression thermique")
        imp_label.setStyleSheet(f"font-size: 14pt; font-weight: bold; color: {Theme.c('dark')};")
        content_layout.addWidget(imp_label)

        imp_frame = QFrame()
        imp_frame.setStyleSheet(f"background-color: {Theme.c('light')}; border-radius: 8px; padding: 10px;")
        imp_layout = QVBoxLayout(imp_frame)
        imp_layout.setSpacing(8)

        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("Mode :"))
        self.combo_imp_mode = QComboBox()
        self.combo_imp_mode.addItems(["USB", "Réseau (IP)", "Série (COM)"])
        mode_row.addWidget(self.combo_imp_mode, 1)
        imp_layout.addLayout(mode_row)

        btn_test_imp = QPushButton("Imprimer ticket de test")
        btn_test_imp.setProperty("class", "secondary")
        btn_test_imp.setCursor(Qt.PointingHandCursor)
        btn_test_imp.clicked.connect(self._tester_impression)
        imp_layout.addWidget(btn_test_imp)

        content_layout.addWidget(imp_frame)

        content_layout.addSpacing(20)

        # === INFORMATIONS BOUTIQUE ===
        boutique_label = QLabel("Informations boutique")
        boutique_label.setStyleSheet(f"font-size: 14pt; font-weight: bold; color: {Theme.c('dark')};")
        content_layout.addWidget(boutique_label)

        boutique_desc = QLabel("Ces informations apparaissent sur les reçus PDF et tickets thermiques.")
        boutique_desc.setStyleSheet(f"color: {Theme.c('gray')}; font-size: 10pt;")
        boutique_desc.setWordWrap(True)
        content_layout.addWidget(boutique_desc)

        boutique_frame = QFrame()
        boutique_frame.setStyleSheet(f"background-color: {Theme.c('light')}; border-radius: 8px; padding: 20px;")
        boutique_layout = QVBoxLayout(boutique_frame)
        boutique_layout.setSpacing(10)

        def _champ(label_txt, placeholder):
            row = QHBoxLayout()
            lbl = QLabel(label_txt)
            lbl.setFixedWidth(100)
            lbl.setStyleSheet("font-size: 10pt;")
            row.addWidget(lbl)
            entry = QLineEdit()
            entry.setPlaceholderText(placeholder)
            entry.setStyleSheet(f"padding: 6px; border: 1px solid {Theme.c('gray')}; border-radius: 4px;")
            row.addWidget(entry)
            boutique_layout.addLayout(row)
            return entry

        self.input_nom_boutique     = _champ("Nom :",      "Ma Boutique")
        self.input_adresse_boutique = _champ("Adresse :",  "Cotonou, Bénin")
        self.input_tel_boutique     = _champ("Téléphone :", "+229 XX XX XX XX")
        self.input_email_boutique   = _champ("Email :",    "contact@maboutique.bj")
        self.input_ifu_boutique     = _champ("IFU :",      "Numéro IFU (ex: 1234567890123)")
        self.input_rccm_boutique    = _champ("RCCM :",     "Numéro RCCM (ex: RB/ABC/24 B 12345)")

        # Réseaux sociaux
        boutique_layout.addSpacing(6)
        rs_title = QLabel("Réseaux sociaux (optionnel) :")
        rs_title.setStyleSheet("font-size: 10pt; font-weight: bold;")
        boutique_layout.addWidget(rs_title)

        self.input_facebook  = _champ("Facebook :",  "fb.com/maboutique ou @MaBoutique")
        self.input_instagram = _champ("Instagram :", "@maboutique")
        self.input_whatsapp  = _champ("WhatsApp :",  "+229 XX XX XX XX")

        boutique_layout.addSpacing(4)

        # Message pied de page
        msg_label = QLabel("Message pied de page :")
        msg_label.setStyleSheet("font-size: 10pt;")
        boutique_layout.addWidget(msg_label)
        self.input_message_pied = QLineEdit()
        self.input_message_pied.setPlaceholderText("Ex: Retour accepté sous 7 jours avec ticket de caisse")
        self.input_message_pied.setStyleSheet(f"padding: 6px; border: 1px solid {Theme.c('gray')}; border-radius: 4px;")
        boutique_layout.addWidget(self.input_message_pied)

        # Logo boutique
        boutique_layout.addSpacing(10)
        logo_title = QLabel("Logo boutique :")
        logo_title.setStyleSheet("font-size: 10pt;")
        boutique_layout.addWidget(logo_title)

        logo_row = QHBoxLayout()

        self._label_logo_preview = QLabel("Aucun\nlogo")
        self._label_logo_preview.setFixedSize(80, 80)
        self._label_logo_preview.setAlignment(Qt.AlignCenter)
        self._label_logo_preview.setStyleSheet(
            f"border: 1px dashed {Theme.c('gray')}; border-radius: 4px; "
            f"background: white; color: {Theme.c('gray')}; font-size: 9pt;"
        )
        logo_row.addWidget(self._label_logo_preview)

        logo_btns = QVBoxLayout()
        btn_choisir_logo = QPushButton("Choisir un logo…")
        btn_choisir_logo.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.c('info')};
                color: white; padding: 8px 12px;
                border-radius: 4px; font-weight: bold;
            }}
            QPushButton:hover {{ background-color: #0284C7; }}
        """)
        btn_choisir_logo.clicked.connect(self._choisir_logo)
        logo_btns.addWidget(btn_choisir_logo)

        self._btn_suppr_logo = QPushButton("Supprimer le logo")
        self._btn_suppr_logo.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.c('danger')};
                color: white; padding: 8px 12px;
                border-radius: 4px;
            }}
            QPushButton:hover {{ background-color: #DC2626; }}
        """)
        self._btn_suppr_logo.clicked.connect(self._supprimer_logo)
        logo_btns.addWidget(self._btn_suppr_logo)
        logo_btns.addStretch()

        logo_row.addLayout(logo_btns)
        logo_row.addStretch()
        boutique_layout.addLayout(logo_row)

        logo_hint = QLabel("PNG ou JPG recommandé · Sera affiché sur les reçus PDF et en filigrane.")
        logo_hint.setStyleSheet(f"color: {Theme.c('gray')}; font-size: 9pt;")
        boutique_layout.addWidget(logo_hint)

        content_layout.addWidget(boutique_frame)

        content_layout.addSpacing(20)

        # === APPARENCE ===
        app_label = QLabel("Apparence")
        app_label.setStyleSheet(f"font-size: 14pt; font-weight: bold; color: {Theme.c('dark')};")
        content_layout.addWidget(app_label)

        app_desc = QLabel("Personnalisez la couleur principale de l'interface.")
        app_desc.setStyleSheet(f"color: {Theme.c('gray')}; font-size: 10pt;")
        content_layout.addWidget(app_desc)

        app_frame = QFrame()
        app_frame.setStyleSheet(f"background-color: {Theme.c('light')}; border-radius: 8px; padding: 20px;")
        app_frame_layout = QHBoxLayout(app_frame)
        app_frame_layout.setSpacing(12)

        couleur_lbl = QLabel("Couleur principale :")
        couleur_lbl.setStyleSheet("font-size: 10pt;")
        app_frame_layout.addWidget(couleur_lbl)

        self._btn_couleur_primaire = QPushButton()
        self._btn_couleur_primaire.setFixedSize(40, 40)
        self._btn_couleur_primaire.setToolTip("Cliquer pour changer la couleur")
        self._btn_couleur_primaire.setCursor(Qt.PointingHandCursor)
        self._btn_couleur_primaire.clicked.connect(self._choisir_couleur_primaire)
        app_frame_layout.addWidget(self._btn_couleur_primaire)

        self._lbl_couleur_hex = QLabel()
        self._lbl_couleur_hex.setStyleSheet(f"color: {Theme.c('gray')}; font-size: 10pt; font-family: Consolas;")
        app_frame_layout.addWidget(self._lbl_couleur_hex)

        app_frame_layout.addStretch()

        btn_reset_couleur = QPushButton("Réinitialiser")
        btn_reset_couleur.setProperty("class", "secondary")
        btn_reset_couleur.setCursor(Qt.PointingHandCursor)
        btn_reset_couleur.clicked.connect(self._reinitialiser_couleur)
        app_frame_layout.addWidget(btn_reset_couleur)

        content_layout.addWidget(app_frame)

        content_layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        close_btn = QPushButton("Fermer")
        close_btn.setObjectName("secondaryButton")
        close_btn.clicked.connect(self.reject)
        btn_layout.addWidget(close_btn)

        save_btn = QPushButton("Enregistrer")
        save_btn.setObjectName("primaryButton")
        save_btn.setStyleSheet(f"""
            QPushButton#primaryButton {{
                background-color: {Theme.c('success')};
                padding: 12px 30px;
                font-size: 11pt;
                font-weight: bold;
            }}
        """)
        save_btn.clicked.connect(self._enregistrer)
        btn_layout.addWidget(save_btn)

        content_layout.addLayout(btn_layout)

        # Envelopper content dans QScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        scroll.setWidget(content)
        layout.addWidget(scroll)

    def _charger_parametres(self):
        """Charger les paramètres actuels"""
        # Mode de scan
        mode_auto = db.get_parametre('mode_scan_auto', '1') == '1'
        if mode_auto:
            self.radio_auto.setChecked(True)
        else:
            self.radio_manuel.setChecked(True)

        # Son de scan
        son_actif = db.get_parametre('son_scan_actif', '1') == '1'
        self.checkbox_son.setChecked(son_actif)

        # Caméra auto
        camera_auto = db.get_parametre('camera_auto_start', '0') == '1'
        self.checkbox_camera_auto.setChecked(camera_auto)

        # Source caméra
        camera_source = db.get_parametre('camera_source', '0')
        self.input_camera_source.setText(camera_source)

        # Mode imprimante
        mode_imp = db.get_parametre('imprimante_mode', 'usb')
        mode_map = {'usb': 0, 'reseau': 1, 'serie': 2}
        self.combo_imp_mode.setCurrentIndex(mode_map.get(mode_imp, 0))

        # Infos boutique
        from config import BOUTIQUE_NOM, BOUTIQUE_ADRESSE, BOUTIQUE_TELEPHONE, BOUTIQUE_EMAIL
        self.input_nom_boutique.setText(db.get_parametre('boutique_nom', BOUTIQUE_NOM))
        self.input_adresse_boutique.setText(db.get_parametre('boutique_adresse', BOUTIQUE_ADRESSE))
        self.input_tel_boutique.setText(db.get_parametre('boutique_telephone', BOUTIQUE_TELEPHONE))
        self.input_email_boutique.setText(db.get_parametre('boutique_email', BOUTIQUE_EMAIL))
        self.input_ifu_boutique.setText(db.get_parametre('boutique_ifu', ''))
        self.input_rccm_boutique.setText(db.get_parametre('boutique_rccm', ''))
        self.input_facebook.setText(db.get_parametre('boutique_facebook', ''))
        self.input_instagram.setText(db.get_parametre('boutique_instagram', ''))
        self.input_whatsapp.setText(db.get_parametre('boutique_whatsapp', ''))
        self.input_message_pied.setText(db.get_parametre('recu_message_pied', ''))
        self._actualiser_apercu_logo(db.get_parametre('boutique_logo_path', ''))

        # Couleur primaire
        couleur = db.get_parametre('theme_couleur_primaire', Theme.c('primary'))
        self._actualiser_btn_couleur(couleur)

    def _enregistrer(self):
        """Sauvegarder les paramètres"""
        # Mode de scan
        mode_auto = '1' if self.radio_auto.isChecked() else '0'
        db.set_parametre('mode_scan_auto', mode_auto)

        # Son de scan
        son_actif = '1' if self.checkbox_son.isChecked() else '0'
        db.set_parametre('son_scan_actif', son_actif)
        db.set_parametre('son_scan_type', 'beep')

        # Caméra auto
        camera_auto = '1' if self.checkbox_camera_auto.isChecked() else '0'
        db.set_parametre('camera_auto_start', camera_auto)

        # Source caméra
        camera_source = self.input_camera_source.text().strip() or '0'
        db.set_parametre('camera_source', camera_source)

        # Mode imprimante
        mode_imp_map = ['usb', 'reseau', 'serie']
        db.set_parametre('imprimante_mode', mode_imp_map[self.combo_imp_mode.currentIndex()])

        # Infos boutique
        nom = self.input_nom_boutique.text().strip()
        adresse = self.input_adresse_boutique.text().strip()
        tel = self.input_tel_boutique.text().strip()
        email = self.input_email_boutique.text().strip()
        if nom:
            db.set_parametre('boutique_nom', nom)
        if adresse:
            db.set_parametre('boutique_adresse', adresse)
        if tel:
            db.set_parametre('boutique_telephone', tel)
        if email:
            db.set_parametre('boutique_email', email)
        db.set_parametre('boutique_ifu', self.input_ifu_boutique.text().strip())
        db.set_parametre('boutique_rccm', self.input_rccm_boutique.text().strip())
        db.set_parametre('boutique_facebook', self.input_facebook.text().strip())
        db.set_parametre('boutique_instagram', self.input_instagram.text().strip())
        db.set_parametre('boutique_whatsapp', self.input_whatsapp.text().strip())
        db.set_parametre('recu_message_pied', self.input_message_pied.text().strip())

        information(self, "Paramètres sauvegardés", "Paramètres enregistrés avec succès.")
        self.accept()

    def _choisir_logo(self):
        chemin, _ = QFileDialog.getOpenFileName(
            self, "Choisir un logo", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif *.webp)"
        )
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
            self._actualiser_apercu_logo(dest)
            information(self, "Logo enregistré", "Le logo a été enregistré avec succès.")
        except Exception as e:
            erreur(self, "Erreur", f"Impossible d'enregistrer le logo : {e}")

    def _supprimer_logo(self):
        db.set_parametre('boutique_logo_path', '')
        self._actualiser_apercu_logo('')
        information(self, "Logo supprimé", "Le logo a été supprimé.")

    def _actualiser_apercu_logo(self, logo_path):
        if logo_path and os.path.exists(logo_path):
            px = QPixmap(logo_path).scaled(76, 76, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self._label_logo_preview.setPixmap(px)
            self._label_logo_preview.setText('')
        else:
            self._label_logo_preview.clear()
            self._label_logo_preview.setText("Aucun\nlogo")

    def _actualiser_btn_couleur(self, hex_color: str):
        from PySide6.QtGui import QColor
        if not QColor(hex_color).isValid():
            hex_color = Theme.c('primary')
        self._btn_couleur_primaire.setStyleSheet(
            f"QPushButton {{ background-color: {hex_color}; border-radius: 6px; border: 2px solid rgba(0,0,0,0.2); }}"
            f"QPushButton:hover {{ border: 2px solid rgba(0,0,0,0.4); }}"
        )
        self._lbl_couleur_hex.setText(hex_color.upper())

    def _choisir_couleur_primaire(self):
        from PySide6.QtGui import QColor
        couleur_actuelle = db.get_parametre('theme_couleur_primaire', Theme.c('primary'))
        couleur = QColorDialog.getColor(QColor(couleur_actuelle), self, "Choisir la couleur principale")
        if couleur.isValid():
            hex_color = couleur.name()
            Theme.appliquer_couleur_primaire(hex_color, sauvegarder=True)
            self._actualiser_btn_couleur(hex_color)

    def _reinitialiser_couleur(self):
        hex_default = '#3B82F6'
        Theme.appliquer_couleur_primaire(hex_default, sauvegarder=True)
        self._actualiser_btn_couleur(hex_default)

    def _tester_impression(self):
        """Tester l'impression thermique"""
        from modules.imprimante import ImprimanteThermique

        if not ImprimanteThermique.est_disponible():
            erreur(self, "Module manquant", "python-escpos n'est pas installé.\nInstallez-le avec : pip install python-escpos")
            return

        mode_imp_map = ['usb', 'reseau', 'serie']
        db.set_parametre('imprimante_mode', mode_imp_map[self.combo_imp_mode.currentIndex()])

        ok, msg = ImprimanteThermique.imprimer_test()
        if ok:
            information(self, "Test réussi", msg)
        else:
            erreur(self, "Échec du test", msg)

    def _tester_camera(self):
        """Tester la connexion à la caméra"""
        try:
            import cv2
        except ImportError:
            erreur(self, "Erreur", "opencv-python n'est pas installé.\nInstallez-le avec : pip install opencv-python")
            return

        source = self.input_camera_source.text().strip() or '0'

        # Convertir en int si possible
        try:
            source = int(source)
        except ValueError:
            pass  # C'est une URL

        cap = cv2.VideoCapture(source)
        if cap.isOpened():
            ret, frame = cap.read()
            cap.release()
            if ret:
                information(self, "Test réussi", f"✓ Caméra connectée avec succès !\nSource : {source}")
            else:
                erreur(self, "Erreur", f"Caméra trouvée mais impossible de lire les images.\nVérifiez que la caméra n'est pas utilisée par une autre application.")
        else:
            erreur(self, "Erreur de connexion",
                f"Impossible de se connecter à la caméra.\n\n"
                f"Source testée : {source}\n\n"
                f"Vérifications :\n"
                f"• Pour webcam PC : essayez 0, 1 ou 2\n"
                f"• Pour téléphone : vérifiez l'URL (http://IP:PORT/video)\n"
                f"• Assurez-vous que l'app mobile est lancée\n"
                f"• Vérifiez que PC et téléphone sont sur le même WiFi"
            )
