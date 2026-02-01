"""
Barre d'outils standard pour les fenetres de l'application.
"""
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QSizePolicy
)
from PySide6.QtCore import Signal
from PySide6.QtGui import QKeySequence, QShortcut


class BoutonAction:
    """Configuration d'un bouton de la toolbar."""

    def __init__(self, texte: str, raccourci: str = None,
                 classe: str = "primary", tooltip: str = None):
        self.texte = texte
        self.raccourci = raccourci
        self.classe = classe
        self.tooltip = tooltip


class BarreOutils(QWidget):
    """Barre d'outils horizontale avec boutons et raccourcis clavier.

    Usage :
        toolbar = BarreOutils(self)
        toolbar.ajouter_bouton("Nouveau", "F1", classe="success")
        toolbar.ajouter_bouton("Supprimer", "Delete", classe="danger")
        toolbar.ajouter_spacer()
        toolbar.ajouter_bouton("Fermer", "Escape", classe="secondary")
        toolbar.bouton_clique.connect(self._on_toolbar_action)
    """

    bouton_clique = Signal(str)  # Emet le texte du bouton clique

    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(8)
        self._boutons: dict[str, QPushButton] = {}

    def ajouter_bouton(self, texte: str, raccourci: str = None,
                       classe: str = "primary", tooltip: str = None) -> QPushButton:
        """Ajoute un bouton a la toolbar.

        Args:
            texte: Texte du bouton (aussi utilise comme identifiant).
            raccourci: Raccourci clavier (ex: "F1", "Ctrl+N", "Delete").
            classe: Style CSS - "primary", "success", "danger", "secondary".
            tooltip: Infobulle.

        Returns:
            Le QPushButton cree.
        """
        btn = QPushButton(texte)
        btn.setProperty("class", classe)
        btn.setCursor(Qt.PointingHandCursor)

        if raccourci:
            label = f"{texte} ({raccourci})"
            btn.setText(label)
            shortcut = QShortcut(QKeySequence(raccourci), self.window())
            shortcut.activated.connect(lambda t=texte: self.bouton_clique.emit(t))

        if tooltip:
            btn.setToolTip(tooltip)

        btn.clicked.connect(lambda checked=False, t=texte: self.bouton_clique.emit(t))

        self._boutons[texte] = btn
        self._layout.addWidget(btn)
        return btn

    def ajouter_spacer(self):
        """Ajoute un espace flexible entre les boutons."""
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._layout.addWidget(spacer)

    def activer_bouton(self, texte: str, actif: bool = True):
        """Active ou desactive un bouton."""
        if texte in self._boutons:
            self._boutons[texte].setEnabled(actif)

    def obtenir_bouton(self, texte: str) -> QPushButton:
        """Retourne le QPushButton par son texte."""
        return self._boutons.get(texte)
