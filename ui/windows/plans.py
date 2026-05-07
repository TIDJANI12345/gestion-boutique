"""
Fenêtre de comparaison des plans HishamPOS.
Affiche Standard / Pro / White Label avec bouton d'achat vers le site.
"""
import webbrowser

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QWidget, QGridLayout, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from ui.theme import Theme

SHOP_URL = "https://hishamdigital.com"

# ---------------------------------------------------------------------------
# Données de comparaison
# ---------------------------------------------------------------------------

_FEATURES_BASE = [
    ("Ventes + Reçu PDF 80mm", True, True, True),
    ("Gestion Stock + Alertes seuil bas", True, True, True),
    ("Import CSV produits (en masse)", True, True, True),
    ("Gestion Fournisseurs", True, True, True),
    ("Scanner code-barres (caméra PC)", True, True, True),
    ("Codes-barres EAN-13, EAN-8, Code 128", True, True, True),
    ("Prix de gros + Remises", True, True, True),
    ("Impression thermique ESC/POS 80mm", True, True, True),
    ("IFU / RCCM sur les reçus", True, True, True),
    ("Rapports journaliers & mensuels", True, True, True),
    ("Thème clair / sombre", True, True, True),
]

_FEATURES_PRO = [
    ("Multi-terminaux réseau local (jusqu'à 3 PCs)", False, True, True),
    ("Multi-utilisateurs : Caissiers + Gestionnaires illimités", False, True, True),
    ("Session caisse par rôle (timeout configurable)", False, True, True),
    ("Crédit Client — Ardoise", False, True, True),
    ("Gestion Clients & Fidélité", False, True, True),
    ("Rapports Marge + TVA détaillés", False, True, True),
    ("Exports Excel / CSV", False, True, True),
    ("Sauvegarde automatique quotidienne", False, True, True),
    ("Scanner mobile via téléphone (réseau local)", False, True, True),
    ("Audit log — traçabilité caisse par terminal", False, True, True),
]

_FEATURES_WL = [
    ("Terminaux réseau illimités", False, False, True),
    ("Votre Nom + Logo dans toute l'interface", False, False, True),
    ("Reçus PDF à votre marque (aucune mention HishamPOS)", False, False, True),
    ("Revendre à vos clients sous votre marque", False, False, True),
    ("Support prioritaire 12 mois", False, False, True),
]

_POUR_QUI = [
    ("#3B82F6", "Standard — 40 000 F",
     "Vous gérez votre boutique seul ou avec votre famille. 1 poste de caisse, toutes les fonctions essentielles. Idéal pour démarrer."),
    ("#10B981", "Pro — 85 000 F",
     "Vous avez des employés et/ou plusieurs caisses. Multi-terminaux sur votre réseau local, comptes Caissiers/Gestionnaires, ardoise client et rapports avancés."),
    ("#8B5CF6", "White Label — 200 000 F",
     "Vous êtes informaticien ou revendeur. Livrez le logiciel sous votre propre marque. Terminaux illimités, support 12 mois, 1 licence = 1 déploiement client."),
]


# ---------------------------------------------------------------------------
# Helpers UI
# ---------------------------------------------------------------------------

def _sep_label(texte: str) -> QFrame:
    frame = QFrame()
    frame.setStyleSheet(f"background-color: {Theme.c('light')}; border-radius: 4px;")
    lay = QHBoxLayout(frame)
    lay.setContentsMargins(10, 6, 10, 6)
    lbl = QLabel(texte)
    lbl.setFont(QFont("Segoe UI", 10, QFont.Bold))
    lbl.setStyleSheet(f"color: {Theme.c('text_secondary')}; background: transparent;")
    lay.addWidget(lbl)
    return frame


def _check_label(val: bool) -> QLabel:
    lbl = QLabel("✅" if val else "❌")
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setFont(QFont("Segoe UI", 13))
    return lbl


def _feat_label(texte: str) -> QLabel:
    lbl = QLabel(texte)
    lbl.setFont(QFont("Segoe UI", 10))
    lbl.setStyleSheet(f"color: {Theme.c('text')};")
    lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
    return lbl


# ---------------------------------------------------------------------------
# Fenêtre principale
# ---------------------------------------------------------------------------

