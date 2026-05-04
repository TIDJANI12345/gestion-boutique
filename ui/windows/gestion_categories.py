"""
Gestion des catégories de produits.
"""
import json
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QListWidget, QListWidgetItem, QMessageBox, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from ui.theme import Theme
from database import db

_KEY = 'categories_produits'

_CATEGORIES_DEFAUT = [
    "Alimentation", "Boissons", "Hygiène", "Nettoyage",
    "Électronique", "Vêtements", "Chaussures", "Fournitures bureau",
    "Cosmétiques", "Divers",
]


def charger_categories() -> list[str]:
    raw = db.get_parametre(_KEY, None)
    try:
        cats = json.loads(raw) if raw else []
    except Exception:
        cats = []
    if not cats:
        # Aucune catégorie enregistrée → pré-charger les défauts
        sauvegarder_categories(_CATEGORIES_DEFAUT)
        return sorted(_CATEGORIES_DEFAUT)
    return sorted(set(c.strip() for c in cats if c.strip()))


def sauvegarder_categories(cats: list[str]):
    db.set_parametre(_KEY, json.dumps(sorted(set(cats))))


class GestionCategoriesWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestion des catégories")
        self.setFixedSize(420, 480)
        self.setModal(True)
        self._setup_ui()
        self._charger()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QFrame()
        header.setFixedHeight(65)
        header.setStyleSheet(f"background-color: {Theme.c('primary')};")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(20, 0, 20, 0)
        lbl = QLabel("Catégories de produits")
        lbl.setFont(QFont("Segoe UI", 14, QFont.Bold))
        lbl.setStyleSheet("color: white;")
        hl.addWidget(lbl)
        layout.addWidget(header)

        body = QFrame()
        bl = QVBoxLayout(body)
        bl.setContentsMargins(20, 16, 20, 16)
        bl.setSpacing(10)

        self._liste = QListWidget()
        self._liste.setAlternatingRowColors(True)
        bl.addWidget(self._liste)

        row = QHBoxLayout()
        self._entry = QLineEdit()
        self._entry.setPlaceholderText("Nouvelle catégorie...")
        self._entry.setFont(QFont("Segoe UI", 11))
        self._entry.returnPressed.connect(self._ajouter)
        row.addWidget(self._entry)

        btn_add = QPushButton("Ajouter")
        btn_add.setAutoDefault(False)
        btn_add.setFixedWidth(90)
        btn_add.setStyleSheet(
            f"background:{Theme.c('success')};color:white;border:none;"
            f"border-radius:5px;padding:8px;"
        )
        btn_add.clicked.connect(self._ajouter)
        row.addWidget(btn_add)
        bl.addLayout(row)

        btn_sup = QPushButton("Supprimer la sélection")
        btn_sup.setAutoDefault(False)
        btn_sup.setStyleSheet(
            f"background:{Theme.c('danger')};color:white;border:none;"
            f"border-radius:5px;padding:8px;"
        )
        btn_sup.clicked.connect(self._supprimer)
        bl.addWidget(btn_sup)

        btn_ok = QPushButton("Fermer")
        btn_ok.setAutoDefault(False)
        btn_ok.setStyleSheet(
            f"background:{Theme.c('primary')};color:white;border:none;"
            f"border-radius:5px;padding:10px;font-weight:bold;"
        )
        btn_ok.clicked.connect(self.accept)
        bl.addWidget(btn_ok)

        layout.addWidget(body, 1)

    def _charger(self):
        from modules.produits import Produit
        self._liste.clear()
        predefinies = charger_categories()
        depuis_produits = Produit.obtenir_categories()
        toutes = sorted(set(predefinies + depuis_produits))
        for cat in toutes:
            self._liste.addItem(QListWidgetItem(cat))

    def _ajouter(self):
        nom = self._entry.text().strip()
        if not nom:
            return
        cats = charger_categories()
        if nom.lower() in [c.lower() for c in cats]:
            QMessageBox.warning(self, "Doublon", f'"{nom}" existe déjà.')
            return
        cats.append(nom)
        sauvegarder_categories(cats)
        self._entry.clear()
        self._charger()

    def _supprimer(self):
        item = self._liste.currentItem()
        if not item:
            return
        nom = item.text()
        rep = QMessageBox.question(
            self, "Confirmer", f'Supprimer la catégorie "{nom}" ?'
        )
        if rep != QMessageBox.Yes:
            return
        cats = [c for c in charger_categories() if c != nom]
        sauvegarder_categories(cats)
        self._charger()
