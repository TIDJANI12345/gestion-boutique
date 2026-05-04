"""
Dashboard principal (patron/admin) - PySide6
Graphiques, stats, actions rapides, session timeout.
"""
import sys
from datetime import datetime

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QMessageBox, QMenuBar, QMenu,
    QStatusBar, QComboBox, QTextEdit, QSplitter, QFileDialog
)
from PySide6.QtCore import Qt, QTimer, Signal, QThread
from PySide6.QtGui import QFont, QShortcut, QKeySequence, QAction

from config import APP_NAME, APP_VERSION, WINDOW_WIDTH, WINDOW_HEIGHT
from ui.theme import Theme
from modules.fiscalite import get_devise

# Matplotlib avec backend Qt
try:
    import matplotlib
    matplotlib.use('QtAgg')
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
    MATPLOTLIB_DISPONIBLE = True
except ImportError:
    MATPLOTLIB_DISPONIBLE = False


class UpdateCheckerThread(QThread):
    """Thread pour vérifier les MAJ sans bloquer l'interface"""
    finished = Signal(bool, object)  # (nouvelle_dispo, infos)

    def __init__(self, version_actuelle):
        super().__init__()
        self.version_actuelle = version_actuelle

    def run(self):
        from modules.updater import Updater
        nouvelle_dispo, infos = Updater.verifier_mise_a_jour(self.version_actuelle)
        self.finished.emit(nouvelle_dispo, infos)


class CarteStatistique(QFrame):
    """Widget carte de statistique (ventes, CA, alertes)."""

    def __init__(self, titre: str, valeur: str, couleur: str, parent=None):
        super().__init__(parent)
        self._couleur = couleur
        self.setProperty("role", "card")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)

        self._titre = QLabel(titre)
        self._titre.setStyleSheet(f"color: {Theme.c('text_secondary')}; font-size: 12px;")
        layout.addWidget(self._titre)

        self._valeur = QLabel(valeur)
        self._valeur.setFont(QFont("Segoe UI", 22, QFont.Bold))
        self._valeur.setStyleSheet(f"color: {couleur};")
        layout.addWidget(self._valeur)

    def set_valeur(self, text: str):
        self._valeur.setText(text)

    def refresh_theme(self):
        self._titre.setStyleSheet(f"color: {Theme.c('text_secondary')}; font-size: 12px;")


