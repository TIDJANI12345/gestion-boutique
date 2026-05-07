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
from modules.fiscalite import get_devise
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
        self._setup_menubar()
        self._afficher_bandeau_statut()
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

        # Badge plan
        self._badge_plan = QLabel("")
        self._badge_plan.setObjectName("badge_plan")
        self._badge_plan.setStyleSheet(
            "background: #6B7280; color: white; border-radius: 4px; "
            "padding: 3px 10px; font-weight: bold; font-size: 10pt;"
        )
        header_layout.addWidget(self._badge_plan)
        header_layout.addSpacing(8)

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

        self._btn_theme = QPushButton("☾ Sombre" if not Theme.est_sombre() else "☀ Clair")
        self._btn_theme.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.2); color: white;
                border: 1px solid rgba(255,255,255,0.3); border-radius: 4px;
                padding: 8px 14px; font-size: 11px;
            }
            QPushButton:hover { background: rgba(255,255,255,0.3); }
        """)
        self._btn_theme.setCursor(Qt.PointingHandCursor)
        self._btn_theme.clicked.connect(self._basculer_theme)
        header_layout.addWidget(self._btn_theme)
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

        self._label_ca = QLabel("0 {get_devise()}")
        self._label_ca.setFont(QFont("Segoe UI", 32, QFont.Bold))
        self._label_ca.setStyleSheet(f"color: {Theme.c('success')};")
        self._label_ca.setAlignment(Qt.AlignCenter)
        cc_layout.addWidget(self._label_ca)

        cards_layout.addWidget(ca_card)
        stats_layout.addLayout(cards_layout)
        content_layout.addWidget(stats_frame)

        # Boutons session caisse
        try:
            from modules.features import peut
            if peut('session_caisse'):
                caisse_row = QHBoxLayout()
                btn_ouvrir_caisse = QPushButton("Ouvrir la caisse")
                btn_ouvrir_caisse.setFont(QFont("Segoe UI", 12, QFont.Bold))
                btn_ouvrir_caisse.setCursor(Qt.PointingHandCursor)
                btn_ouvrir_caisse.setMinimumHeight(48)
                btn_ouvrir_caisse.setStyleSheet(
                    f"background-color: {Theme.c('success')}; color: white; "
                    "border: none; border-radius: 6px;"
                )
                btn_ouvrir_caisse.clicked.connect(self.ouvrir_caisse)
                caisse_row.addWidget(btn_ouvrir_caisse)

                btn_cloture_z = QPushButton("Clôture Z")
                btn_cloture_z.setFont(QFont("Segoe UI", 12, QFont.Bold))
                btn_cloture_z.setCursor(Qt.PointingHandCursor)
                btn_cloture_z.setMinimumHeight(48)
                btn_cloture_z.setStyleSheet(
                    f"background-color: {Theme.c('danger')}; color: white; "
                    "border: none; border-radius: 6px;"
                )
                btn_cloture_z.clicked.connect(self.cloturer_z)
                caisse_row.addWidget(btn_cloture_z)
                content_layout.addLayout(caisse_row)
        except Exception:
            pass

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

        # Bouton annulation vente
        btn_annulation = QPushButton("Annuler une vente")
        btn_annulation.setFont(QFont("Segoe UI", 12, QFont.Bold))
        btn_annulation.setCursor(Qt.PointingHandCursor)
        btn_annulation.setMinimumHeight(48)
        btn_annulation.setStyleSheet("""
            QPushButton {
                background-color: #EF4444; color: white;
                border: none; border-radius: 6px;
            }
            QPushButton:hover { background-color: #DC2626; }
        """)
        btn_annulation.clicked.connect(self.ouvrir_annulation_vente)
        content_layout.addWidget(btn_annulation)

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

    def _setup_menubar(self):
        from PySide6.QtGui import QAction
        menubar = self.menuBar()
        menu_aide = menubar.addMenu("Aide")
        action_plans = QAction("📋 Comparer les plans (Standard / Pro / White Label)", self)
        action_plans.triggered.connect(self.ouvrir_plans)
        menu_aide.addAction(action_plans)

    def ouvrir_plans(self):
        from ui.windows.plans import PlansWindow
        dlg = PlansWindow(parent=self)
        dlg.exec()

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
        self._afficher_bandeau_statut()
        try:
            import modules.reseau as reseau
            if reseau.actif():
                stats = reseau.get_client().get_stats_dashboard()
                self._label_ventes.setText(str(stats.get('ventes_jour', {}).get('nb', 0)))
                self._label_ca.setText(
                    f"{stats.get('ventes_jour', {}).get('total', 0):,.0f} {get_devise()}"
                )
                return
        except Exception:
            pass
        try:
            from modules.rapports import Rapport
            stats = Rapport.statistiques_utilisateur(self.utilisateur['id'])
            self._label_ventes.setText(str(stats['nb_ventes']))
            self._label_ca.setText(f"{stats['ca_jour']:,.0f} {get_devise()}")
        except Exception as e:
            logger.error(f"Erreur actualisation: {e}")

    def ouvrir_ventes(self):
        from ui.windows.ventes import VentesWindow
        from ui.windows.ecran_client import EcranClientWindow
        dlg = VentesWindow(parent=self, utilisateur=self.utilisateur)
        dlg.vente_terminee.connect(self.actualiser_stats)
        # Ouvrir l'écran client si activé dans les préférences
        from database import db
        if db.get_parametre('ecran_client_actif', '0') == '1':
            ecran = EcranClientWindow()
            dlg.panier_modifie.connect(ecran.update_panier)
            dlg.vente_terminee.connect(ecran.vente_terminee)
            dlg._ecran_client = ecran
        dlg.exec()
        if dlg._ecran_client:
            dlg._ecran_client.close()

    # === SESSION CAISSE ===

    def ouvrir_caisse(self):
        try:
            from modules.features import peut
            if not peut('session_caisse'):
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.information(self, "Pro requis",
                    "Les sessions de caisse nécessitent le plan Pro.")
                return
            from ui.dialogs.ouverture_caisse import OuvertureCaisseDialog
            dlg = OuvertureCaisseDialog(self.utilisateur, self)
            dlg.exec()
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Erreur", str(e))

    def cloturer_z(self):
        try:
            from modules.features import peut
            if not peut('session_caisse'):
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.information(self, "Pro requis",
                    "Les sessions de caisse nécessitent le plan Pro.")
                return
            from modules.sessions import session_actuelle
            if not session_actuelle():
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.information(self, "Info", "Aucune session ouverte.")
                return
            from ui.dialogs.cloture_z import ClotureZDialog
            dlg = ClotureZDialog(self.utilisateur, self)
            dlg.cloture_effectuee.connect(lambda _: self.actualiser_stats())
            dlg.exec()
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Erreur", str(e))

    def ouvrir_annulation_vente(self):
        from ui.windows.annulation_vente import AnnulationVenteWindow
        dlg = AnnulationVenteWindow(self.utilisateur, self)
        dlg.vente_annulee.connect(lambda _: self.actualiser_stats())
        dlg.exec()

    def voir_mes_ventes(self):
        """Ouvrir la liste de MES ventes (filtré caissier)"""
        from ui.windows.liste_ventes import ListeVentesWindow
        dlg = ListeVentesWindow(parent=self, utilisateur=self.utilisateur)
        dlg.exec()

    def _basculer_theme(self):
        from ui.theme import Theme
        Theme.basculer()
        self._btn_theme.setText("☾ Sombre" if not Theme.est_sombre() else "☀ Clair")
        self.update()

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
        timeout_str = db.get_parametre('session_timeout_caissier', '1800')
        try:
            timeout_ms = int(timeout_str) * 1000
        except ValueError:
            timeout_ms = 0

        self._session_timer = QTimer(self)
        self._session_timer.setSingleShot(True)
        self._session_timer.timeout.connect(self._on_session_expired)
        if timeout_ms > 0:
            self._session_timer.setInterval(timeout_ms)
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

    # === BADGE + BANDEAU LICENCE ===

    def _afficher_bandeau_statut(self):
        # Supprimer l'ancien bandeau
        if getattr(self, '_bandeau_widget', None) is not None:
            central = self.centralWidget()
            if central and central.layout():
                central.layout().removeWidget(self._bandeau_widget)
            self._bandeau_widget.deleteLater()
            self._bandeau_widget = None

        try:
            from modules.features import statut_expiration, demo_infos, plan_actuel
            from database import db
            from PySide6.QtWidgets import QFrame, QHBoxLayout

            plan = plan_actuel()
            badges = {
                'demo':        ('DÉMO', '#3B82F6'),
                'standard':    ('STANDARD', '#6B7280'),
                'pro':         ('PRO', '#10B981'),
                'white_label': ('PRO', '#10B981'),
            }
            label_txt, couleur = badges.get(plan, ('STANDARD', '#6B7280'))
            self._badge_plan.setText(label_txt)
            self._badge_plan.setStyleSheet(
                f"background: {couleur}; color: white; border-radius: 4px; "
                f"padding: 3px 10px; font-weight: bold; font-size: 10pt;"
            )

            statut = statut_expiration()
            bandeau = None

            if statut == 'grace':
                expire = db.get_parametre('licence_expire', '')
                bandeau = QFrame()
                bandeau.setStyleSheet("background-color: #F59E0B; color: white; padding: 6px;")
                bl = QHBoxLayout(bandeau)
                bl.setContentsMargins(20, 0, 20, 0)
                lbl = QLabel(
                    f"⚠️  Votre licence a expiré le {expire}. "
                    f"Renouvelez dans les 7 jours pour continuer à vendre."
                )
                lbl.setStyleSheet("color: white; font-weight: bold; font-size: 10pt;")
                bl.addWidget(lbl)
            elif statut == 'demo':
                infos = demo_infos()
                bandeau = QFrame()
                bandeau.setStyleSheet("background-color: #3B82F6; color: white; padding: 6px;")
                bl = QHBoxLayout(bandeau)
                bl.setContentsMargins(20, 0, 12, 0)
                lbl = QLabel(
                    f"🔵  Mode DÉMONSTRATION — "
                    f"{infos['ventes_utilisees']}/{infos['ventes_max']} ventes utilisées — "
                    f"{infos['jours_restants']} jour(s) restant(s)."
                )
                lbl.setStyleSheet("color: white; font-size: 10pt;")
                bl.addWidget(lbl)
                bl.addStretch()
                btn_plans = QPushButton("📋 Voir les plans")
                btn_plans.setStyleSheet(
                    "QPushButton { background: white; color: #3B82F6; border: none;"
                    " border-radius: 4px; padding: 4px 14px; font-weight: bold; font-size: 10pt; }"
                    "QPushButton:hover { background: #F3F4F6; }"
                )
                btn_plans.setCursor(Qt.PointingHandCursor)
                btn_plans.clicked.connect(self.ouvrir_plans)
                bl.addWidget(btn_plans)

            if bandeau is not None:
                central = self.centralWidget()
                if central and central.layout():
                    central.layout().insertWidget(0, bandeau)
                self._bandeau_widget = bandeau

        except Exception:
            pass
