"""
Fenetre de creation du premier compte administrateur - PySide6
Affichee au premier lancement quand aucun utilisateur n'existe.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QFormLayout, QMessageBox, QFrame, QWidget
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from modules.utilisateurs import Utilisateur
from ui.theme import Theme


class PremierLancementWindow(QDialog):
    """Fenetre de creation du compte patron (premier lancement)."""

    compte_cree = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Premier lancement - Gestion Boutique")
        self.setFixedSize(500, 620)
        self.setModal(True)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # En-tete vert
        header = QFrame()
        header.setFixedHeight(120)
        header.setStyleSheet(
            f"background-color: {Theme.c('success')}; border: none;"
        )
        header_layout = QVBoxLayout(header)
        header_layout.setAlignment(Qt.AlignCenter)

        titre = QLabel("Bienvenue !")
        titre.setFont(QFont("Segoe UI", 22, QFont.Bold))
        titre.setStyleSheet("color: white; background: transparent;")
        titre.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(titre)

        sous_titre = QLabel("Creez votre compte administrateur")
        sous_titre.setFont(QFont("Segoe UI", 11))
        sous_titre.setStyleSheet("color: white; background: transparent;")
        sous_titre.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(sous_titre)

        layout.addWidget(header)

        # Formulaire
        form_container = QWidget()
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(50, 25, 50, 25)
        form_layout.setSpacing(4)

        # Nom
        form_layout.addWidget(self._label("Nom"))
        self._entry_nom = QLineEdit()
        self._entry_nom.setFont(QFont("Segoe UI", 12))
        form_layout.addWidget(self._entry_nom)
        form_layout.addSpacing(8)

        # Prenom
        form_layout.addWidget(self._label("Prenom"))
        self._entry_prenom = QLineEdit()
        self._entry_prenom.setFont(QFont("Segoe UI", 12))
        form_layout.addWidget(self._entry_prenom)
        form_layout.addSpacing(8)

        # Email
        form_layout.addWidget(self._label("Email"))
        self._entry_email = QLineEdit()
        self._entry_email.setFont(QFont("Segoe UI", 12))
        form_layout.addWidget(self._entry_email)
        form_layout.addSpacing(8)

        # Mot de passe
        form_layout.addWidget(self._label("Mot de passe"))
        self._entry_mdp = QLineEdit()
        self._entry_mdp.setFont(QFont("Segoe UI", 12))
        self._entry_mdp.setEchoMode(QLineEdit.Password)
        form_layout.addWidget(self._entry_mdp)

        hint = QLabel("Minimum 8 caracteres, au moins 1 chiffre")
        hint.setStyleSheet("color: #9CA3AF; font-size: 11px;")
        form_layout.addWidget(hint)
        form_layout.addSpacing(8)

        # Confirmation
        form_layout.addWidget(self._label("Confirmer le mot de passe"))
        self._entry_mdp_confirm = QLineEdit()
        self._entry_mdp_confirm.setFont(QFont("Segoe UI", 12))
        self._entry_mdp_confirm.setEchoMode(QLineEdit.Password)
        self._entry_mdp_confirm.returnPressed.connect(self._creer_compte)
        form_layout.addWidget(self._entry_mdp_confirm)
        form_layout.addSpacing(20)

        # Bouton
        btn_creer = QPushButton("CREER LE COMPTE")
        btn_creer.setProperty("class", "success")
        btn_creer.setFont(QFont("Segoe UI", 12, QFont.Bold))
        btn_creer.setCursor(Qt.PointingHandCursor)
        btn_creer.setMinimumHeight(48)
        btn_creer.clicked.connect(self._creer_compte)
        form_layout.addWidget(btn_creer)

        form_layout.addStretch()
        layout.addWidget(form_container)

        self._entry_nom.setFocus()

    def _label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setFont(QFont("Segoe UI", 10, QFont.Bold))
        return lbl

    def _creer_compte(self):
        nom = self._entry_nom.text().strip()
        prenom = self._entry_prenom.text().strip()
        email = self._entry_email.text().strip()
        mdp = self._entry_mdp.text()
        mdp_confirm = self._entry_mdp_confirm.text()

        # Validations
        if not all([nom, prenom, email, mdp, mdp_confirm]):
            QMessageBox.warning(self, "Attention",
                                "Veuillez remplir tous les champs")
            return

        if '@' not in email or '.' not in email:
            QMessageBox.warning(self, "Attention",
                                "Veuillez entrer un email valide")
            return

        if mdp != mdp_confirm:
            QMessageBox.critical(self, "Erreur",
                                 "Les mots de passe ne correspondent pas")
            self._entry_mdp_confirm.clear()
            return

        valide, message = Utilisateur.valider_mot_de_passe(mdp)
        if not valide:
            QMessageBox.critical(self, "Mot de passe", message)
            return

        succes, message = Utilisateur.creer_utilisateur(
            nom, prenom, email, mdp, role='patron'
        )

        if succes:
            QMessageBox.information(
                self, "Succes",
                "Compte administrateur cree !\n"
                "Vous pouvez maintenant vous connecter."
            )
            self.compte_cree.emit()
            self.accept()
        else:
            QMessageBox.critical(self, "Erreur", message)

    def closeEvent(self, event):
        # Empecher de fermer sans creer de compte
        QMessageBox.warning(
            self, "Attention",
            "Vous devez creer un compte administrateur pour continuer."
        )
        event.ignore()
