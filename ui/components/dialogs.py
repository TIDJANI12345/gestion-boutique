"""
Dialogues standard reutilisables pour l'application.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QSpinBox, QDoubleSpinBox, QMessageBox,
    QFormLayout, QWidget
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeySequence, QShortcut


def confirmer(parent: QWidget, titre: str, message: str) -> bool:
    """Affiche un dialogue de confirmation Oui/Non."""
    result = QMessageBox.question(
        parent, titre, message,
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.No
    )
    return result == QMessageBox.Yes


def information(parent: QWidget, titre: str, message: str):
    """Affiche un message d'information."""
    QMessageBox.information(parent, titre, message)


def erreur(parent: QWidget, titre: str, message: str):
    """Affiche un message d'erreur."""
    QMessageBox.critical(parent, titre, message)


def avertissement(parent: QWidget, titre: str, message: str):
    """Affiche un avertissement."""
    QMessageBox.warning(parent, titre, message)


class DialogueSaisie(QDialog):
    """Dialogue generique de saisie de texte."""

    def __init__(self, parent, titre: str, label: str, valeur: str = "",
                 placeholder: str = ""):
        super().__init__(parent)
        self.setWindowTitle(titre)
        self.setMinimumWidth(400)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Label
        lbl = QLabel(label)
        lbl.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(lbl)

        # Champ de saisie
        self._input = QLineEdit()
        self._input.setText(valeur)
        self._input.setPlaceholderText(placeholder)
        self._input.returnPressed.connect(self.accept)
        layout.addWidget(self._input)

        # Boutons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_annuler = QPushButton("Annuler")
        btn_annuler.setProperty("class", "secondary")
        btn_annuler.clicked.connect(self.reject)
        btn_layout.addWidget(btn_annuler)

        btn_ok = QPushButton("Valider")
        btn_ok.clicked.connect(self.accept)
        btn_layout.addWidget(btn_ok)

        layout.addLayout(btn_layout)

        self._input.setFocus()

    def valeur(self) -> str:
        return self._input.text().strip()

    @staticmethod
    def saisir(parent, titre: str, label: str, valeur: str = "",
               placeholder: str = "") -> tuple[str, bool]:
        """Affiche le dialogue et retourne (valeur, ok)."""
        dlg = DialogueSaisie(parent, titre, label, valeur, placeholder)
        ok = dlg.exec() == QDialog.Accepted
        return dlg.valeur(), ok


class DialogueQuantite(QDialog):
    """Dialogue de saisie de quantite (entier ou decimal)."""

    def __init__(self, parent, titre: str, label: str = "Quantite :",
                 valeur: int = 1, minimum: int = 1, maximum: int = 9999,
                 decimal: bool = False):
        super().__init__(parent)
        self.setWindowTitle(titre)
        self.setMinimumWidth(350)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Label
        lbl = QLabel(label)
        lbl.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(lbl)

        # Spinbox
        if decimal:
            self._spin = QDoubleSpinBox()
            self._spin.setDecimals(2)
            self._spin.setValue(float(valeur))
            self._spin.setMinimum(float(minimum))
            self._spin.setMaximum(float(maximum))
        else:
            self._spin = QSpinBox()
            self._spin.setValue(valeur)
            self._spin.setMinimum(minimum)
            self._spin.setMaximum(maximum)

        self._spin.setAlignment(Qt.AlignCenter)
        self._spin.setStyleSheet("font-size: 18px; padding: 8px;")
        layout.addWidget(self._spin)

        # Boutons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_annuler = QPushButton("Annuler")
        btn_annuler.setProperty("class", "secondary")
        btn_annuler.clicked.connect(self.reject)
        btn_layout.addWidget(btn_annuler)

        btn_ok = QPushButton("Valider")
        btn_ok.clicked.connect(self.accept)
        btn_layout.addWidget(btn_ok)

        layout.addLayout(btn_layout)

        # Entree valide
        QShortcut(QKeySequence(Qt.Key_Return), self, self.accept)

        self._spin.setFocus()
        self._spin.selectAll()

    def valeur(self):
        return self._spin.value()

    @staticmethod
    def saisir(parent, titre: str, label: str = "Quantite :",
               valeur: int = 1, minimum: int = 1, maximum: int = 9999,
               decimal: bool = False):
        """Affiche le dialogue et retourne (valeur, ok)."""
        dlg = DialogueQuantite(parent, titre, label, valeur, minimum,
                               maximum, decimal)
        ok = dlg.exec() == QDialog.Accepted
        return dlg.valeur(), ok
