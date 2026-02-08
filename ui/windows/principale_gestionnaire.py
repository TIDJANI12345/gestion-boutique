"""
Dashboard pour les gestionnaires - PySide6
Interface adaptee pour la gestion de produits, stocks, clients.
"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QMessageBox, QMenu, QMenuBar
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont, QShortcut, QKeySequence

from config import APP_NAME
from ui.theme import Theme
from modules.logger import get_logger
from modules.permissions import Permissions
from database import db

logger = get_logger('fenetre_gestionnaire')


class PrincipaleGestionnaireWindow(QMainWindow):
    """Dashboard gestionnaire - interface adaptee."""

    session_expiree = Signal()
    deconnexion_demandee = Signal()

    def __init__(self, utilisateur: dict, parent=None):
        super().__init__(parent)
        self.utilisateur = utilisateur
        self.setWindowTitle(f"{APP_NAME} - Gestionnaire")
        self.setMinimumSize(1000, 700)
        self.resize(1100, 800)

        self._setup_ui()
        self._setup_menubar()
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

        # Info gestionnaire
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        lbl_role = QLabel("Gestionnaire")
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

        # === Boutons d'actions principaux ===
        actions_row_1 = QHBoxLayout()
        actions_row_1.setSpacing(20)

        # Bouton Produits
        btn_produits = QPushButton("Produits (F1)")
        btn_produits.setFont(QFont("Segoe UI", 16, QFont.Bold))
        btn_produits.setCursor(Qt.PointingHandCursor)
        btn_produits.setMinimumHeight(100)
        btn_produits.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.c('info')};
                color: white; border: none; border-radius: 10px;
            }}
            QPushButton:hover {{
                background-color: {Theme.c('primary')};
            }}
        """)
        btn_produits.clicked.connect(self.ouvrir_produits)
        actions_row_1.addWidget(btn_produits)

        # Bouton Clients
        btn_clients = QPushButton("Clients (F2)")
        btn_clients.setFont(QFont("Segoe UI", 16, QFont.Bold))
        btn_clients.setCursor(Qt.PointingHandCursor)
        btn_clients.setMinimumHeight(100)
        btn_clients.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.c('warning')};
                color: white; border: none; border-radius: 10px;
            }}
            QPushButton:hover {{
                background-color: #D97706;
            }}
        """)
        btn_clients.clicked.connect(self.ouvrir_clients)
        actions_row_1.addWidget(btn_clients)

        # Bouton Nouvelle Vente (Conditionnel)
        if Permissions.peut(self.utilisateur, 'effectuer_ventes'):
            btn_vente = QPushButton("Nouvelle Vente (F3)")
            btn_vente.setFont(QFont("Segoe UI", 16, QFont.Bold))
            btn_vente.setCursor(Qt.PointingHandCursor)
            btn_vente.setMinimumHeight(100)
            btn_vente.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Theme.c('success')};
                    color: white; border: none; border-radius: 10px;
                }}
                QPushButton:hover {{
                    background-color: {Theme.c('success_hover')};
                }}
            """)
            btn_vente.clicked.connect(self.ouvrir_ventes)
            actions_row_1.addWidget(btn_vente)
        content_layout.addLayout(actions_row_1)

        # Stats du jour (Adapté pour gestionnaire)
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

        stats_title = QLabel("Statistiques du stock") # Peut etre ajuste
        stats_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        stats_layout.addWidget(stats_title)

        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(15)

        # Carte Nombre de Produits
        produits_card = QFrame()
        produits_card.setStyleSheet(
            f"background: {Theme.c('light')}; border-radius: 8px; border: none;"
        )
        pc_layout = QVBoxLayout(produits_card)
        pc_layout.setAlignment(Qt.AlignCenter)
        pc_layout.setContentsMargins(20, 15, 20, 15)

        pc_label = QLabel("Total Produits")
        pc_label.setStyleSheet(f"color: {Theme.c('text_secondary')}; font-size: 11px;")
        pc_label.setAlignment(Qt.AlignCenter)
        pc_layout.addWidget(pc_label)

        self._label_total_produits = QLabel("0")
        self._label_total_produits.setFont(QFont("Segoe UI", 32, QFont.Bold))
        self._label_total_produits.setStyleSheet(f"color: {Theme.c('primary')};")
        self._label_total_produits.setAlignment(Qt.AlignCenter)
        pc_layout.addWidget(self._label_total_produits)
        cards_layout.addWidget(produits_card)

        # Carte Valeur du Stock
        stock_valeur_card = QFrame()
        stock_valeur_card.setStyleSheet(
            f"background: {Theme.c('light')}; border-radius: 8px; border: none;"
        )
        svc_layout = QVBoxLayout(stock_valeur_card)
        svc_layout.setAlignment(Qt.AlignCenter)
        svc_layout.setContentsMargins(20, 15, 20, 15)

        svc_label = QLabel("Valeur du Stock")
        svc_label.setStyleSheet(f"color: {Theme.c('text_secondary')}; font-size: 11px;")
        svc_label.setAlignment(Qt.AlignCenter)
        svc_layout.addWidget(svc_label)

        self._label_valeur_stock = QLabel("0 FCFA")
        self._label_valeur_stock.setFont(QFont("Segoe UI", 32, QFont.Bold))
        self._label_valeur_stock.setStyleSheet(f"color: {Theme.c('success')};")
        self._label_valeur_stock.setAlignment(Qt.AlignCenter)
        svc_layout.addWidget(self._label_valeur_stock)
        cards_layout.addWidget(stock_valeur_card)

        # Carte Produits en Alerte
        alerte_card = QFrame()
        alerte_card.setStyleSheet(
            f"background: {Theme.c('light')}; border-radius: 8px; border: none;"
        )
        ac_layout = QVBoxLayout(alerte_card)
        ac_layout.setAlignment(Qt.AlignCenter)
        ac_layout.setContentsMargins(20, 15, 20, 15)

        ac_label = QLabel("Produits en alerte")
        ac_label.setStyleSheet(f"color: {Theme.c('text_secondary')}; font-size: 11px;")
        ac_label.setAlignment(Qt.AlignCenter)
        ac_layout.addWidget(ac_label)

        self._label_produits_alerte = QLabel("0")
        self._label_produits_alerte.setFont(QFont("Segoe UI", 32, QFont.Bold))
        self._label_produits_alerte.setStyleSheet(f"color: {Theme.c('warning')};")
        self._label_produits_alerte.setAlignment(Qt.AlignCenter)
        ac_layout.addWidget(self._label_produits_alerte)
        cards_layout.addWidget(alerte_card)


        stats_layout.addLayout(cards_layout)
        content_layout.addWidget(stats_frame)

        if Permissions.peut(self.utilisateur, 'voir_mes_ventes'):
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
        footer_label = QLabel("F1=Produits | F2=Clients | F3=Nouvelle vente (si activé) | F5=Actualiser")
        footer_label.setStyleSheet(f"color: {Theme.c('gray')}; font-size: 10px;")
        footer_label.setAlignment(Qt.AlignCenter)
        footer_layout.addWidget(footer_label)
        main_layout.addWidget(footer)

    def _setup_menubar(self):
        menubar = self.menuBar()

        # Menu Fichier
        file_menu = menubar.addMenu("Fichier")
        file_menu.addAction("Déconnexion", self._deconnexion)
        file_menu.addAction("Quitter", self.close)

        # Menu Gestion
        gestion_menu = menubar.addMenu("Gestion")
        if Permissions.peut(self.utilisateur, 'gerer_produits'):
            gestion_menu.addAction("Produits", self.ouvrir_produits)
        if Permissions.peut(self.utilisateur, 'gerer_clients'):
            gestion_menu.addAction("Clients", self.ouvrir_clients)
        if Permissions.peut(self.utilisateur, 'effectuer_ventes'):
            gestion_menu.addAction("Nouvelle Vente", self.ouvrir_ventes)
        if Permissions.peut(self.utilisateur, 'voir_mes_ventes'):
            gestion_menu.addAction("Mes Ventes", self.voir_mes_ventes)

        # Menu Outils
        outils_menu = menubar.addMenu("Outils")
        outils_menu.addAction("📱 Scanner Mobile", self.ouvrir_scanner_mobile_setup)

        # Menu Aide
        help_menu = menubar.addMenu("Aide")
        help_menu.addAction("À Propos", self.ouvrir_a_propos)


    def _setup_raccourcis(self):
        shortcuts = []
        if Permissions.peut(self.utilisateur, 'gerer_produits'):
            shortcuts.append(("F1", self.ouvrir_produits))
        if Permissions.peut(self.utilisateur, 'gerer_clients'):
            shortcuts.append(("F2", self.ouvrir_clients))
        if Permissions.peut(self.utilisateur, 'effectuer_ventes'):
            shortcuts.append(("F3", self.ouvrir_ventes))
        
        shortcuts.append(("F5", self.actualiser_stats))
        shortcuts.append(("F12", self._deconnexion))


        for key, slot in shortcuts:
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.activated.connect(slot)

    def actualiser_stats(self):
        """Actualiser stats pour gestionnaire (stock, produits en alerte, etc.)"""
        try:
            from modules.produits import Produit
            from modules.rapports import Rapport

            # Stats Produits
            total_produits = Produit.compter_produits()
            produits_alerte = Produit.compter_produits_alerte()
            valeur_stock = Produit.calculer_valeur_stock_globale()

            self._label_total_produits.setText(str(total_produits))
            self._label_produits_alerte.setText(str(produits_alerte))
            self._label_valeur_stock.setText(f"{valeur_stock:,.0f} FCFA")

            # Stats Ventes (si le gestionnaire peut vendre)
            if Permissions.peut(self.utilisateur, 'voir_mes_ventes'):
                stats_ventes = Rapport.statistiques_utilisateur(self.utilisateur['id'])
                # Vous pouvez ajouter ces stats a l'interface si desire
                logger.info(f"Stats ventes gestionnaire: {stats_ventes}")

        except Exception as e:
            logger.error(f"Erreur actualisation stats gestionnaire: {e}")

    def ouvrir_produits(self):
        from ui.windows.produits import ProduitsWindow
        if Permissions.peut(self.utilisateur, 'gerer_produits'):
            dlg = ProduitsWindow(parent=self)
            dlg.exec()
        else:
            QMessageBox.warning(self, "Accès refusé", "Vous n'avez pas la permission de gérer les produits.")

    def ouvrir_clients(self):
        from ui.windows.clients import ClientsWindow
        if Permissions.peut(self.utilisateur, 'gerer_clients'):
            dlg = ClientsWindow(parent=self)
            dlg.exec()
        else:
            QMessageBox.warning(self, "Accès refusé", "Vous n'avez pas la permission de gérer les clients.")

    def ouvrir_ventes(self):
        from ui.windows.ventes import VentesWindow
        if Permissions.peut(self.utilisateur, 'effectuer_ventes'):
            dlg = VentesWindow(parent=self, utilisateur=self.utilisateur)
            dlg.vente_terminee.connect(self.actualiser_stats) # Connecter a l'actualisation des stats manager
            dlg.exec()
        else:
            QMessageBox.warning(self, "Accès refusé", "Vous n'avez pas la permission d'effectuer des ventes.")

    def voir_mes_ventes(self):
        """Ouvrir la liste de MES ventes (filtré gestionnaire)"""
        from ui.windows.liste_ventes import ListeVentesWindow
        if Permissions.peut(self.utilisateur, 'voir_mes_ventes'):
            dlg = ListeVentesWindow(parent=self, utilisateur=self.utilisateur)
            dlg.exec()
        else:
            QMessageBox.warning(self, "Accès refusé", "Vous n'avez pas la permission de voir vos ventes.")

    def ouvrir_scanner_mobile_setup(self):
        """Ouvrir la configuration du scanner mobile"""
        from ui.windows.scanner_mobile_setup import ScannerMobileSetupDialog
        dlg = ScannerMobileSetupDialog(parent=self)
        dlg.exec()

    def ouvrir_a_propos(self):
        from ui.windows.a_propos import AProposWindow
        dlg = AProposWindow(parent=self)
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
