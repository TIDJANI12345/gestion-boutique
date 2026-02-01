"""
Fenetre d'activation de licence - PySide6
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QMessageBox, QSpacerItem, QSizePolicy, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from modules.licence import GestionLicence
from config import APP_NAME
from ui.theme import Theme


class LicenceWindow(QDialog):
    """Fenetre d'activation de licence."""

    licence_activee = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.licence_manager = GestionLicence()
        self.setWindowTitle(f"Activation - {APP_NAME}")
        self.setFixedSize(500, 400)
        self.setModal(True)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(40, 20, 40, 20)

        # Icone
        icone = QLabel("\U0001F510")
        icone.setFont(QFont("Segoe UI", 40))
        icone.setAlignment(Qt.AlignCenter)
        layout.addWidget(icone)

        # Titre
        titre = QLabel("Activation Requise")
        titre.setFont(QFont("Segoe UI", 18, QFont.Bold))
        titre.setAlignment(Qt.AlignCenter)
        layout.addWidget(titre)

        # Description
        desc = QLabel(
            "Veuillez entrer votre cle de produit pour continuer.\n"
            "Cette licence sera liee a cet ordinateur."
        )
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet(f"color: {Theme.c('text_secondary')}; font-size: 12px;")
        layout.addWidget(desc)

        layout.addSpacerItem(QSpacerItem(0, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # Label champ
        lbl = QLabel("Cle de licence (Format GB26-...)")
        layout.addWidget(lbl)

        # Champ de saisie
        self._entry_cle = QLineEdit()
        self._entry_cle.setFont(QFont("Consolas", 12))
        self._entry_cle.setAlignment(Qt.AlignCenter)
        self._entry_cle.setPlaceholderText("GB26-XXXX-XXXX-XXXX")
        self._entry_cle.returnPressed.connect(self._activer)
        layout.addWidget(self._entry_cle)

        layout.addSpacerItem(QSpacerItem(0, 10, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # Bouton activer
        self._btn_activer = QPushButton("ACTIVER LE LOGICIEL")
        self._btn_activer.setProperty("class", "success")
        self._btn_activer.setCursor(Qt.PointingHandCursor)
        self._btn_activer.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self._btn_activer.clicked.connect(self._activer)
        layout.addWidget(self._btn_activer)

        layout.addStretch()

        # Bouton quitter
        btn_quitter = QPushButton("Quitter")
        btn_quitter.setProperty("class", "secondary")
        btn_quitter.setStyleSheet(f"color: {Theme.c('danger')};")
        btn_quitter.setCursor(Qt.PointingHandCursor)
        btn_quitter.clicked.connect(self.reject)
        layout.addWidget(btn_quitter, alignment=Qt.AlignCenter)

        self._entry_cle.setFocus()

    def _activer(self):
        cle = self._entry_cle.text().strip()
        if len(cle) < 10:
            QMessageBox.warning(self, "Erreur", "Format de cle invalide")
            return

        self._btn_activer.setEnabled(False)
        self._btn_activer.setText("Verification...")
        # Force le repaint avant l'appel reseau bloquant
        from PySide6.QtWidgets import QApplication
        QApplication.processEvents()

        succes, message = self.licence_manager.activer_en_ligne(cle)

        if succes:
            QMessageBox.information(
                self, "Felicitations",
                f"{message}\n\nL'application va maintenant demarrer."
            )
            self.licence_activee.emit()
            self.accept()
        else:
            QMessageBox.critical(self, "Echec de l'activation", message)
            self._btn_activer.setEnabled(True)
            self._btn_activer.setText("ACTIVER LE LOGICIEL")

    def closeEvent(self, event):
        self.reject()
