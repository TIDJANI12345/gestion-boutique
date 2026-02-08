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
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont, QShortcut, QKeySequence, QAction

from config import APP_NAME, APP_VERSION, WINDOW_WIDTH, WINDOW_HEIGHT
from ui.theme import Theme

# Matplotlib avec backend Qt
try:
    import matplotlib
    matplotlib.use('QtAgg')
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
    MATPLOTLIB_DISPONIBLE = True
except ImportError:
    MATPLOTLIB_DISPONIBLE = False


class CarteStatistique(QFrame):
    """Widget carte de statistique (ventes, CA, alertes)."""

    def __init__(self, titre: str, valeur: str, couleur: str, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            CarteStatistique {{
                background-color: {Theme.c('card_bg')};
                border: 1px solid {Theme.c('card_border')};
                border-radius: 8px;
            }}
        """)

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

    def __init__(self, utilisateur: dict, parent=None):
        super().__init__(parent)
        self.utilisateur = utilisateur
        self.setWindowTitle(
            f"{APP_NAME} - {utilisateur['nom']} ({utilisateur['role'].upper()})"
        )
        self.setMinimumSize(1024, 600)
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)

        self._setup_menubar()
        self._setup_ui()
        self._setup_raccourcis()
        self._setup_session_timeout()

        # Premier chargement
        self.actualiser_stats()

        # Actualisation periodique (10s)
        self._timer_refresh = QTimer(self)
        self._timer_refresh.setInterval(10000)
        self._timer_refresh.timeout.connect(self.actualiser_stats)
        self._timer_refresh.start()

        # Sauvegarde auto
        try:
            from modules.sauvegarde import planifier_sauvegarde_auto
            planifier_sauvegarde_auto()
        except Exception:
            pass

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
                ("Synchronisation", self.ouvrir_sync),
                ("Parametres fiscaux", self.ouvrir_parametres_fiscaux),
                ("Gestion clients", self.ouvrir_clients),
            ]:
                action = QAction(label, self)
                action.triggered.connect(slot)
                menu_admin.addAction(action)

            menu_admin.addSeparator()

            for label, slot in [
                ("Logs d'audit", self.ouvrir_logs_audit),
                ("Sauvegarde", self.sauvegarder),
                ("Restaurer", self.restaurer),
            ]:
                action = QAction(label, self)
                action.triggered.connect(slot)
                menu_admin.addAction(action)

            menu_admin.addSeparator()

            for label, slot in [
                ("Exporter (ZIP)", self.exporter_zip),
                ("Importer (ZIP)", self.importer_zip),
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

        # Info session
        session_label = QLabel(
            f"{self.utilisateur['prenom']} {self.utilisateur['nom']} "
            f"({self.utilisateur['role'].upper()})"
        )
        session_label.setStyleSheet("color: white; font-size: 11px; background: transparent;")
        header_layout.addWidget(session_label)

        # Bouton theme
        btn_theme = QPushButton("Theme")
        btn_theme.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.2); color: white;
                border: 1px solid rgba(255,255,255,0.3); border-radius: 4px;
                padding: 6px 12px; font-size: 11px;
            }
            QPushButton:hover { background: rgba(255,255,255,0.3); }
        """)
        btn_theme.clicked.connect(self._basculer_theme)
        header_layout.addWidget(btn_theme)

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
            "Chiffre d'affaires", "0 FCFA", Theme.c('success'))
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

        content_layout.addLayout(actions_grid)

        # === Section inferieure : Graphique + Listes ===
        splitter = QSplitter(Qt.Horizontal)

        # Gauche : Graphique
        chart_panel = QFrame()
        chart_panel.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.c('card_bg')};
                border: 1px solid {Theme.c('card_border')};
                border-radius: 8px;
            }}
        """)
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
        self._text_ventes.setStyleSheet(
            f"border: none; background: {Theme.c('card_bg')}; font-size: 12px;"
        )
        ventes_frame.layout().addWidget(self._text_ventes)
        right_layout.addWidget(ventes_frame)

        # Stock faible
        stock_frame = self._creer_panel("Stock faible")
        self._text_stock = QTextEdit()
        self._text_stock.setReadOnly(True)
        self._text_stock.setMaximumHeight(140)
        self._text_stock.setStyleSheet(
            f"border: none; background: {Theme.c('card_bg')}; font-size: 12px;"
        )
        stock_frame.layout().addWidget(self._text_stock)
        right_layout.addWidget(stock_frame)

        right_layout.addStretch()
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        content_layout.addWidget(splitter, 1)

        main_layout.addWidget(content, 1)

        # Footer raccourcis
        footer = QFrame()
        footer.setFixedHeight(28)
        footer.setStyleSheet(
            f"background-color: {Theme.c('light')};"
        )
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(10, 0, 10, 0)
        footer_label = QLabel(
            "F1=Nouvelle vente | F2=Produits | F3=Ventes | "
            "F4=Rapports | F5=Actualiser | F6=WhatsApp | F7=Clients"
        )
        footer_label.setStyleSheet(
            f"color: {Theme.c('gray')}; font-size: 9px;"
        )
        footer_label.setAlignment(Qt.AlignCenter)
        footer_layout.addWidget(footer_label)
        main_layout.addWidget(footer)

    def _creer_panel(self, titre: str) -> QFrame:
        panel = QFrame()
        panel.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.c('card_bg')};
                border: 1px solid {Theme.c('card_border')};
                border-radius: 8px;
            }}
        """)
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
        ax.set_ylabel('CA (FCFA)', color=text_c, fontsize=9)
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
            self.carte_ca.set_valeur(f"{stats['ca_jour']:,.0f} FCFA")

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
                    f"CA mois: {stats['ca_mois']:,.0f} FCFA"
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
                    lines.append(f"  {numero}: {total:,.0f} FCFA")
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
            print(f"Erreur actualisation: {e}")

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

    # === THEME ===

    def _basculer_theme(self):
        Theme.basculer()
        QMessageBox.information(
            self, "Theme",
            "Theme modifie.\n\nRedemarrez l'application pour appliquer completement."
        )

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

    def ouvrir_a_propos(self):
        from ui.windows.a_propos import AProposWindow
        dlg = AProposWindow(parent=self)
        dlg.exec()

    def verifier_mises_a_jour_manuel(self):
        """Vérification manuelle des mises à jour (menu Aide)"""
        from modules.updater import Updater
        from ui.dialogs.update_notification import UpdateNotificationDialog
        from config import APP_VERSION
        from PySide6.QtWidgets import QMessageBox, QApplication

        # Afficher "Vérification en cours..."
        progress = QMessageBox(self)
        progress.setWindowTitle("Vérification")
        progress.setText("⏳ Vérification des mises à jour en cours...\n\nVeuillez patienter.")
        progress.setStandardButtons(QMessageBox.NoButton)
        progress.show()
        QApplication.processEvents()  # Forcer l'affichage

        # Vérifier les mises à jour
        nouvelle_dispo, infos = Updater.verifier_mise_a_jour(APP_VERSION)
        progress.close()

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

    # === SAUVEGARDE / RESTAURATION ===

    def sauvegarder(self):
        from modules.sauvegarde import sauvegarder_locale
        succes, message, chemin = sauvegarder_locale()
        if succes:
            QMessageBox.information(self, "Succes", f"Sauvegarde creee!\n\n{chemin}")
        else:
            QMessageBox.critical(self, "Erreur", f"Erreur de sauvegarde:\n{message}")

    def restaurer(self):
        from modules.sauvegarde import lister_sauvegardes, restaurer
        sauvegardes = lister_sauvegardes()
        if not sauvegardes:
            QMessageBox.information(self, "Info", "Aucune sauvegarde disponible.")
            return
        # Dialogue simplifie : choisir fichier .db directement
        chemin, _ = QFileDialog.getOpenFileName(
            self, "Selectionner une sauvegarde",
            "", "Base de donnees (*.db)"
        )
        if not chemin:
            return
        reponse = QMessageBox.question(
            self, "Confirmation",
            "Restaurer cette sauvegarde ?\n\n"
            "La base actuelle sera sauvegardee avant la restauration.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reponse == QMessageBox.Yes:
            succes, message = restaurer(chemin)
            if succes:
                QMessageBox.information(self, "Succes", message)
                self.actualiser_stats()
            else:
                QMessageBox.critical(self, "Erreur", message)

    def exporter_zip(self):
        from modules.sauvegarde import exporter_zip
        succes, message, chemin = exporter_zip()
        if succes:
            QMessageBox.information(self, "Succes", f"Export ZIP cree!\n\n{chemin}")
        else:
            QMessageBox.critical(self, "Erreur", message)

    def importer_zip(self):
        from modules.sauvegarde import importer_zip
        chemin, _ = QFileDialog.getOpenFileName(
            self, "Selectionner un fichier ZIP",
            "", "Fichiers ZIP (*.zip)"
        )
        if not chemin:
            return
        reponse = QMessageBox.question(
            self, "Confirmation",
            "Importer ce fichier?\n\n"
            "Les donnees actuelles seront sauvegardees puis remplacees.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reponse == QMessageBox.Yes:
            succes, message = importer_zip(chemin)
            if succes:
                QMessageBox.information(self, "Succes", message)
                self.actualiser_stats()
            else:
                QMessageBox.critical(self, "Erreur", message)
