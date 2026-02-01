"""
Configuration de la synchronisation cloud
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton
)
from PySide6.QtCore import Qt, QTimer

from ui.theme import Theme
from ui.components.dialogs import information, avertissement, erreur
from modules.synchronisation import Synchronisation
from config import SYNC_SERVER_URL


class ConfigSyncWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Synchronisation Cloud")
        self.setFixedSize(600, 520)
        self.setStyleSheet(Theme.stylesheet())

        self.sync = Synchronisation()
        self._setup_ui()

        # Initial detection
        QTimer.singleShot(100, self._detecter_mode)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QFrame()
        header.setObjectName("headerFrame")
        header.setStyleSheet(f"#headerFrame {{ background-color: {Theme.c('info')}; }}")
        header.setFixedHeight(80)

        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Synchronisation Cloud")
        title.setStyleSheet("color: white; font-size: 18pt; font-weight: bold;")
        title.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title)

        layout.addWidget(header)

        # Content
        content = QFrame()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(40, 30, 40, 30)
        content_layout.setSpacing(10)

        # Connection status
        status_label = QLabel("Statut de connexion :")
        status_label.setStyleSheet("font-size: 11pt; font-weight: bold;")
        content_layout.addWidget(status_label)

        self.mode_label = QLabel("Detection en cours...")
        self.mode_label.setStyleSheet(f"font-size: 14pt; font-weight: bold; color: {Theme.c('gray')};")
        content_layout.addWidget(self.mode_label)

        content_layout.addSpacing(10)

        # Last sync
        last_sync_label = QLabel("Derniere synchronisation :")
        last_sync_label.setStyleSheet("font-size: 11pt; font-weight: bold;")
        content_layout.addWidget(last_sync_label)

        dernier_sync = self.sync._get_dernier_sync()
        if dernier_sync:
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(dernier_sync)
                texte_sync = dt.strftime("%d/%m/%Y %H:%M:%S")
            except Exception:
                texte_sync = dernier_sync
        else:
            texte_sync = "Jamais"

        self.last_sync_label = QLabel(texte_sync)
        self.last_sync_label.setStyleSheet(f"font-size: 12pt; color: {Theme.c('dark')};")
        content_layout.addWidget(self.last_sync_label)

        content_layout.addSpacing(10)

        # Server info
        server_label = QLabel(f"Serveur : {SYNC_SERVER_URL}")
        server_label.setStyleSheet(f"font-size: 9pt; color: {Theme.c('gray')};")
        content_layout.addWidget(server_label)

        content_layout.addSpacing(20)

        # Sync button
        sync_btn = QPushButton("Synchroniser maintenant")
        sync_btn.setObjectName("primaryButton")
        sync_btn.setStyleSheet(f"""
            QPushButton#primaryButton {{
                background-color: {Theme.c('primary')};
                font-size: 12pt;
                font-weight: bold;
                padding: 15px;
            }}
            QPushButton#primaryButton:hover {{
                background-color: {Theme.c('primary_hover')};
            }}
        """)
        sync_btn.clicked.connect(self._synchroniser_maintenant)
        content_layout.addWidget(sync_btn)

        # Detect button
        detect_btn = QPushButton("Detecter a nouveau")
        detect_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.c('info')};
                color: white;
                font-size: 11pt;
                padding: 12px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {Theme.c('primary')};
            }}
        """)
        detect_btn.clicked.connect(self._detecter_mode)
        content_layout.addWidget(detect_btn)

        content_layout.addStretch()

        layout.addWidget(content)

    def _maj_label_mode(self, mode):
        """Update mode display"""
        if mode == 'cloud':
            self.mode_label.setText("Connecte (Cloud)")
            self.mode_label.setStyleSheet(f"font-size: 14pt; font-weight: bold; color: {Theme.c('success')};")
        else:
            self.mode_label.setText("Hors ligne")
            self.mode_label.setStyleSheet(f"font-size: 14pt; font-weight: bold; color: {Theme.c('danger')};")

    def _synchroniser_maintenant(self):
        """Launch sync"""
        self.mode_label.setText("Synchronisation en cours...")
        self.mode_label.setStyleSheet(f"font-size: 14pt; font-weight: bold; color: {Theme.c('warning')};")
        self.repaint()

        try:
            succes = self.sync.synchroniser()
            if succes:
                self._maj_label_mode('cloud')
                # Update last sync
                dernier_sync = self.sync._get_dernier_sync()
                if dernier_sync:
                    try:
                        from datetime import datetime
                        dt = datetime.fromisoformat(dernier_sync)
                        self.last_sync_label.setText(dt.strftime("%d/%m/%Y %H:%M:%S"))
                    except Exception:
                        self.last_sync_label.setText(dernier_sync)
                information(self, "Synchronisation", "Synchronisation terminee avec succes !")
            else:
                self._maj_label_mode(self.sync.mode)
                avertissement(self, "Synchronisation", "Synchronisation impossible (hors ligne ou erreur)")
        except Exception as e:
            self._maj_label_mode('offline')
            erreur(self, "Erreur", f"Erreur: {e}")

    def _detecter_mode(self):
        """Redetect connection mode"""
        self.mode_label.setText("Detection en cours...")
        self.mode_label.setStyleSheet(f"font-size: 14pt; font-weight: bold; color: {Theme.c('warning')};")
        self.repaint()

        mode = self.sync.detecter_mode()
        self._maj_label_mode(mode)
