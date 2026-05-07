"""
Écran client — fenêtre affichée face au client (2ème écran ou TV).
Montre en temps réel les articles scannés, les prix et le total.
Se met à jour automatiquement quand le caissier modifie le panier.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame, QApplication
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QFont, QScreen

from ui.theme import Theme


class EcranClientWindow(QWidget):
    """
    Fenêtre indépendante (pas un dialog) affichée sur le 2ème écran.
    Le caissier ne l'utilise pas — elle s'actualise via update_panier().
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("HishamPOS — Écran client")
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        self._build_ui()
        self._afficher_accueil()
        self._placer_second_ecran()

    def _placer_second_ecran(self):
        """Place la fenêtre sur le 2ème écran si disponible, sinon coin droit."""
        screens = QApplication.screens()
        if len(screens) >= 2:
            geom = screens[1].geometry()
            self.setGeometry(geom)
            self.showFullScreen()
        else:
            screen = QApplication.primaryScreen().geometry()
            self.resize(600, 800)
            self.move(screen.width() - 620, 40)
            self.show()

    def _build_ui(self):
        self.setStyleSheet(f"background: {Theme.c('dark')}; color: white;")
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # ── En-tête boutique ──────────────────────────────────────────────────
        self._header = QFrame()
        self._header.setFixedHeight(90)
        self._header.setStyleSheet(f"background: {Theme.c('primary')};")
        header_layout = QVBoxLayout(self._header)
        header_layout.setContentsMargins(24, 0, 24, 0)

        from database import db
        nom_boutique = db.get_parametre('boutique_nom', 'HishamPOS')
        self._lbl_boutique = QLabel(nom_boutique)
        self._lbl_boutique.setFont(QFont("Segoe UI", 22, QFont.Bold))
        self._lbl_boutique.setStyleSheet("color: white;")
        header_layout.addWidget(self._lbl_boutique)

        layout.addWidget(self._header)

        # ── Zone accueil (visible quand panier vide) ──────────────────────────
        self._frame_accueil = QFrame()
        accueil_layout = QVBoxLayout(self._frame_accueil)
        accueil_layout.setAlignment(Qt.AlignCenter)

        lbl_bienvenue = QLabel("Bienvenue !")
        lbl_bienvenue.setFont(QFont("Segoe UI", 36, QFont.Bold))
        lbl_bienvenue.setAlignment(Qt.AlignCenter)
        lbl_bienvenue.setStyleSheet("color: white;")

        lbl_sous = QLabel("Vos achats apparaîtront ici.")
        lbl_sous.setFont(QFont("Segoe UI", 16))
        lbl_sous.setAlignment(Qt.AlignCenter)
        lbl_sous.setStyleSheet(f"color: {Theme.c('gray')};")

        accueil_layout.addWidget(lbl_bienvenue)
        accueil_layout.addWidget(lbl_sous)
        layout.addWidget(self._frame_accueil, stretch=1)

        # ── Zone panier (visible quand articles présents) ─────────────────────
        self._frame_panier = QFrame()
        self._frame_panier.hide()
        panier_layout = QVBoxLayout(self._frame_panier)
        panier_layout.setContentsMargins(0, 0, 0, 0)
        panier_layout.setSpacing(0)

        # En-tête colonnes
        col_header = QFrame()
        col_header.setStyleSheet("background: #1a1a2e; padding: 8px 16px;")
        col_h_layout = QHBoxLayout(col_header)
        col_h_layout.setContentsMargins(16, 8, 16, 8)
        for txt, stretch in [("Article", 3), ("Qté", 1), ("P.U.", 2), ("Total", 2)]:
            lbl = QLabel(txt)
            lbl.setStyleSheet("color: #9ca3af; font-size: 11pt; font-weight: bold;")
            col_h_layout.addWidget(lbl, stretch)
        panier_layout.addWidget(col_header)

        # Liste scrollable
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self._liste_container = QWidget()
        self._liste_container.setStyleSheet("background: transparent;")
        self._liste_layout = QVBoxLayout(self._liste_container)
        self._liste_layout.setSpacing(1)
        self._liste_layout.setContentsMargins(0, 0, 0, 0)
        self._liste_layout.addStretch()
        scroll.setWidget(self._liste_container)
        panier_layout.addWidget(scroll, stretch=1)

        layout.addWidget(self._frame_panier, stretch=1)

        # ── Pied — total ──────────────────────────────────────────────────────
        self._footer = QFrame()
        self._footer.setFixedHeight(100)
        self._footer.setStyleSheet(f"background: #0f172a;")
        footer_layout = QHBoxLayout(self._footer)
        footer_layout.setContentsMargins(24, 0, 24, 0)

        lbl_total_txt = QLabel("TOTAL")
        lbl_total_txt.setFont(QFont("Segoe UI", 18, QFont.Bold))
        lbl_total_txt.setStyleSheet("color: #9ca3af;")

        self._lbl_total = QLabel("0 FCFA")
        self._lbl_total.setFont(QFont("Segoe UI", 28, QFont.Bold))
        self._lbl_total.setStyleSheet("color: #22c55e;")
        self._lbl_total.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        footer_layout.addWidget(lbl_total_txt)
        footer_layout.addStretch()
        footer_layout.addWidget(self._lbl_total)
        layout.addWidget(self._footer)

    def _afficher_accueil(self):
        self._frame_accueil.show()
        self._frame_panier.hide()
        self._lbl_total.setText("0")

    @Slot(list, float, str)
    def update_panier(self, panier: list, total: float, devise: str):
        """Appelé par VentesWindow à chaque modification du panier."""
        if not panier:
            self._afficher_accueil()
            return

        self._frame_accueil.hide()
        self._frame_panier.show()

        # Vider les lignes existantes
        while self._liste_layout.count() > 1:
            item = self._liste_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for article in panier:
            ligne = QFrame()
            ligne.setStyleSheet(
                "background: #1e293b; border-bottom: 1px solid #334155;"
            )
            ligne.setFixedHeight(52)
            row = QHBoxLayout(ligne)
            row.setContentsMargins(16, 0, 16, 0)

            nom = QLabel(article.get('nom', ''))
            nom.setFont(QFont("Segoe UI", 13))
            nom.setStyleSheet("color: white;")
            nom.setWordWrap(True)

            qte = QLabel(str(article.get('quantite', 1)))
            qte.setFont(QFont("Segoe UI", 13, QFont.Bold))
            qte.setStyleSheet("color: #60a5fa;")
            qte.setAlignment(Qt.AlignCenter)

            pu = article.get('prix_vente', 0)
            lbl_pu = QLabel(f"{pu:,.0f}")
            lbl_pu.setFont(QFont("Segoe UI", 13))
            lbl_pu.setStyleSheet("color: #d1d5db;")
            lbl_pu.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

            sous_total = article.get('sous_total', 0)
            lbl_st = QLabel(f"{sous_total:,.0f}")
            lbl_st.setFont(QFont("Segoe UI", 13, QFont.Bold))
            lbl_st.setStyleSheet("color: white;")
            lbl_st.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

            row.addWidget(nom, 3)
            row.addWidget(qte, 1)
            row.addWidget(lbl_pu, 2)
            row.addWidget(lbl_st, 2)

            self._liste_layout.insertWidget(self._liste_layout.count() - 1, ligne)

        self._lbl_total.setText(f"{total:,.0f} {devise}")

    @Slot()
    def vente_terminee(self):
        """Remet l'écran en mode accueil après paiement."""
        self._afficher_accueil()
        self._lbl_total.setText(f"Merci pour votre achat !")
        from PySide6.QtCore import QTimer
        QTimer.singleShot(3000, self._afficher_accueil)
