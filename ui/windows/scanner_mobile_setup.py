"""
Dialog de configuration Scanner Mobile
Affiche QR code pour connexion, gère démarrage/arrêt serveur
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTextEdit
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QImage

from ui.theme import Theme
from ui.components.dialogs import erreur, information
from modules.scanner_mobile_server import ScannerMobileServer, est_disponible
from modules.scanner_mobile_http import ScannerMobileHTTP

try:
    import qrcode
    from io import BytesIO
    QRCODE_DISPONIBLE = True
except ImportError:
    QRCODE_DISPONIBLE = False


class ScannerMobileSetupDialog(QDialog):
    """Dialog de configuration du scanner mobile"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Scanner Mobile - Configuration")
        self.setMinimumSize(500, 700)
        self.setStyleSheet(Theme.stylesheet())

        self.ws_server = None
        self.http_server = None
        self.url_connexion = ""
        self.clients_connectes = []

        self._setup_ui()
        self._check_disponibilite()

        # Centrer sur parent
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

        title = QLabel("📱 Scanner Mobile")
        title.setStyleSheet("color: white; font-size: 18pt; font-weight: bold;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        layout.addWidget(header)

        # Content
        content = QFrame()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(20)

        # Description
        desc = QLabel(
            "Scannez des codes-barres depuis votre téléphone sans installer d'application.\n"
            "Utilisez simplement le navigateur de votre mobile."
        )
        desc.setStyleSheet(f"color: {Theme.c('gray')}; font-size: 10pt;")
        desc.setWordWrap(True)
        content_layout.addWidget(desc)

        # Statut
        self.label_statut = QLabel("⏸ Serveur arrêté")
        self.label_statut.setStyleSheet(f"""
            background-color: {Theme.c('light')};
            color: {Theme.c('dark')};
            font-size: 12pt;
            font-weight: bold;
            padding: 15px;
            border-radius: 8px;
        """)
        self.label_statut.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(self.label_statut)

        # QR Code
        qr_frame = QFrame()
        qr_frame.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 2px solid {Theme.c('gray')};
                border-radius: 8px;
                padding: 20px;
            }}
        """)
        qr_layout = QVBoxLayout(qr_frame)
        qr_layout.setAlignment(Qt.AlignCenter)

        qr_label = QLabel("QR Code de Connexion")
        qr_label.setStyleSheet("font-size: 11pt; font-weight: bold; color: #1F2937;")
        qr_label.setAlignment(Qt.AlignCenter)
        qr_layout.addWidget(qr_label)

        self.qr_image = QLabel()
        self.qr_image.setFixedSize(250, 250)
        self.qr_image.setStyleSheet("background-color: #F3F4F6; border-radius: 8px;")
        self.qr_image.setAlignment(Qt.AlignCenter)
        self.qr_image.setText("Démarrez le serveur\npour voir le QR code")
        qr_layout.addWidget(self.qr_image)

        content_layout.addWidget(qr_frame)

        # URL
        self.label_url = QLabel("URL : -")
        self.label_url.setStyleSheet(f"""
            background-color: {Theme.c('light')};
            color: {Theme.c('dark')};
            font-size: 10pt;
            padding: 10px;
            border-radius: 6px;
            font-family: 'Courier New', monospace;
        """)
        self.label_url.setAlignment(Qt.AlignCenter)
        self.label_url.setWordWrap(True)
        content_layout.addWidget(self.label_url)

        # Clients connectés
        clients_label = QLabel("📡 Clients connectés")
        clients_label.setStyleSheet("font-size: 11pt; font-weight: bold;")
        content_layout.addWidget(clients_label)

        self.text_clients = QTextEdit()
        self.text_clients.setReadOnly(True)
        self.text_clients.setMaximumHeight(80)
        self.text_clients.setPlaceholderText("Aucun client connecté")
        self.text_clients.setStyleSheet(f"""
            QTextEdit {{
                background-color: {Theme.c('light')};
                border: 1px solid {Theme.c('gray')};
                border-radius: 6px;
                padding: 10px;
                font-size: 9pt;
            }}
        """)
        content_layout.addWidget(self.text_clients)

        content_layout.addStretch()

        # Boutons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.btn_toggle = QPushButton("Démarrer le Serveur")
        self.btn_toggle.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.c('success')};
                color: white;
                font-size: 11pt;
                font-weight: bold;
                padding: 12px 20px;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: #059669;
            }}
        """)
        self.btn_toggle.clicked.connect(self._toggle_serveur)
        btn_layout.addWidget(self.btn_toggle)

        close_btn = QPushButton("Fermer")
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.c('gray')};
                color: white;
                font-size: 11pt;
                font-weight: bold;
                padding: 12px 20px;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: #4B5563;
            }}
        """)
        close_btn.clicked.connect(self.reject)
        btn_layout.addWidget(close_btn)

        content_layout.addLayout(btn_layout)

        layout.addWidget(content)

    def _check_disponibilite(self):
        """Vérifier si les dépendances sont installées"""
        if not est_disponible():
            erreur(self, "Dépendances manquantes",
                "Le scanner mobile nécessite le module 'websockets'.\n\n"
                "Installez-le avec :\npip install websockets")
            self.btn_toggle.setEnabled(False)

        if not QRCODE_DISPONIBLE:
            # QR code déjà dans requirements.txt normalement
            pass

    def _toggle_serveur(self):
        """Démarrer ou arrêter le serveur"""
        if self.ws_server and self.ws_server.isRunning():
            self._arreter_serveur()
        else:
            self._demarrer_serveur()

    def _demarrer_serveur(self):
        """Démarrer les serveurs WebSocket et HTTP"""
        try:
            # Serveur WebSocket
            self.ws_server = ScannerMobileServer(host='0.0.0.0', port=8765)
            self.ws_server.client_connecte.connect(self._on_client_connecte)
            self.ws_server.client_deconnecte.connect(self._on_client_deconnecte)
            self.ws_server.erreur.connect(self._on_erreur_ws)
            self.ws_server.start()

            # Serveur HTTP
            self.http_server = ScannerMobileHTTP(port=8080)
            self.http_server.demarrage_ok.connect(self._on_http_ok)
            self.http_server.erreur.connect(self._on_erreur_http)
            self.http_server.start()

            self.label_statut.setText("🟢 Serveur démarré")
            self.label_statut.setStyleSheet(f"""
                background-color: {Theme.c('success')};
                color: white;
                font-size: 12pt;
                font-weight: bold;
                padding: 15px;
                border-radius: 8px;
            """)

            self.btn_toggle.setText("Arrêter le Serveur")
            self.btn_toggle.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Theme.c('danger')};
                    color: white;
                    font-size: 11pt;
                    font-weight: bold;
                    padding: 12px 20px;
                    border-radius: 6px;
                }}
                QPushButton:hover {{
                    background-color: #DC2626;
                }}
            """)

        except Exception as e:
            erreur(self, "Erreur", f"Impossible de démarrer le serveur :\n{e}")

    def _arreter_serveur(self):
        """Arrêter les serveurs"""
        if self.ws_server:
            self.ws_server.arreter()
            self.ws_server = None

        if self.http_server:
            self.http_server.arreter()
            self.http_server = None

        self.label_statut.setText("⏸ Serveur arrêté")
        self.label_statut.setStyleSheet(f"""
            background-color: {Theme.c('light')};
            color: {Theme.c('dark')};
            font-size: 12pt;
            font-weight: bold;
            padding: 15px;
            border-radius: 8px;
        """)

        self.btn_toggle.setText("Démarrer le Serveur")
        self.btn_toggle.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.c('success')};
                color: white;
                font-size: 11pt;
                font-weight: bold;
                padding: 12px 20px;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: #059669;
            }}
        """)

        self.qr_image.clear()
        self.qr_image.setText("Démarrez le serveur\npour voir le QR code")
        self.label_url.setText("URL : -")
        self.text_clients.clear()
        self.clients_connectes.clear()

    def _on_http_ok(self, url):
        """HTTP serveur démarré"""
        self.url_connexion = url
        self.label_url.setText(f"URL : {url}")
        self._generer_qr_code(url)

    def _on_erreur_ws(self, message):
        """Erreur WebSocket"""
        erreur(self, "Erreur WebSocket", message)
        self._arreter_serveur()

    def _on_erreur_http(self, message):
        """Erreur HTTP"""
        erreur(self, "Erreur HTTP", message)
        self._arreter_serveur()

    def _on_client_connecte(self, ip):
        """Client WebSocket connecté"""
        self.clients_connectes.append(ip)
        self._update_clients_list()

    def _on_client_deconnecte(self, ip):
        """Client WebSocket déconnecté"""
        if ip in self.clients_connectes:
            self.clients_connectes.remove(ip)
        self._update_clients_list()

    def _update_clients_list(self):
        """Mettre à jour la liste des clients"""
        if self.clients_connectes:
            text = "\n".join([f"✓ {ip}" for ip in self.clients_connectes])
            self.text_clients.setText(text)
        else:
            self.text_clients.clear()

    def _generer_qr_code(self, url):
        """Générer et afficher le QR code"""
        if not QRCODE_DISPONIBLE:
            return

        try:
            qr = qrcode.QRCode(version=1, box_size=10, border=2)
            qr.add_data(url)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")

            # Convertir en QPixmap
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)

            qimage = QImage()
            qimage.loadFromData(buffer.read())
            pixmap = QPixmap.fromImage(qimage)
            pixmap = pixmap.scaled(250, 250, Qt.KeepAspectRatio, Qt.SmoothTransformation)

            self.qr_image.setPixmap(pixmap)

        except Exception as e:
            self.qr_image.setText(f"Erreur QR code:\n{e}")

    def closeEvent(self, event):
        """Arrêter les serveurs à la fermeture"""
        self._arreter_serveur()
        event.accept()