class PlansWindow(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("HishamPOS — Comparer les plans")
        self.setMinimumSize(700, 580)
        self.resize(760, 680)
        self.setModal(True)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_header())

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(f"background: {Theme.c('bg')};")

        content = QWidget()
        content.setStyleSheet(f"background: {Theme.c('bg')};")
        vlay = QVBoxLayout(content)
        vlay.setContentsMargins(24, 20, 24, 20)
        vlay.setSpacing(6)

        vlay.addWidget(self._build_table())
        vlay.addSpacing(20)
        vlay.addWidget(self._build_pour_qui())
        vlay.addSpacing(16)
        vlay.addWidget(self._build_notes())
        vlay.addSpacing(20)
        vlay.addWidget(self._build_footer())

        scroll.setWidget(content)
        root.addWidget(scroll)

    # --- Header ---

    def _build_header(self) -> QFrame:
        frame = QFrame()
        frame.setFixedHeight(72)
        frame.setStyleSheet(f"background: {Theme.c('primary')};")
        lay = QHBoxLayout(frame)
        lay.setContentsMargins(28, 0, 28, 0)

        title = QLabel("HishamPOS — Quelle version choisir ?")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setStyleSheet("color: white;")
        lay.addWidget(title)
        lay.addStretch()

        sub = QLabel("Licence perpétuelle · 1 paiement · Mises à jour v2.x incluses")
        sub.setFont(QFont("Segoe UI", 10))
        sub.setStyleSheet("color: rgba(255,255,255,0.75);")
        lay.addWidget(sub)
        return frame

    # --- Table de comparaison ---

    def _build_table(self) -> QFrame:
        card = QFrame()
        card.setStyleSheet(
            f"background: {Theme.c('card_bg')}; border: 1px solid {Theme.c('card_border')};"
            " border-radius: 10px;"
        )
        grid = QGridLayout(card)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(0)

        # Colonne stretches
        grid.setColumnStretch(0, 4)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(2, 1)
        grid.setColumnStretch(3, 1)

        row = 0

        # --- En-tête colonnes ---
        headers = [
            ("Fonctionnalité", None, Qt.AlignLeft),
            ("Standard\n40 000 F/an", "#3B82F6", Qt.AlignCenter),
            ("Pro\n85 000 F/an", "#10B981", Qt.AlignCenter),
            ("White Label\n200 000 F", "#8B5CF6", Qt.AlignCenter),
        ]
        for col, (txt, color, align) in enumerate(headers):
            cell = QFrame()
            if col == 0:
                cell.setStyleSheet(
                    f"background: {Theme.c('table_header')};"
                    " border-top-left-radius: 10px;"
                    " border-bottom: 2px solid #E5E7EB;"
                )
            else:
                radius_right = " border-top-right-radius: 10px;" if col == 3 else ""
                cell.setStyleSheet(
                    f"background: {color}22; border-bottom: 2px solid {color};{radius_right}"
                )
            lay = QVBoxLayout(cell)
            lay.setContentsMargins(12, 10, 12, 10)
            lbl = QLabel(txt)
            lbl.setAlignment(align)
            lbl.setFont(QFont("Segoe UI", 10, QFont.Bold))
            if color:
                lbl.setStyleSheet(f"color: {color};")
            else:
                lbl.setStyleSheet(f"color: {Theme.c('text')};")
            lay.addWidget(lbl)
            grid.addWidget(cell, row, col)
        row += 1

        def add_separator(title: str):
            nonlocal row
            sep = QFrame()
            sep.setStyleSheet(f"background: {Theme.c('light')};")
            lay = QHBoxLayout(sep)
            lay.setContentsMargins(12, 5, 12, 5)
            lbl = QLabel(title)
            lbl.setFont(QFont("Segoe UI", 9, QFont.Bold))
            lbl.setStyleSheet(f"color: {Theme.c('text_secondary')}; background: transparent;")
            lay.addWidget(lbl)
            grid.addWidget(sep, row, 0, 1, 4)
            row += 1

        def add_feature_row(feat_tuple):
            nonlocal row
            texte, s, p, wl = feat_tuple
            bg = Theme.c('card_bg') if row % 2 == 0 else Theme.c('table_row_alt')
            for col, val in enumerate([texte, s, p, wl]):
                cell = QFrame()
                cell.setStyleSheet(f"background: {bg};")
                lay = QHBoxLayout(cell)
                lay.setContentsMargins(12, 7, 12, 7)
                if col == 0:
                    lbl = QLabel(val)
                    lbl.setFont(QFont("Segoe UI", 10))
                    lbl.setStyleSheet(f"color: {Theme.c('text')}; background: transparent;")
                    lay.addWidget(lbl)
                else:
                    lbl = QLabel("✅" if val else "❌")
                    lbl.setAlignment(Qt.AlignCenter)
                    lbl.setFont(QFont("Segoe UI", 12))
                    lbl.setStyleSheet("background: transparent;")
                    lay.addWidget(lbl)
                grid.addWidget(cell, row, col)
            row += 1

        add_separator("FONCTIONS DE BASE")
        for f in _FEATURES_BASE:
            add_feature_row(f)

        add_separator("FONCTIONS PRO")
        for f in _FEATURES_PRO:
            add_feature_row(f)

        add_separator("WHITE LABEL")
        for f in _FEATURES_WL:
            add_feature_row(f)

        return card

    # --- Pour qui ---

    def _build_pour_qui(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(
            f"background: {Theme.c('card_bg')}; border: 1px solid {Theme.c('card_border')};"
            " border-radius: 10px;"
        )
        vlay = QVBoxLayout(frame)
        vlay.setContentsMargins(20, 16, 20, 16)
        vlay.setSpacing(10)

        title = QLabel("POUR QUI ?")
        title.setFont(QFont("Segoe UI", 11, QFont.Bold))
        title.setStyleSheet(f"color: {Theme.c('text')};")
        vlay.addWidget(title)

        for color, plan, desc in _POUR_QUI:
            row = QHBoxLayout()
            dot = QLabel("●")
            dot.setFont(QFont("Segoe UI", 14))
            dot.setStyleSheet(f"color: {color};")
            dot.setFixedWidth(22)
            row.addWidget(dot)

            txt = QLabel(f"<b>{plan}</b> — {desc}")
            txt.setWordWrap(True)
            txt.setFont(QFont("Segoe UI", 10))
            txt.setStyleSheet(f"color: {Theme.c('text')};")
            row.addWidget(txt)
            vlay.addLayout(row)

        return frame

    # --- Notes bas ---

    def _build_notes(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(
            f"background: {Theme.c('warning')}18; border: 1px solid {Theme.c('warning')}44;"
            " border-radius: 8px;"
        )
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(4)

        notes = [
            "🔑  LICENCE PERPÉTUELLE : Payez 1 fois, utilisez à vie. Aucun abonnement mensuel.",
            "💬  Support WhatsApp inclus : 3 mois (Standard) · 6 mois (Pro) · 12 mois (White Label).",
            "📦  Mises à jour v2.x incluses sans supplément.",
            "🔄  Upgrade à tout moment : activez simplement la nouvelle clé, vos données sont conservées.",
            "🌐  Multi-terminaux Pro : serveur sur 1 PC, caisses sur les autres — réseau local uniquement.",
        ]
        for note in notes:
            lbl = QLabel(note)
            lbl.setFont(QFont("Segoe UI", 10))
            lbl.setStyleSheet(f"color: {Theme.c('text')};")
            lay.addWidget(lbl)

        return frame

    # --- Footer avec bouton ---

    def _build_footer(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet("background: transparent;")
        lay = QHBoxLayout(frame)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        btn_site = QPushButton("🛒  Acheter une licence sur hishamdigital.com")
        btn_site.setFont(QFont("Segoe UI", 11, QFont.Bold))
        btn_site.setMinimumHeight(46)
        btn_site.setCursor(Qt.PointingHandCursor)
        btn_site.setStyleSheet(f"""
            QPushButton {{
                background: {Theme.c('primary')};
                color: white;
                border-radius: 8px;
                padding: 0 24px;
            }}
            QPushButton:hover {{ background: {Theme.c('primary_hover')}; }}
            QPushButton:pressed {{ background: {Theme.c('primary_pressed')}; }}
        """)
        btn_site.clicked.connect(lambda: webbrowser.open(SHOP_URL))
        lay.addWidget(btn_site, stretch=3)

        btn_close = QPushButton("Fermer")
        btn_close.setFont(QFont("Segoe UI", 10))
        btn_close.setMinimumHeight(46)
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.setStyleSheet(f"""
            QPushButton {{
                background: {Theme.c('light')};
                color: {Theme.c('text')};
                border: 1px solid {Theme.c('card_border')};
                border-radius: 8px;
                padding: 0 20px;
            }}
            QPushButton:hover {{ background: {Theme.c('card_border')}; }}
        """)
        btn_close.clicked.connect(self.accept)
        lay.addWidget(btn_close, stretch=1)

        return frame
