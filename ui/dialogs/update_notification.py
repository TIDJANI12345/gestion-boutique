"""
Dialog de notification de mise à jour disponible
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon
from modules.updater import Updater, formater_taille
from config import APP_VERSION


class UpdateNotificationDialog(QDialog):
    """Dialog personnalisé pour notifier d'une mise à jour disponible"""

    def __init__(self, infos_update, parent=None):
        super().__init__(parent)
        self.infos = infos_update
        self.setWindowTitle("Mise à Jour Disponible")
        self.setMinimumWidth(500)
        self.setModal(True)
        self._setup_ui()

    def _setup_ui(self):
        """Construire l'interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # === TITRE ===
        titre = QLabel("🎉 Nouvelle version disponible !")
        titre_font = QFont()
        titre_font.setPointSize(14)
        titre_font.setBold(True)
        titre.setFont(titre_font)
        titre.setAlignment(Qt.AlignCenter)
        layout.addWidget(titre)

        # === INFORMATIONS VERSION ===
        infos_layout = QVBoxLayout()
        infos_layout.setSpacing(10)

        # Version
        version_label = QLabel(
            f"<b>Nouvelle version :</b> {self.infos.get('version', 'N/A')}"
        )
        version_label.setStyleSheet("font-size: 12pt;")
        infos_layout.addWidget(version_label)

        # Date de sortie
        if 'date' in self.infos:
            date_label = QLabel(f"<b>Date de sortie :</b> {self.infos['date']}")
            infos_layout.addWidget(date_label)

        # Taille
        if 'taille_mb' in self.infos:
            taille = formater_taille(self.infos['taille_mb'])
            taille_label = QLabel(f"<b>Taille du téléchargement :</b> ~{taille}")
            infos_layout.addWidget(taille_label)

        # Version actuelle
        actuelle_label = QLabel(f"<i>Version actuelle : {APP_VERSION}</i>")
        actuelle_label.setStyleSheet("color: gray;")
        infos_layout.addWidget(actuelle_label)

        layout.addLayout(infos_layout)

        # === MESSAGE / DESCRIPTION ===
        if 'message' in self.infos and self.infos['message']:
            separator1 = QLabel("─" * 60)
            separator1.setAlignment(Qt.AlignCenter)
            separator1.setStyleSheet("color: #ccc;")
            layout.addWidget(separator1)

            message_label = QLabel(self.infos['message'])
            message_label.setWordWrap(True)
            message_label.setStyleSheet("padding: 10px; background: #f0f0f0; border-radius: 5px;")
            layout.addWidget(message_label)

        # === BADGE CRITIQUE (si applicable) ===
        if self.infos.get('critique', False):
            critique_label = QLabel("⚠️ MISE À JOUR CRITIQUE - Installation fortement recommandée")
            critique_label.setStyleSheet(
                "color: white; background: #d32f2f; padding: 8px; "
                "font-weight: bold; border-radius: 5px;"
            )
            critique_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(critique_label)

        layout.addSpacing(10)

        # === BOUTONS ===
        boutons_layout = QHBoxLayout()
        boutons_layout.setSpacing(10)

        # Bouton Télécharger (principal)
        btn_telecharger = QPushButton("📥 Télécharger")
        btn_telecharger.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px 20px;
                font-size: 11pt;
                font-weight: bold;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        btn_telecharger.clicked.connect(self._telecharger)
        boutons_layout.addWidget(btn_telecharger)

        # Bouton Voir Changements
        btn_changelog = QPushButton("📄 Voir les changements")
        btn_changelog.clicked.connect(self._voir_changelog)
        boutons_layout.addWidget(btn_changelog)

        layout.addLayout(boutons_layout)

        # === BOUTONS SECONDAIRES ===
        boutons_secondaires = QHBoxLayout()

        btn_plus_tard = QPushButton("⏰ Plus tard")
        btn_plus_tard.clicked.connect(self.reject)
        boutons_secondaires.addWidget(btn_plus_tard)

        btn_ignorer = QPushButton("🚫 Ignorer cette version")
        btn_ignorer.setStyleSheet("color: gray;")
        btn_ignorer.clicked.connect(self._ignorer_version)
        boutons_secondaires.addWidget(btn_ignorer)

        layout.addLayout(boutons_secondaires)

    def _telecharger(self):
        """Ouvrir la page de téléchargement et afficher les instructions"""
        url_download = self.infos.get('url_download')

        if not url_download:
            QMessageBox.warning(
                self, "Erreur",
                "URL de téléchargement introuvable.\n"
                "Veuillez visiter le site officiel."
            )
            return

        # Ouvrir le navigateur
        Updater.ouvrir_page_telechargement(url_download)

        # Afficher les instructions
        QMessageBox.information(
            self, "Instructions de Mise à Jour",
            "<h3>📋 Instructions :</h3>"
            "<ol>"
            "<li><b>Téléchargez</b> le fichier (le navigateur s'est ouvert)</li>"
            "<li><b>Fermez</b> complètement l'application</li>"
            "<li><b>Sauvegardez</b> votre base de données :<br>"
            "   <i>Menu Fichier → Sauvegarde</i></li>"
            "<li><b>Remplacez</b> l'ancien fichier .exe par le nouveau</li>"
            "<li><b>Relancez</b> l'application</li>"
            "</ol>"
            "<br>"
            "<p style='color: #f57c00;'><b>⚠️ Important :</b> Ne sautez pas l'étape de sauvegarde !</p>"
        )

        self.accept()

    def _voir_changelog(self):
        """Ouvrir la page du changelog"""
        url_changelog = self.infos.get('url_changelog')

        if url_changelog:
            Updater.ouvrir_page_telechargement(url_changelog)
        else:
            QMessageBox.information(
                self, "Changements",
                "Consultez la page de téléchargement pour voir les changements détaillés."
            )

    def _ignorer_version(self):
        """Marquer cette version comme ignorée"""
        reponse = QMessageBox.question(
            self, "Ignorer cette version ?",
            f"Vous ne serez plus notifié de la version {self.infos['version']}.\n\n"
            "Vous pourrez toujours vérifier manuellement les mises à jour via\n"
            "le menu Aide → Vérifier les mises à jour.\n\n"
            "Continuer ?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reponse == QMessageBox.Yes:
            Updater.ignorer_version(self.infos['version'])
            QMessageBox.information(
                self, "Version ignorée",
                f"La version {self.infos['version']} sera ignorée."
            )
            self.reject()
