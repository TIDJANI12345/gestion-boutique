"""
Dialog d'ouverture de caisse — saisie du fond de caisse.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QIntValidator

from ui.theme import Theme


class OuvertureCaisseDialog(QDialog):
    """Dialog bloquant : saisie du fond de caisse avant de commencer à vendre."""

    session_ouverte = Signal(int)  # session_id

    def __init__(self, utilisateur: dict, parent=None):
        super().__init__(parent)
        self.utilisateur = utilisateur
        self.setWindowTitle("Ouverture de caisse")
        self.setFixedSize(420, 300)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowCloseButtonHint)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(30, 24, 30, 24)

        # En-tête
        header = QFrame()
        header.setStyleSheet(f"background: {Theme.c('primary')}; border-radius: 8px;")
        hl = QVBoxLayout(header)
        hl.setContentsMargins(16, 12, 16, 12)
        titre = QLabel("Ouverture de caisse")
        titre.setFont(QFont("Segoe UI", 15, QFont.Bold))
        titre.setStyleSheet("color: white; background: transparent;")
        titre.setAlignment(Qt.AlignCenter)
        hl.addWidget(titre)
        layout.addWidget(header)

        # Caissier
        lbl_caissier = QLabel(
            f"Caissier : {self.utilisateur.get('prenom', '')} {self.utilisateur.get('nom', '')}"
        )
        lbl_caissier.setStyleSheet(f"color: {Theme.c('text_secondary')}; font-size: 12px;")
        lbl_caissier.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_caissier)

        # Fond de caisse
        lbl = QLabel("Fond de caisse (FCFA)")
        lbl.setFont(QFont("Segoe UI", 11, QFont.Bold))
        layout.addWidget(lbl)

        self._input_fond = QLineEdit()
        self._input_fond.setPlaceholderText("Ex : 50000")
        self._input_fond.setValidator(QIntValidator(0, 99999999))
        self._input_fond.setAlignment(Qt.AlignRight)
        self._input_fond.setMinimumHeight(44)
        self._input_fond.setFont(QFont("Segoe UI", 14))
        self._input_fond.returnPressed.connect(self._ouvrir)
        layout.addWidget(self._input_fond)

        layout.addStretch()

        # Bouton
        btn = QPushButton("Ouvrir la caisse")
        btn.setMinimumHeight(44)
        btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
        btn.setStyleSheet(
            f"background: {Theme.c('success')}; color: white; "
            "border: none; border-radius: 6px;"
        )
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(self._ouvrir)
        layout.addWidget(btn)

        self._input_fond.setFocus()

    def _ouvrir(self):
        texte = self._input_fond.text().strip()
        try:
            fond = int(texte) if texte else 0
        except ValueError:
            fond = 0

        from modules.sessions import ouvrir_session
        utilisateur_id = self.utilisateur.get('id')
        succes, message, session_id = ouvrir_session(utilisateur_id, fond)

        if succes:
            self.session_ouverte.emit(session_id)
            self.accept()
        else:
            QMessageBox.warning(self, "Impossible d'ouvrir", message)
