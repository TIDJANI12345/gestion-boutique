"""
Fenêtre Paramètres Caisse - Configuration point de vente
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QPushButton, QRadioButton, QButtonGroup, QCheckBox, QScrollArea, QLineEdit
)
from PySide6.QtCore import Qt

from ui.theme import Theme
from ui.components.dialogs import information, erreur
from database import db


class PreferencesCaisseWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Paramètres Caisse")
        self.setMinimumSize(650, 550)
        self.setStyleSheet(Theme.stylesheet())

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

        mode_txt = "AUTOMATIQUE" if mode_auto == '1' else "MANUEL"
        son_txt = "activé" if son_actif == '1' else "désactivé"
        camera_txt = "activée" if camera_auto == '1' else "désactivée"
        information(
            self, "Paramètres sauvegardés",
            f"Mode de scan : {mode_txt}\n"
            f"Son de scan : {son_txt}\n"
            f"Caméra auto : {camera_txt}\n"
            f"Source caméra : {camera_source}"
        )
        self.accept()

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
