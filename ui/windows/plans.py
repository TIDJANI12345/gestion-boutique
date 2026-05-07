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
    ("Gestion Stock + Alertes", True, True, True),
    ("Import CSV produits", True, True, True),
    ("Scanner code-barres (caméra)", True, True, True),
    ("Codes-barres EAN-13, EAN-8, Code 128", True, True, True),
    ("Prix de gros + Remises", True, True, True),
    ("Impression thermique ESC/POS", True, True, True),
    ("Rapports de base", True, True, True),
]

_FEATURES_PRO = [
    ("Multi-utilisateurs : Caissiers + Gestionnaires", False, True, True),
    ("Clôture Z + Session caisse", False, True, True),
    ("Crédit Client — Ardoise", False, True, True),
    ("Gestion Clients & Fidélité", False, True, True),
    ("Rapports Marge + TVA", False, True, True),
    ("Exports Excel / PDF", False, True, True),
    ("Sauvegarde automatique", False, True, True),
    ("Scanner mobile (réseau local)", False, True, True),
]

_FEATURES_WL = [
    ("Votre Nom + Logo dans l'interface", False, False, True),
    ("Reçus PDF à votre marque", False, False, True),
    ("Titre de fenêtre personnalisé", False, False, True),
    ("Revendre à vos clients", False, False, True),
]

_POUR_QUI = [
    ("#3B82F6", "Standard — 35 000 F",
     "Vous travaillez SEUL dans votre boutique. 1 seul compte (le patron). Idéal pour une boutique solo."),
    ("#10B981", "Pro — 60 000 F",
     "Vous avez des employés. Créez des comptes Caissiers et Gestionnaires sur le même PC. Ardoise client et rapports avancés."),
    ("#8B5CF6", "White Label — 200 000 F",
     "Vous êtes informaticien/revendeur. Livrez le logiciel sous votre propre marque à vos clients (1 licence = 1 déploiement client)."),
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

        sub = QLabel("Licences perpétuelles · 1 paiement · 1 PC")
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
            ("Standard\n35 000 F", "#3B82F6", Qt.AlignCenter),
            ("Pro\n60 000 F", "#10B981", Qt.AlignCenter),
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
            "🔑  LICENCE PERPÉTUELLE : Payez 1 fois, utilisez à vie sur 1 PC.",
            "💬  Support WhatsApp inclus : 3 mois (Standard) · 6 mois (Pro) · 12 mois (White Label).",
            "📦  Mises à jour v2.x incluses sans supplément.",
            "🔄  Upgrade possible à tout moment : achetez le plan supérieur et activez la nouvelle clé.",
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