class BoutonAction(QPushButton):
    """Bouton d'action rapide du dashboard."""

    def __init__(self, texte: str, couleur: str, parent=None):
        super().__init__(texte, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.setMinimumHeight(55)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {couleur};
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {_darken(couleur)};
            }}
        """)


def _darken(hex_color: str) -> str:
    """Assombrir une couleur hex."""
    h = hex_color.lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f'#{max(0,r-25):02x}{max(0,g-25):02x}{max(0,b-25):02x}'


class PrincipaleWindow(QMainWindow):
    """Fenetre principale - Dashboard admin."""

    session_expiree = Signal()
    deconnexion_demandee = Signal()

    def __init__(self, utilisateur: dict, parent=None):
        super().__init__(parent)
        self.utilisateur = utilisateur

        # Titre : white label si activé
        try:
            from modules.features import peut
            from database import db
            if peut('white_label'):
                titre = db.get_parametre('boutique_nom', APP_NAME)
            else:
                titre = f"{APP_NAME} - {utilisateur['nom']} ({utilisateur['role'].upper()})"
        except Exception:
            titre = f"{APP_NAME} - {utilisateur['nom']} ({utilisateur['role'].upper()})"
        self.setWindowTitle(titre)

        self.setMinimumSize(1024, 600)
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)

        self._setup_menubar()
        self._setup_ui()
        self._afficher_bandeau_statut()
        self._setup_raccourcis()
        self._setup_session_timeout()

        # Premier chargement
        self.actualiser_stats()

        # Actualisation periodique (10s)
        self._timer_refresh = QTimer(self)
        self._timer_refresh.setInterval(10000)
        self._timer_refresh.timeout.connect(self.actualiser_stats)
        self._timer_refresh.start()

        self.statusBar().showMessage("Pret")

    # === MENU ===

    def _setup_menubar(self):
        menubar = self.menuBar()

        # Fichier
        menu_fichier = menubar.addMenu("Fichier")
        action_quitter = QAction("Quitter", self)
        action_quitter.triggered.connect(self.close)
        menu_fichier.addAction(action_quitter)

        # Administration (patron uniquement)
        if self.utilisateur.get('role') == 'patron':
            menu_admin = menubar.addMenu("Administration")

            for label, slot in [
                ("Gestion utilisateurs", self.ouvrir_utilisateurs),
                ("Parametres caisse", self.ouvrir_preferences_caisse),
                ("Modes de paiement", self.ouvrir_parametres_paiement),
                ("Categories produits", self.ouvrir_categories),
                ("Synchronisation", self.ouvrir_sync),
                ("Parametres fiscaux", self.ouvrir_parametres_fiscaux),
                ("Gestion clients", self.ouvrir_clients),
            ]:
                action = QAction(label, self)
                action.triggered.connect(slot)
                menu_admin.addAction(action)

            menu_admin.addSeparator()

            # Caisse (Pro)
            try:
                from modules.features import peut
                if peut('session_caisse'):
                    menu_caisse = menu_admin.addMenu("Caisse")
                    for label, slot in [
                        ("Ouvrir la caisse", self.ouvrir_caisse),
                        ("Clôture Z", self.cloturer_z),
                        ("Historique clôtures", self.historique_clotures),
                    ]:
                        a = QAction(label, self)
                        a.triggered.connect(slot)
                        menu_caisse.addAction(a)
                    menu_admin.addSeparator()

                if peut('credit_client'):
                    menu_ardoise = menu_admin.addMenu("Ardoise (Crédit)")
                    a = QAction("Gérer les ardoises", self)
                    a.triggered.connect(self.ouvrir_ardoise)
                    menu_ardoise.addAction(a)
                    menu_admin.addSeparator()
            except Exception:
                pass

            for label, slot in [
                ("Logs d'audit", self.ouvrir_logs_audit),
                ("Sauvegarde & Restauration", self.sauvegarder),
            ]:
                action = QAction(label, self)
                action.triggered.connect(slot)
                menu_admin.addAction(action)

        # Aide
        menu_aide = menubar.addMenu("Aide")

        action_verifier_maj = QAction("🔄 Vérifier les mises à jour", self)
        action_verifier_maj.triggered.connect(self.verifier_mises_a_jour_manuel)
        menu_aide.addAction(action_verifier_maj)

        menu_aide.addSeparator()

        action_apropos = QAction("A propos", self)
        action_apropos.triggered.connect(self.ouvrir_a_propos)
        menu_aide.addAction(action_apropos)

    # === INTERFACE ===

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # En-tete
        header = QFrame()
        header.setFixedHeight(70)
        header.setStyleSheet(f"background-color: {Theme.c('primary')};")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)

        titre = QLabel(f"  {APP_NAME}")
        titre.setFont(QFont("Segoe UI", 22, QFont.Bold))
        titre.setStyleSheet("color: white; background: transparent;")
        header_layout.addWidget(titre)

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

        # Info session
        session_label = QLabel(
            f"{self.utilisateur['prenom']} {self.utilisateur['nom']} "
            f"({self.utilisateur['role'].upper()})"
        )
        session_label.setStyleSheet("color: white; font-size: 11px; background: transparent;")
        header_layout.addWidget(session_label)

        # Bouton theme
        self._btn_theme = QPushButton(self._label_theme())
        self._btn_theme.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.2); color: white;
                border: 1px solid rgba(255,255,255,0.3); border-radius: 4px;
                padding: 6px 12px; font-size: 11px;
            }
            QPushButton:hover { background: rgba(255,255,255,0.3); }
        """)
        self._btn_theme.clicked.connect(self._basculer_theme)
        header_layout.addWidget(self._btn_theme)

        # Bouton deconnexion
        btn_deconnexion = QPushButton("Deconnexion")
        btn_deconnexion.setStyleSheet("""
            QPushButton {
                background: rgba(239,68,68,0.8); color: white;
                border: none; border-radius: 4px;
                padding: 6px 12px; font-size: 11px; font-weight: bold;
            }
            QPushButton:hover { background: rgba(239,68,68,1.0); }
        """)
        btn_deconnexion.setCursor(Qt.PointingHandCursor)
        btn_deconnexion.clicked.connect(self._deconnexion)
        header_layout.addWidget(btn_deconnexion)

        main_layout.addWidget(header)

        # Contenu scrollable
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 15, 20, 15)
        content_layout.setSpacing(12)

        # === Cartes statistiques ===
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(12)

        self.carte_ventes = CarteStatistique(
            "Ventes du jour", "0", Theme.c('primary'))
        self.carte_ca = CarteStatistique(
            "Chiffre d'affaires", f"0 {get_devise()}", Theme.c('success'))
        self.carte_alertes = CarteStatistique(
            "Alertes stock", "0", Theme.c('danger'))

        stats_layout.addWidget(self.carte_ventes)
        stats_layout.addWidget(self.carte_ca)
        stats_layout.addWidget(self.carte_alertes)
        content_layout.addLayout(stats_layout)

        # Ligne de comparaison
        self._label_comparaison = QLabel("")
        self._label_comparaison.setStyleSheet("font-size: 11px; font-weight: bold;")
        content_layout.addWidget(self._label_comparaison)

        # === Actions rapides ===
        actions_label = QLabel("Actions rapides")
        actions_label.setFont(QFont("Segoe UI", 13, QFont.Bold))
        content_layout.addWidget(actions_label)

        actions_grid = QGridLayout()
        actions_grid.setSpacing(8)

        c = Theme.couleurs()
        boutons = [
            ("F1  Nouvelle vente", c['primary'], self.ouvrir_ventes, 0, 0),
            ("F2  Produits", c['success'], self.ouvrir_produits, 0, 1),
            ("F3  Liste des ventes", c['purple'], self.ouvrir_liste_ventes, 0, 2),
            ("F4  Rapports", c['info'], self.ouvrir_rapports, 1, 0),
            ("F6  Export WhatsApp", c['warning'], self.ouvrir_whatsapp, 1, 1),
            ("F7  Clients", c['info'], self.ouvrir_clients, 1, 2),
            # ("F8  Import WhatsApp", c['primary'], self.ouvrir_import_whatsapp, 2, 0),  # TODO: Activer plus tard
        ]

        self._boutons_actions = {}
        for texte, couleur, slot, row, col in boutons:
            btn = BoutonAction(texte, couleur)
            btn.clicked.connect(slot)
            actions_grid.addWidget(btn, row, col)
            self._boutons_actions[texte] = btn

        # Cacher rapports/produits pour les caissiers
        if self.utilisateur.get('role') == 'caissier':
            self._boutons_actions.get("F4  Rapports", QPushButton()).hide()
            self._boutons_actions.get("F2  Produits", QPushButton()).hide()

        self._appliquer_restrictions_plan()
        content_layout.addLayout(actions_grid)

        # === Section inferieure : Graphique + Listes ===
        splitter = QSplitter(Qt.Horizontal)

        # Gauche : Graphique
        chart_panel = QFrame()
        chart_panel.setProperty("role", "card")
        chart_layout = QVBoxLayout(chart_panel)
        chart_layout.setContentsMargins(15, 12, 15, 12)

        chart_header = QHBoxLayout()
        chart_title = QLabel("Ventes")
        chart_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        chart_header.addWidget(chart_title)

        self._combo_periode = QComboBox()
        self._combo_periode.addItems(["Jour", "Semaine", "Mois"])
        self._combo_periode.setCurrentIndex(1)
        self._combo_periode.currentTextChanged.connect(
            lambda: self._dessiner_graphique()
        )
        chart_header.addStretch()
        chart_header.addWidget(self._combo_periode)
        chart_layout.addLayout(chart_header)

        self._chart_container = QVBoxLayout()
        chart_layout.addLayout(self._chart_container)

        splitter.addWidget(chart_panel)

        # Droite : Dernieres ventes + Stock faible
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        # Dernieres ventes
        ventes_frame = self._creer_panel("Dernieres ventes")
        self._text_ventes = QTextEdit()
        self._text_ventes.setReadOnly(True)
        self._text_ventes.setMaximumHeight(140)
        self._text_ventes.setProperty("role", "panel-text")
        ventes_frame.layout().addWidget(self._text_ventes)
        right_layout.addWidget(ventes_frame)

        # Stock faible
        stock_frame = self._creer_panel("Stock faible")
        self._text_stock = QTextEdit()
        self._text_stock.setReadOnly(True)
        self._text_stock.setMaximumHeight(140)
        self._text_stock.setProperty("role", "panel-text")
        stock_frame.layout().addWidget(self._text_stock)
        right_layout.addWidget(stock_frame)

        right_layout.addStretch()
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        content_layout.addWidget(splitter, 1)

        main_layout.addWidget(content, 1)

        # Footer raccourcis
        self._footer = QFrame()
        self._footer.setFixedHeight(28)
        self._footer.setProperty("role", "footer-bar")
        footer_layout = QHBoxLayout(self._footer)
        footer_layout.setContentsMargins(10, 0, 10, 0)
        self._footer_label = QLabel(
            "F1=Nouvelle vente | F2=Produits | F3=Ventes | "
            "F4=Rapports | F5=Actualiser | F6=WhatsApp | F7=Clients"
        )
        self._footer_label.setStyleSheet(
            f"color: {Theme.c('gray')}; font-size: 9px;"
        )
        self._footer_label.setAlignment(Qt.AlignCenter)
        footer_layout.addWidget(self._footer_label)
        main_layout.addWidget(self._footer)

    def _creer_panel(self, titre: str) -> QFrame:
        panel = QFrame()
        panel.setProperty("role", "card")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 12, 15, 12)
        lbl = QLabel(titre)
        lbl.setFont(QFont("Segoe UI", 12, QFont.Bold))
        layout.addWidget(lbl)
        return panel

    # === RACCOURCIS ===

    def _setup_raccourcis(self):
        raccourcis = [
            ("F1", self.ouvrir_ventes),
            ("F2", self.ouvrir_produits),
            ("F3", self.ouvrir_liste_ventes),
            ("F4", self.ouvrir_rapports),
            ("F5", self.actualiser_stats),
            ("F6", self.ouvrir_whatsapp),
            ("F7", self.ouvrir_clients),
            # ("F8", self.ouvrir_import_whatsapp),  # TODO: Activer plus tard
        ]
        for key, slot in raccourcis:
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.activated.connect(slot)

    # === GRAPHIQUE ===

    def _dessiner_graphique(self):
        # Vider le conteneur
        while self._chart_container.count():
            item = self._chart_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not MATPLOTLIB_DISPONIBLE:
            lbl = QLabel("matplotlib non installe")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(f"color: {Theme.c('gray')};")
            self._chart_container.addWidget(lbl)
            return

        from modules.rapports import Rapport

        periodes = {"Jour": "jour", "Semaine": "semaine", "Mois": "mois"}
        periode = periodes.get(self._combo_periode.currentText(), "semaine")
        data = Rapport.donnees_graphique_ventes(periode)

        if not data:
            lbl = QLabel("Pas de donnees pour cette periode")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(f"color: {Theme.c('gray')}; font-size: 12px;")
            self._chart_container.addWidget(lbl)
            return

        labels = [d[0] for d in data]
        values = [d[1] for d in data]

        bg = Theme.c('card_bg')
        text_c = Theme.c('text')
        bar_c = Theme.c('primary')
        sep_c = Theme.c('separator')

        fig = Figure(figsize=(5, 2.5), dpi=100)
        fig.patch.set_facecolor(bg)

        ax = fig.add_subplot(111)
        ax.set_facecolor(bg)
        ax.bar(labels, values, color=bar_c, width=0.6)
        ax.set_ylabel(f'CA ({get_devise()})', color=text_c, fontsize=9)
        ax.tick_params(colors=text_c, labelsize=8)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_color(sep_c)
        ax.spines['left'].set_color(sep_c)
        ax.yaxis.set_major_formatter(
            matplotlib.ticker.FuncFormatter(lambda x, _: f'{x:,.0f}')
        )
        fig.tight_layout()

        canvas = FigureCanvasQTAgg(fig)
        self._chart_container.addWidget(canvas)

    # === STATISTIQUES ===

    def actualiser_stats(self):
        try:
            from modules.rapports import Rapport
            from modules.produits import Produit

            stats = Rapport.statistiques_generales()

            self.carte_ventes.set_valeur(str(stats['nb_ventes']))
            self.carte_ca.set_valeur(f"{stats['ca_jour']:,.0f} {get_devise()}")

            produits_alerte = Produit.obtenir_stock_faible()
            self.carte_alertes.set_valeur(str(len(produits_alerte)))

            # Comparaison vs hier
            try:
                comp = Rapport.comparaison_jour_precedent()
                variation = comp['variation_ca_pct']
                signe = "+" if variation >= 0 else ""
                couleur = Theme.c('success') if variation >= 0 else Theme.c('danger')
                fleche = "^" if variation >= 0 else "v"
                self._label_comparaison.setText(
                    f"{fleche} {signe}{variation:.0f}% vs hier  |  "
                    f"CA mois: {stats['ca_mois']:,.0f} {get_devise()}"
                )
                self._label_comparaison.setStyleSheet(
                    f"color: {couleur}; font-size: 11px; font-weight: bold;"
                )
            except Exception:
                pass

            # Dernieres ventes
            from modules.ventes import Vente
            ventes_jour = Vente.obtenir_ventes_du_jour()
            if not ventes_jour:
                self._text_ventes.setPlainText("Aucune vente aujourd'hui")
            else:
                lines = []
                for v in ventes_jour[:5]:
                    numero = v[1] if len(v) > 1 else "N/A"
                    total = v[3] if len(v) > 3 else 0
                    lines.append(f"  {numero}: {total:,.0f} {get_devise()}")
                self._text_ventes.setPlainText("\n".join(lines))

            # Stock faible
            if not produits_alerte:
                self._text_stock.setPlainText("Tous les stocks sont OK")
            else:
                lines = []
                for p in produits_alerte[:5]:
                    lines.append(f"  {p[1]}: Stock {p[5]}")
                self._text_stock.setPlainText("\n".join(lines))

            # Graphique
            self._dessiner_graphique()

        except Exception as e:
            pass

    # === RESTRICTIONS PAR PLAN ===

    def _appliquer_restrictions_plan(self):
        """Grise les fonctionnalités Pro non disponibles sur le plan actuel."""
        try:
            from modules.features import peut, plan_actuel
        except Exception:
            return

        _MSG_PRO = "Disponible en offre Pro — contactez votre revendeur"
        _STYLE_VERROU = """
            QPushButton {
                background-color: #9CA3AF;
                color: white; border: none; border-radius: 6px;
                font-weight: bold; font-size: 13px;
            }
        """

        # Clients & fidélité
        btn_clients = self._boutons_actions.get("F7  Clients")
        if btn_clients and not peut('clients_fidelite'):
            btn_clients.setEnabled(False)
            btn_clients.setText("🔒  Clients  [Pro]")
            btn_clients.setStyleSheet(_STYLE_VERROU)
            btn_clients.setToolTip(_MSG_PRO)

        # Exports (dans les menus)
        try:
            for action in self.menuBar().actions():
                menu = action.menu()
                if not menu:
                    continue
                for sub in menu.actions():
                    if 'export' in sub.text().lower() or 'sauvegarde' in sub.text().lower():
                        feature = 'exports' if 'export' in sub.text().lower() else 'sauvegarde_auto'
                        if not peut(feature):
                            sub.setEnabled(False)
                            sub.setText(sub.text() + "  [Pro]")
        except Exception:
            pass

        # Badge plan dans le header (coin droit)
        plan = plan_actuel()
        badges = {
            'demo':        ('DÉMO', '#3B82F6'),
            'standard':    ('STANDARD', '#6B7280'),
            'pro':         ('PRO', '#10B981'),
            'white_label': ('PRO', '#10B981'),
        }
        label_txt, couleur = badges.get(plan, ('STANDARD', '#6B7280'))
        try:
            self._badge_plan.setText(label_txt)
            self._badge_plan.setStyleSheet(
                f"background: {couleur}; color: white; border-radius: 4px; "
                f"padding: 3px 10px; font-weight: bold; font-size: 10pt;"
            )
        except Exception:
            pass

    # === BANDEAU STATUT LICENCE ===

    def _afficher_bandeau_statut(self):
        """Affiche un bandeau si licence en grace period ou mode démo."""
        try:
            from modules.features import statut_expiration, est_demo, demo_infos
            from database import db
            from PySide6.QtWidgets import QLabel, QFrame, QHBoxLayout

            statut = statut_expiration()

            if statut == 'grace':
                expire = db.get_parametre('licence_expire', '')
                bandeau = QFrame()
                bandeau.setStyleSheet(
                    "background-color: #F59E0B; color: white; padding: 6px;"
                )
                bl = QHBoxLayout(bandeau)
                bl.setContentsMargins(20, 0, 20, 0)
                lbl = QLabel(
                    f"⚠️  Votre licence a expiré le {expire}. "
                    f"Renouvelez dans les 7 jours pour continuer à vendre."
                )
                lbl.setStyleSheet("color: white; font-weight: bold; font-size: 10pt;")
                bl.addWidget(lbl)
                # Insérer sous la barre de menus
                central = self.centralWidget()
                if central and central.layout():
                    central.layout().insertWidget(0, bandeau)

            elif statut == 'demo':
                infos = demo_infos()
                bandeau = QFrame()
                bandeau.setStyleSheet(
                    "background-color: #3B82F6; color: white; padding: 6px;"
                )
                bl = QHBoxLayout(bandeau)
                bl.setContentsMargins(20, 0, 20, 0)
                lbl = QLabel(
                    f"🔵  Mode DÉMONSTRATION — "
                    f"{infos['ventes_utilisees']}/{infos['ventes_max']} ventes utilisées — "
                    f"{infos['jours_restants']} jour(s) restant(s). "
                    f"Activez une licence pour débloquer toutes les fonctionnalités."
                )
                lbl.setStyleSheet("color: white; font-size: 10pt;")
                bl.addWidget(lbl)
                central = self.centralWidget()
                if central and central.layout():
                    central.layout().insertWidget(0, bandeau)

        except Exception:
            pass

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

    def _deconnexion(self):
        try:
            from modules.audit import enregistrer_action
            enregistrer_action(
                self.utilisateur['id'], 'deconnexion',
                'Session terminee par l\'utilisateur'
            )
        except Exception:
            pass
        self._timer_refresh.stop()
        self.deconnexion_demandee.emit()
        self.close()

    def _on_session_expired(self):
        self._timer_refresh.stop()
        QMessageBox.information(
            self, "Session expiree",
            "Vous avez ete deconnecte pour inactivite."
        )
        self.session_expiree.emit()
        self.close()

    # === THEME ===

    @staticmethod
    def _label_theme() -> str:
        return "☾ Sombre" if not Theme.est_sombre() else "☀ Clair"

    def _basculer_theme(self):
        Theme.basculer()
        self._btn_theme.setText(self._label_theme())
        self._footer_label.setStyleSheet(f"color: {Theme.c('gray')}; font-size: 9px;")
        self.carte_ventes.refresh_theme()
        self.carte_ca.refresh_theme()
        self.carte_alertes.refresh_theme()
        self._dessiner_graphique()
        self.update()

    # === OUVERTURE FENETRES ===
    # Les fenetres non encore migrees afficheront un message temporaire.
    # Elles seront connectees au fur et a mesure des phases suivantes.

    def ouvrir_ventes(self):
        from ui.windows.ventes import VentesWindow
        dlg = VentesWindow(parent=self, utilisateur=self.utilisateur)
        dlg.vente_terminee.connect(self.actualiser_stats)
        dlg.exec()

    def ouvrir_produits(self):
        from ui.windows.produits import ProduitsWindow
        dlg = ProduitsWindow(parent=self)
        dlg.exec()

    def ouvrir_liste_ventes(self):
        from ui.windows.liste_ventes import ListeVentesWindow
        dlg = ListeVentesWindow(parent=self, utilisateur=self.utilisateur)
        dlg.exec()

    def ouvrir_rapports(self):
        if self.utilisateur.get('role') != 'patron':
            QMessageBox.warning(self, "Acces refuse", "Reserve a l'administrateur")
            return
        from ui.windows.rapports import RapportsWindow
        dlg = RapportsWindow(parent=self)
        dlg.exec()

    def ouvrir_clients(self):
        from ui.windows.clients import ClientsWindow
        dlg = ClientsWindow(parent=self)
        dlg.exec()

    def ouvrir_whatsapp(self):
        from ui.windows.whatsapp import WhatsAppWindow
        dlg = WhatsAppWindow(parent=self)
        dlg.exec()

    # TODO: Activer plus tard
    # def ouvrir_import_whatsapp(self):
    #     from ui.windows.import_whatsapp import ImportWhatsAppWindow
    #     dlg = ImportWhatsAppWindow(parent=self)
    #     if dlg.exec():
    #         self.actualiser_stats()

    def ouvrir_a_propos(self):
        from ui.windows.a_propos import AProposWindow
        dlg = AProposWindow(parent=self)
        dlg.exec()

    def verifier_mises_a_jour_manuel(self):
        """Vérification manuelle des mises à jour (menu Aide)"""
        from ui.dialogs.update_notification import UpdateNotificationDialog
        from config import APP_VERSION
        from PySide6.QtWidgets import QMessageBox

        # Afficher "Vérification en cours..."
        self.progress_dialog = QMessageBox(self)
        self.progress_dialog.setWindowTitle("Vérification")
        self.progress_dialog.setText("⏳ Vérification des mises à jour en cours...\n\nVeuillez patienter.")
        self.progress_dialog.setStandardButtons(QMessageBox.NoButton)
        self.progress_dialog.show()

        # Lancer vérification en arrière-plan (non bloquant)
        self.update_thread = UpdateCheckerThread(APP_VERSION)
        self.update_thread.finished.connect(self._on_update_check_finished)
        self.update_thread.start()

    def _on_update_check_finished(self, nouvelle_dispo, infos):
        """Callback quand vérification MAJ terminée"""
        from ui.dialogs.update_notification import UpdateNotificationDialog
        from config import APP_VERSION
        from PySide6.QtWidgets import QMessageBox

        # Fermer dialog de chargement
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.close()

        if nouvelle_dispo and infos:
            # Afficher le dialog de notification (même si version ignorée)
            dialog = UpdateNotificationDialog(infos, self)
            dialog.exec()
        else:
            # Aucune mise à jour disponible
            QMessageBox.information(
                self, "À jour ✅",
                f"<h3>Vous utilisez la dernière version !</h3>"
                f"<p><b>Version actuelle :</b> {APP_VERSION}</p>"
                f"<br>"
                f"<p>Aucune mise à jour disponible pour le moment.</p>"
            )

    def ouvrir_utilisateurs(self):
        from ui.windows.utilisateurs import UtilisateursWindow
        dlg = UtilisateursWindow(self.utilisateur, parent=self)
        dlg.exec()

    def ouvrir_sync(self):
        from ui.windows.config_sync import ConfigSyncWindow
        dlg = ConfigSyncWindow(parent=self)
        dlg.exec()

    def ouvrir_preferences_caisse(self):
        from ui.windows.preferences_caisse import PreferencesCaisseWindow
        dlg = PreferencesCaisseWindow(parent=self)
        dlg.exec()

    def ouvrir_parametres_paiement(self):
        from ui.windows.parametres_paiement import ParametresPaiementWindow
        dlg = ParametresPaiementWindow(parent=self)
        dlg.exec()

    def ouvrir_categories(self):
        from ui.windows.gestion_categories import GestionCategoriesWindow
        dlg = GestionCategoriesWindow(parent=self)
        dlg.exec()

    def ouvrir_parametres_fiscaux(self):
        from ui.windows.parametres_fiscaux import ParametresFiscauxWindow
        dlg = ParametresFiscauxWindow(parent=self)
        dlg.exec()

    def ouvrir_logs_audit(self):
        """Ouvrir la fenetre de consultation des logs d'audit"""
        from ui.windows.logs_audit import LogsAuditWindow
        dlg = LogsAuditWindow(self.utilisateur, parent=self)
        dlg.exec()

    def _fenetre_non_migree(self, nom: str):
        QMessageBox.information(
            self, "En construction",
            f"La fenetre '{nom}' sera disponible apres sa migration vers PySide6."
        )

    # === SESSION CAISSE ===

    def ouvrir_caisse(self):
        try:
            from modules.sessions import session_actuelle
            if session_actuelle():
                QMessageBox.information(self, "Info", "Une session est déjà ouverte.")
                return
            from ui.dialogs.ouverture_caisse import OuvertureCaisseDialog
            dlg = OuvertureCaisseDialog(self.utilisateur, self)
            dlg.exec()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))

    def cloturer_z(self):
        try:
            from modules.sessions import session_actuelle
            if not session_actuelle():
                QMessageBox.information(self, "Info", "Aucune session ouverte à clôturer.")
                return
            from ui.dialogs.cloture_z import ClotureZDialog
            dlg = ClotureZDialog(self.utilisateur, self)
            dlg.cloture_effectuee.connect(lambda _: self.actualiser_stats())
            dlg.exec()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))

    def historique_clotures(self):
        try:
            from modules.sessions import historique_clotures
            from PySide6.QtWidgets import QDialog, QTableWidget, QTableWidgetItem, QHeaderView, QVBoxLayout
            clotures = historique_clotures()
            dlg = QDialog(self)
            dlg.setWindowTitle("Historique des clôtures Z")
            dlg.resize(800, 400)
            layout = QVBoxLayout(dlg)
            table = QTableWidget(len(clotures), 7)
            table.setHorizontalHeaderLabels(
                ["Date clôture", "Caisse", "Caissier", "Nb ventes",
                 "Total", "Écart", "Hash Z"]
            )
            table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            table.setEditTriggers(QTableWidget.NoEditTriggers)
            devise = 'FCFA'
            try:
                from modules.fiscalite import get_devise
                devise = get_devise()
            except Exception:
                pass
            for i, c in enumerate(clotures):
                table.setItem(i, 0, QTableWidgetItem(c.get('date_cloture', '')))
                table.setItem(i, 1, QTableWidgetItem(c.get('id_caisse', '')))
                table.setItem(i, 2, QTableWidgetItem(c.get('caissier_nom', '')))
                table.setItem(i, 3, QTableWidgetItem(str(c.get('nb_ventes', 0))))
                table.setItem(i, 4, QTableWidgetItem(f"{c.get('total_general', 0):,} {devise}"))
                ecart = c.get('ecart', 0)
                item_ecart = QTableWidgetItem(f"{ecart:+,} {devise}")
                item_ecart.setForeground(
                    __import__('PySide6.QtGui', fromlist=['QColor']).QColor(
                        '#10B981' if ecart == 0 else '#EF4444'
                    )
                )
                table.setItem(i, 5, item_ecart)
                table.setItem(i, 6, QTableWidgetItem(c.get('hash_cloture', '')))
            layout.addWidget(table)
            dlg.exec()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))

    # === ARDOISE ===

    def ouvrir_ardoise(self):
        from ui.windows.ardoise import ArdoiseWindow
        dlg = ArdoiseWindow(self)
        dlg.exec()

    # === SAUVEGARDE / RESTAURATION ===

    def sauvegarder(self):
        from ui.windows.sauvegarde import SauvegardeWindow
        dlg = SauvegardeWindow(self)
        dlg.exec()
        self.actualiser_stats()

    def restaurer(self):
        self.sauvegarder()

    def exporter_zip(self):
        self.sauvegarder()

    def importer_zip(self):
        self.sauvegarder()
