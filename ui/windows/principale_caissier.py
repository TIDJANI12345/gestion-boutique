"""
Dashboard simplifie pour les caissiers - PySide6
Interface epuree : grand bouton vente, stats jour, deconnexion.
"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QMessageBox
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont, QShortcut, QKeySequence

from config import APP_NAME
from ui.theme import Theme
from modules.logger import get_logger

logger = get_logger('fenetre_caissier')


class PrincipaleCaissierWindow(QMainWindow):
    """Dashboard caissier - interface simplifiee."""

    session_expiree = Signal()
    deconnexion_demandee = Signal()

    def __init__(self, utilisateur: dict, parent=None):
        super().__init__(parent)
        self.utilisateur = utilisateur
        self.setWindowTitle(f"{APP_NAME} - Caissier")
        self.setMinimumSize(800, 550)
        self.resize(900, 700)

        self._setup_ui()
        self._setup_raccourcis()
        self._setup_session_timeout()

        # Premier chargement
        self.actualiser_stats()

        # Actualisation periodique (30s)
        self._timer_refresh = QTimer(self)
        self._timer_refresh.setInterval(30000)
        self._timer_refresh.timeout.connect(self.actualiser_stats)
        self._timer_refresh.start()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # En-tete
        header = QFrame()
        header.setFixedHeight(100)
        header.setStyleSheet(f"background-color: {Theme.c('primary')};")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(30, 0, 30, 0)

        # Info caissier
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        lbl_role = QLabel("Caissier")
        lbl_role.setStyleSheet("color: white; font-size: 11px; background: transparent;")
        info_layout.addWidget(lbl_role)

        lbl_nom = QLabel(f"{self.utilisateur['prenom']} {self.utilisateur['nom']}")
        lbl_nom.setFont(QFont("Segoe UI", 20, QFont.Bold))
        lbl_nom.setStyleSheet("color: white; background: transparent;")
        info_layout.addWidget(lbl_nom)

        header_layout.addLayout(info_layout)
        header_layout.addStretch()

        # Bouton deconnexion
        btn_deconnexion = QPushButton("Deconnexion")
        btn_deconnexion.setStyleSheet("""
            QPushButton {
                background: white; color: #3B82F6;
                border: none; border-radius: 6px;
                padding: 10px 20px; font-size: 11px; font-weight: bold;
            }
            QPushButton:hover { background: #F3F4F6; }
        """)
        btn_deconnexion.setCursor(Qt.PointingHandCursor)
        btn_deconnexion.clicked.connect(self._deconnexion)
        header_layout.addWidget(btn_deconnexion)

        main_layout.addWidget(header)

        # Contenu
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(40, 40, 40, 20)
        content_layout.setSpacing(20)

        # GRAND BOUTON NOUVELLE VENTE
        btn_vente = QPushButton("NOUVELLE VENTE")
        btn_vente.setFont(QFont("Segoe UI", 24, QFont.Bold))
        btn_vente.setCursor(Qt.PointingHandCursor)
        btn_vente.setMinimumHeight(120)
        btn_vente.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.c('success')};
                color: white; border: none; border-radius: 10px;
                font-size: 24px; font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {Theme.c('success_hover')};
            }}
        """)
        btn_vente.clicked.connect(self.ouvrir_ventes)
        content_layout.addWidget(btn_vente)

        # Stats du jour
        stats_frame = QFrame()
        stats_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.c('card_bg')};
                border: 1px solid {Theme.c('card_border')};
                border-radius: 8px;
            }}
        """)
        stats_layout = QVBoxLayout(stats_frame)
        stats_layout.setContentsMargins(30, 25, 30, 25)
        stats_layout.setSpacing(15)

        stats_title = QLabel("Vos statistiques du jour")
        stats_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        stats_layout.addWidget(stats_title)

        # Grille 2 colonnes
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(15)

        # Carte ventes
        ventes_card = QFrame()
        ventes_card.setStyleSheet(
            f"background: {Theme.c('light')}; border-radius: 8px; border: none;"
        )
        vc_layout = QVBoxLayout(ventes_card)
        vc_layout.setAlignment(Qt.AlignCenter)
        vc_layout.setContentsMargins(20, 15, 20, 15)

        vc_label = QLabel("Ventes aujourd'hui")
        vc_label.setStyleSheet(f"color: {Theme.c('text_secondary')}; font-size: 11px;")
        vc_label.setAlignment(Qt.AlignCenter)
        vc_layout.addWidget(vc_label)

        self._label_ventes = QLabel("0")
        self._label_ventes.setFont(QFont("Segoe UI", 32, QFont.Bold))
        self._label_ventes.setStyleSheet(f"color: {Theme.c('primary')};")
        self._label_ventes.setAlignment(Qt.AlignCenter)
        vc_layout.addWidget(self._label_ventes)

        cards_layout.addWidget(ventes_card)

        # Carte CA
        ca_card = QFrame()
        ca_card.setStyleSheet(
            f"background: {Theme.c('light')}; border-radius: 8px; border: none;"
        )
        cc_layout = QVBoxLayout(ca_card)
        cc_layout.setAlignment(Qt.AlignCenter)
        cc_layout.setContentsMargins(20, 15, 20, 15)

        cc_label = QLabel("Chiffre d'affaires")
        cc_label.setStyleSheet(f"color: {Theme.c('text_secondary')}; font-size: 11px;")
        cc_label.setAlignment(Qt.AlignCenter)
        cc_layout.addWidget(cc_label)

        self._label_ca = QLabel("0 FCFA")
        self._label_ca.setFont(QFont("Segoe UI", 32, QFont.Bold))
        self._label_ca.setStyleSheet(f"color: {Theme.c('success')};")
        self._label_ca.setAlignment(Qt.AlignCenter)
        cc_layout.addWidget(self._label_ca)

        cards_layout.addWidget(ca_card)
        stats_layout.addLayout(cards_layout)
        content_layout.addWidget(stats_frame)

        # Bouton voir mes ventes
        btn_mes_ventes = QPushButton("Voir mes ventes")
        btn_mes_ventes.setFont(QFont("Segoe UI", 13, QFont.Bold))
        btn_mes_ventes.setCursor(Qt.PointingHandCursor)
        btn_mes_ventes.setMinimumHeight(55)
        btn_mes_ventes.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.c('info')};
                color: white; border: none; border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: {Theme.c('primary')};
            }}
        """)
        btn_mes_ventes.clicked.connect(self.voir_mes_ventes)
        content_layout.addWidget(btn_mes_ventes)

        content_layout.addStretch()
        main_layout.addWidget(content, 1)

        # Footer
        footer = QFrame()
        footer.setFixedHeight(35)
        footer.setStyleSheet(f"background-color: {Theme.c('light')};")
        footer_layout = QHBoxLayout(footer)
        footer_label = QLabel("F1=Nouvelle vente | F3=Mes ventes | F5=Actualiser")
        footer_label.setStyleSheet(f"color: {Theme.c('gray')}; font-size: 10px;")
        footer_label.setAlignment(Qt.AlignCenter)
        footer_layout.addWidget(footer_label)
        main_layout.addWidget(footer)

    def _setup_raccourcis(self):
        for key, slot in [
            ("F1", self.ouvrir_ventes),
            ("F3", self.voir_mes_ventes),
            ("F5", self.actualiser_stats),
        ]:
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.activated.connect(slot)

    def actualiser_stats(self):
        """Actualiser stats PERSONNELLES du caissier (uniquement ses ventes)"""
        try:
            from modules.rapports import Rapport
            stats = Rapport.statistiques_utilisateur(self.utilisateur['id'])
            self._label_ventes.setText(str(stats['nb_ventes']))
            self._label_ca.setText(f"{stats['ca_jour']:,.0f} FCFA")
        except Exception as e:
            logger.error(f"Erreur actualisation: {e}")

    def ouvrir_ventes(self):
        from ui.windows.ventes import VentesWindow
        dlg = VentesWindow(parent=self, utilisateur=self.utilisateur)
        dlg.vente_terminee.connect(self.actualiser_stats)
        dlg.exec()

    def voir_mes_ventes(self):
        """Ouvrir la liste de MES ventes (filtré caissier)"""
        from ui.windows.liste_ventes import ListeVentesWindow
        dlg = ListeVentesWindow(parent=self, utilisateur=self.utilisateur)
        dlg.exec()

    def _deconnexion(self):
        from modules.utilisateurs import Utilisateur
        Utilisateur.logger_action(
            self.utilisateur['id'], 'deconnexion',
            f"Deconnexion de {self.utilisateur.get('nom', '')}"
        )
        self.deconnexion_demandee.emit()
        self.close()

    # === SESSION TIMEOUT ===

    def _setup_session_timeout(self):
        from database import db
        timeout_str = db.get_parametre('session_timeout', '900')
        try:
            timeout_ms = int(timeout_str) * 1000
        except ValueError:
            timeout_ms = 900000

        self._session_timer = QTimer(self)
        self._session_timer.setInterval(timeout_ms)
        self._session_timer.setSingleShot(True)
        self._session_timer.timeout.connect(self._on_session_expired)
        self._session_timer.start()

    def _reset_session_timer(self):
        if hasattr(self, '_session_timer'):
            self._session_timer.start()

    def keyPressEvent(self, event):
        self._reset_session_timer()
        super().keyPressEvent(event)

    def mousePressEvent(self, event):
        self._reset_session_timer()
        super().mousePressEvent(event)

    def _on_session_expired(self):
        self._timer_refresh.stop()
        QMessageBox.information(
            self, "Session expiree",
            "Vous avez ete deconnecte pour inactivite."
        )
        self.session_expiree.emit()
        self.close()
