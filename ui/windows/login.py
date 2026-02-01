"""
Fenetre de connexion avec protection brute-force - PySide6
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QMessageBox, QFrame, QWidget
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont

from modules.utilisateurs import Utilisateur
from ui.theme import Theme


class LoginWindow(QDialog):
    """Fenetre de connexion utilisateur."""

    MAX_TENTATIVES = 5
    DUREE_BLOCAGE = 30  # secondes

    login_success = Signal(dict)  # emet les infos user

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Connexion - Gestion Boutique")
        self.setFixedSize(450, 480)
        self.setModal(True)

        self._tentatives = 0
        self._bloque = False
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)
        self._secondes_restantes = 0

        Utilisateur.initialiser_tables()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # En-tete bleu
        header = QFrame()
        header.setFixedHeight(130)
        header.setStyleSheet(
            f"background-color: {Theme.c('primary')}; border: none;"
        )
        header_layout = QVBoxLayout(header)
        header_layout.setAlignment(Qt.AlignCenter)

        titre = QLabel("AUTHENTIFICATION")
        titre.setFont(QFont("Segoe UI", 20, QFont.Bold))
        titre.setStyleSheet("color: white; background: transparent;")
        titre.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(titre)

        layout.addWidget(header)

        # Formulaire
        form_container = QWidget()
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(50, 30, 50, 30)
        form_layout.setSpacing(4)

        # Email
        form_layout.addWidget(self._label("Email"))
        self._entry_email = QLineEdit()
        self._entry_email.setFont(QFont("Segoe UI", 12))
        form_layout.addWidget(self._entry_email)
        form_layout.addSpacing(16)

        # Mot de passe
        form_layout.addWidget(self._label("Mot de passe"))
        self._entry_password = QLineEdit()
        self._entry_password.setFont(QFont("Segoe UI", 12))
        self._entry_password.setEchoMode(QLineEdit.Password)
        self._entry_password.returnPressed.connect(self._se_connecter)
        form_layout.addWidget(self._entry_password)
        form_layout.addSpacing(24)

        # Bouton connexion
        self._btn_connexion = QPushButton("SE CONNECTER")
        self._btn_connexion.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self._btn_connexion.setCursor(Qt.PointingHandCursor)
        self._btn_connexion.setMinimumHeight(48)
        self._btn_connexion.clicked.connect(self._se_connecter)
        form_layout.addWidget(self._btn_connexion)

        # Label blocage
        self._label_blocage = QLabel("")
        self._label_blocage.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self._label_blocage.setStyleSheet(f"color: {Theme.c('danger')};")
        self._label_blocage.setAlignment(Qt.AlignCenter)
        form_layout.addWidget(self._label_blocage)

        form_layout.addStretch()
        layout.addWidget(form_container)

        self._entry_email.setFocus()

    def _label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setFont(QFont("Segoe UI", 10, QFont.Bold))
        return lbl

    def _se_connecter(self):
        if self._bloque:
            return

        email = self._entry_email.text().strip()
        password = self._entry_password.text()

        if not email or not password:
            QMessageBox.warning(self, "Attention",
                                "Veuillez remplir tous les champs")
            return

        user = Utilisateur.authentifier(email, password)

        if user:
            self._tentatives = 0
            infos_user = {
                'id': user[0],
                'nom': user[1],
                'prenom': user[2],
                'email': user[3],
                'role': user[5],
                'super_admin': user[8] if len(user) > 8 else 0
            }
            Utilisateur.logger_action(user[0], 'connexion', "Connexion reussie")
            self.login_success.emit(infos_user)
            self.accept()
        else:
            self._tentatives += 1
            restantes = self.MAX_TENTATIVES - self._tentatives

            if self._tentatives >= self.MAX_TENTATIVES:
                self._bloquer()
            else:
                QMessageBox.critical(
                    self, "Erreur",
                    f"Email ou mot de passe incorrect\n"
                    f"({restantes} tentative(s) restante(s))"
                )
            self._entry_password.clear()

    def _bloquer(self):
        self._bloque = True
        self._secondes_restantes = self.DUREE_BLOCAGE
        self._btn_connexion.setEnabled(False)
        self._entry_email.setEnabled(False)
        self._entry_password.setEnabled(False)
        self._timer.start()
        self._update_label_blocage()

    def _tick(self):
        self._secondes_restantes -= 1
        if self._secondes_restantes <= 0:
            self._debloquer()
        else:
            self._update_label_blocage()

    def _update_label_blocage(self):
        self._label_blocage.setText(
            f"Trop de tentatives. Reessayez dans {self._secondes_restantes}s"
        )

    def _debloquer(self):
        self._timer.stop()
        self._bloque = False
        self._tentatives = 0
        self._btn_connexion.setEnabled(True)
        self._entry_email.setEnabled(True)
        self._entry_password.setEnabled(True)
        self._label_blocage.setText("")

    def closeEvent(self, event):
        self.reject()
