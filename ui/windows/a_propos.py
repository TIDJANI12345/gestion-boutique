"""
Fenetre A propos de l'application
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

from ui.theme import Theme
from config import APP_NAME, APP_VERSION
from modules.licence import GestionLicence
import os


class AProposWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("À propos")
        self.setFixedSize(500, 650)
        self.setStyleSheet(Theme.stylesheet())

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QFrame()
        header.setStyleSheet(f"background-color: {Theme.c('primary')};")
        header.setFixedHeight(180)
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setAlignment(Qt.AlignCenter)

        # Logo (if exists)
        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logo.png')
        if os.path.exists(logo_path):
            logo_label = QLabel()
            pixmap = QPixmap(logo_path)
            if not pixmap.isNull():
                logo_label.setPixmap(pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                logo_label.setAlignment(Qt.AlignCenter)
                header_layout.addWidget(logo_label)
                header_layout.addSpacing(15)

        app_label = QLabel(APP_NAME.upper())
        app_label.setStyleSheet("color: white; font-size: 20pt; font-weight: bold;")
        app_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(app_label)

        layout.addWidget(header)

        # Content
        content = QFrame()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(40, 30, 40, 30)
        content_layout.setSpacing(10)

        # Version
        version_label = QLabel(f"Version {APP_VERSION}")
        version_label.setStyleSheet(f"font-size: 14pt; font-weight: bold; color: {Theme.c('dark')};")
        version_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(version_label)

        # Description
        desc_label = QLabel("Logiciel de gestion pour boutiques\nau Bénin et en Afrique")
        desc_label.setStyleSheet(f"font-size: 11pt; color: {Theme.c('gray')};")
        desc_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(desc_label)

        content_layout.addSpacing(15)

        # Separator
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.HLine)
        sep1.setStyleSheet(f"background-color: {Theme.c('light')};")
        sep1.setFixedHeight(1)
        content_layout.addWidget(sep1)

        content_layout.addSpacing(10)

        # Contact info
        infos = [
            ("📧 Email", "contact@votreentreprise.bj"),
            ("📱 Téléphone", "+229 XX XX XX XX"),
            ("🌐 Site web", "www.gestionboutique.bj"),
            ("💼 Support", "support@votreentreprise.bj"),
        ]

        for label_text, valeur in infos:
            row = QHBoxLayout()
            label = QLabel(label_text)
            label.setStyleSheet(f"font-size: 10pt; font-weight: bold; color: {Theme.c('dark')};")
            row.addWidget(label)

            value = QLabel(valeur)
            value.setStyleSheet(f"font-size: 10pt; color: {Theme.c('primary')};")
            row.addStretch()
            row.addWidget(value)

            content_layout.addLayout(row)

        content_layout.addSpacing(15)

        # Separator
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet(f"background-color: {Theme.c('light')};")
        sep2.setFixedHeight(1)
        content_layout.addWidget(sep2)

        content_layout.addSpacing(10)

        # License info
        manager = GestionLicence()
        licence_info = manager.obtenir_info_locale()

        if licence_info:
            licence_frame = QFrame()
            licence_frame.setStyleSheet(f"background-color: {Theme.c('light')}; border-radius: 4px;")
            licence_layout = QVBoxLayout(licence_frame)
            licence_layout.setContentsMargins(15, 15, 15, 15)

            lic_title = QLabel("🔑 Informations de licence")
            lic_title.setStyleSheet(f"font-size: 11pt; font-weight: bold; color: {Theme.c('dark')};")
            licence_layout.addWidget(lic_title)

            licence_layout.addSpacing(10)

            lic_key = QLabel(f"Clé: {licence_info.get('cle_licence', 'N/A')}")
            lic_key.setStyleSheet(f"font-size: 9pt; color: {Theme.c('gray')};")
            licence_layout.addWidget(lic_key)

            lic_type = QLabel(f"Type: {licence_info.get('type_licence', 'N/A')}")
            lic_type.setStyleSheet(f"font-size: 9pt; color: {Theme.c('gray')};")
            licence_layout.addWidget(lic_type)

            lic_exp = QLabel(f"Expire le: {licence_info.get('date_expiration', 'N/A')}")
            lic_exp.setStyleSheet(f"font-size: 9pt; color: {Theme.c('gray')};")
            licence_layout.addWidget(lic_exp)

            content_layout.addWidget(licence_frame)

        content_layout.addStretch()

        # Copyright
        copyright_label = QLabel("© 2026 - Tous droits réservés")
        copyright_label.setStyleSheet(f"font-size: 9pt; color: {Theme.c('gray')};")
        copyright_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(copyright_label)

        content_layout.addSpacing(10)

        # Close button
        close_btn = QPushButton("Fermer")
        close_btn.setObjectName("primaryButton")
        close_btn.clicked.connect(self.accept)
        content_layout.addWidget(close_btn)

        layout.addWidget(content)
