"""
Fenetre Rapports - PySide6
5 onglets : Vue d'ensemble, Top Produits, Caisse, TVA, Stock Faible.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QWidget, QTabWidget, QGridLayout, QDateEdit, QScrollArea
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont

from ui.theme import Theme
from ui.components.table import BoutiqueTableView, BoutiqueTableModel
from ui.components.dialogs import information, erreur


class RapportsWindow(QDialog):
    """Fenetre de rapports et statistiques."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Rapports et Statistiques")
        self.setMinimumSize(1200, 700)
        self.setModal(True)

        self._setup_ui()
        self._actualiser()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # En-tete
        header = QFrame()
        header.setFixedHeight(60)
        header.setStyleSheet(f"background-color: {Theme.c('purple')};")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(30, 0, 30, 0)

        titre = QLabel("Rapports et Statistiques")
        titre.setFont(QFont("Segoe UI", 20, QFont.Bold))
        titre.setStyleSheet("color: white; background: transparent;")
        hl.addWidget(titre)
        hl.addStretch()

        btn_refresh = QPushButton("Actualiser")
        btn_refresh.setStyleSheet(
            "QPushButton { background-color: rgba(255,255,255,0.2); color: white; "
            "padding: 8px 16px; border-radius: 6px; font-weight: bold; }"
            "QPushButton:hover { background-color: rgba(255,255,255,0.3); }"
        )
        btn_refresh.clicked.connect(self._actualiser)
        hl.addWidget(btn_refresh)

        btn_export = QPushButton("Exporter Excel")
        btn_export.setStyleSheet(
            "QPushButton { background-color: rgba(255,255,255,0.2); color: white; "
            "padding: 8px 16px; border-radius: 6px; font-weight: bold; }"
            "QPushButton:hover { background-color: rgba(255,255,255,0.3); }"
        )
        btn_export.clicked.connect(self._exporter_excel)
        hl.addWidget(btn_export)

        layout.addWidget(header)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(
            f"QTabBar::tab {{ padding: 10px 20px; font-size: 12px; }}"
            f"QTabBar::tab:selected {{ font-weight: bold; }}"
        )

        self.tabs.addTab(self._creer_tab_overview(), "Vue d'ensemble")
        self.tabs.addTab(self._creer_tab_top_produits(), "Top Produits")
        self.tabs.addTab(self._creer_tab_caisse(), "Caisse")
        self.tabs.addTab(self._creer_tab_tva(), "TVA")
        self.tabs.addTab(self._creer_tab_stock(), "Stock Faible")

        layout.addWidget(self.tabs)

    # === TAB 1 : VUE D'ENSEMBLE ===

    def _creer_tab_overview(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(15)

        # Stats cards (2x3 grid)
        grid = QGridLayout()
        grid.setSpacing(12)

        self._cards_overview = {}
        cards_def = [
            ("ventes_jour", "Ventes aujourd'hui", Theme.c('primary')),
            ("ca_jour", "CA aujourd'hui", Theme.c('success')),
            ("stock_alertes", "Alertes stock", Theme.c('danger')),
            ("nb_ventes_total", "Total ventes", Theme.c('info')),
            ("ca_total", "CA total", Theme.c('purple')),
            ("valeur_stock", "Valeur stock", Theme.c('warning')),
        ]
        for i, (key, label, color) in enumerate(cards_def):
            card = self._creer_stat_card(label, "0", color)
            self._cards_overview[key] = card
            grid.addWidget(card, i // 3, i % 3)

        layout.addLayout(grid)

        # Chart placeholder
        self.chart_frame = QFrame()
        self.chart_frame.setMinimumHeight(300)
        self.chart_frame.setStyleSheet(
            f"QFrame {{ background: {Theme.c('card_bg')}; "
            f"border: 1px solid {Theme.c('card_border')}; border-radius: 8px; }}"
        )
        chart_layout = QVBoxLayout(self.chart_frame)
        chart_layout.setContentsMargins(15, 10, 15, 10)

        lbl_chart = QLabel("Evolution CA - 7 derniers jours")
        lbl_chart.setFont(QFont("Segoe UI", 12, QFont.Bold))
        chart_layout.addWidget(lbl_chart)

        self.chart_container = QVBoxLayout()
        chart_layout.addLayout(self.chart_container)

        layout.addWidget(self.chart_frame)
        layout.addStretch()

        scroll.setWidget(widget)
        return scroll

    def _creer_stat_card(self, label, value, color):
        card = QFrame()
        card.setFixedHeight(100)
        card.setStyleSheet(
            f"QFrame {{ background: {Theme.c('card_bg')}; "
            f"border: 1px solid {Theme.c('card_border')}; border-radius: 10px; "
            f"border-left: 4px solid {color}; }}"
        )
        cl = QVBoxLayout(card)
        cl.setContentsMargins(15, 10, 15, 10)

        lbl = QLabel(label)
        lbl.setFont(QFont("Segoe UI", 10))
        lbl.setStyleSheet(f"color: {Theme.c('gray')}; border: none;")
        cl.addWidget(lbl)

        val = QLabel(value)
        val.setFont(QFont("Segoe UI", 22, QFont.Bold))
        val.setStyleSheet(f"color: {color}; border: none;")
        val.setObjectName("card_value")
        cl.addWidget(val)

        return card

    def _maj_card(self, card, value):
        lbl = card.findChild(QLabel, "card_value")
        if lbl:
            lbl.setText(str(value))

    # === TAB 2 : TOP PRODUITS ===

    def _creer_tab_top_produits(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(12)

        # Chart area (bar chart)
        self.top_chart_frame = QFrame()
        self.top_chart_frame.setMinimumHeight(280)
        self.top_chart_frame.setStyleSheet(
            f"QFrame {{ background: {Theme.c('card_bg')}; "
            f"border: 1px solid {Theme.c('card_border')}; border-radius: 8px; }}"
        )
        top_chart_layout = QVBoxLayout(self.top_chart_frame)
        top_chart_layout.setContentsMargins(15, 10, 15, 10)
        lbl = QLabel("Top 10 Produits par quantite vendue")
        lbl.setFont(QFont("Segoe UI", 12, QFont.Bold))
        top_chart_layout.addWidget(lbl)
        self.top_chart_container = QVBoxLayout()
        top_chart_layout.addLayout(self.top_chart_container)
        layout.addWidget(self.top_chart_frame)

        # Table
        colonnes = ["Rang", "Produit", "Categorie", "Qte Vendue", "CA Genere (FCFA)"]
        self.top_model = BoutiqueTableModel(colonnes)
        self.top_table = BoutiqueTableView()
        self.top_table.setModel(self.top_model)
        layout.addWidget(self.top_table)

        return widget

    # === TAB 3 : CAISSE ===

    def _creer_tab_caisse(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(12)

        # Date selector
        date_bar = QHBoxLayout()
        date_bar.addWidget(QLabel("Date :"))
        self.caisse_date = QDateEdit()
        self.caisse_date.setCalendarPopup(True)
        self.caisse_date.setDate(QDate.currentDate())
        self.caisse_date.setDisplayFormat("dd/MM/yyyy")
        date_bar.addWidget(self.caisse_date)

        btn_voir = QPushButton("Voir")
        btn_voir.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.c('primary')}; color: white; "
            f"padding: 8px 16px; border-radius: 6px; font-weight: bold; }}"
        )
        btn_voir.clicked.connect(self._charger_caisse)
        date_bar.addWidget(btn_voir)
        date_bar.addStretch()
        layout.addLayout(date_bar)

        # Mode cards
        self.caisse_cards_layout = QHBoxLayout()
        self.caisse_cards_layout.setSpacing(12)
        self._caisse_cards = {}

        modes = [
            ("especes", "Especes", Theme.c('success')),
            ("orange_money", "Orange Money", "#FF6600"),
            ("mtn_momo", "MTN MoMo", "#FFCC00"),
            ("moov_money", "Moov Money", Theme.c('primary')),
        ]
        for key, label, color in modes:
            card = self._creer_stat_card(label, "0 FCFA", color)
            self._caisse_cards[key] = card
            self.caisse_cards_layout.addWidget(card)

        layout.addLayout(self.caisse_cards_layout)

        # Table
        colonnes = ["Mode", "Nb transactions", "Total (FCFA)"]
        self.caisse_model = BoutiqueTableModel(colonnes)
        self.caisse_table = BoutiqueTableView()
        self.caisse_table.setModel(self.caisse_model)
        layout.addWidget(self.caisse_table)

        # Total
        self.lbl_total_caisse = QLabel("Total general : 0 FCFA")
        self.lbl_total_caisse.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.lbl_total_caisse.setAlignment(Qt.AlignRight)
        layout.addWidget(self.lbl_total_caisse)

        return widget

    # === TAB 4 : TVA ===

    def _creer_tab_tva(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(12)

        # Status banner
        self.tva_banner = QLabel()
        self.tva_banner.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.tva_banner.setAlignment(Qt.AlignCenter)
        self.tva_banner.setFixedHeight(40)
        layout.addWidget(self.tva_banner)

        # Stats cards
        self.tva_cards_layout = QHBoxLayout()
        self.tva_cards_layout.setSpacing(12)
        self._tva_cards = {}
        for key, label, color in [
            ("ca_ttc", "CA TTC", Theme.c('primary')),
            ("ca_ht", "CA HT", Theme.c('info')),
            ("tva_collectee", "TVA collectee", Theme.c('success')),
        ]:
            card = self._creer_stat_card(label, "0 FCFA", color)
            self._tva_cards[key] = card
            self.tva_cards_layout.addWidget(card)
        layout.addLayout(self.tva_cards_layout)

        # Taux TVA par categorie
        layout.addWidget(QLabel("Taux TVA par categorie :"))
        colonnes = ["ID", "Categorie", "Taux (%)", "Description"]
        self.tva_model = BoutiqueTableModel(colonnes)
        self.tva_table = BoutiqueTableView()
        self.tva_table.setModel(self.tva_model)
        layout.addWidget(self.tva_table)

        return widget

    # === TAB 5 : STOCK FAIBLE ===

    def _creer_tab_stock(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(12)

        # Alert badge
        self.lbl_stock_alert = QLabel()
        self.lbl_stock_alert.setFont(QFont("Segoe UI", 13, QFont.Bold))
        layout.addWidget(self.lbl_stock_alert)

        # Table
        colonnes = ["Produit", "Categorie", "Stock actuel", "Seuil alerte", "Prix vente (FCFA)"]
        self.stock_model = BoutiqueTableModel(colonnes)
        self.stock_table = BoutiqueTableView()
        self.stock_table.setModel(self.stock_model)
        layout.addWidget(self.stock_table)

        return widget

    # === DATA LOADING ===

    def _actualiser(self):
        self._charger_overview()
        self._charger_top_produits()
        self._charger_caisse()
        self._charger_tva()
        self._charger_stock()

    def _charger_overview(self):
        from modules.rapports import Rapport
        from modules.produits import Produit

        try:
            stats = Rapport.statistiques_generales()
            evol = Rapport.evolution_ventes_7_jours()
            alertes = Produit.obtenir_stock_faible()

            nb_ventes_jour = stats.get('nb_ventes', 0)
            ca_jour = stats.get('ca_jour', 0)
            ca_total = stats.get('ca_total', 0)
            valeur_stock = stats.get('valeur_stock', 0)

            # Count today's sales from evolution data
            from datetime import datetime
            today = datetime.now().strftime("%Y-%m-%d")
            ventes_jour = 0
            for e in evol:
                if str(e[0]) == today:
                    ventes_jour = e[1]
                    break

            self._maj_card(self._cards_overview["ventes_jour"], str(ventes_jour or nb_ventes_jour))
            self._maj_card(self._cards_overview["ca_jour"], f"{ca_jour:,.0f} FCFA")
            self._maj_card(self._cards_overview["stock_alertes"], str(len(alertes) if alertes else 0))
            self._maj_card(self._cards_overview["nb_ventes_total"], str(stats.get('nb_ventes', 0)))
            self._maj_card(self._cards_overview["ca_total"], f"{ca_total:,.0f} FCFA")
            self._maj_card(self._cards_overview["valeur_stock"], f"{valeur_stock:,.0f} FCFA")

            # Chart
            self._afficher_graphique_evolution(evol)
        except Exception as e:
            erreur(self, "Erreur", f"Impossible de charger les statistiques :\n{e}")

    def _afficher_graphique_evolution(self, evol):
        # Clear previous chart
        while self.chart_container.count():
            item = self.chart_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        try:
            from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
            from matplotlib.figure import Figure

            fig = Figure(figsize=(8, 3), dpi=100)
            fig.patch.set_facecolor('none')
            ax = fig.add_subplot(111)

            if evol:
                jours = [str(e[0])[-5:] for e in evol]  # MM-DD
                ca_values = [e[2] for e in evol]

                ax.plot(jours, ca_values, marker='o', linewidth=2,
                        color=Theme.c('primary'), markersize=6)
                ax.fill_between(jours, ca_values, alpha=0.1, color=Theme.c('primary'))

                for i, v in enumerate(ca_values):
                    ax.annotate(f"{v:,.0f}", (jours[i], v),
                                textcoords="offset points", xytext=(0, 10),
                                ha='center', fontsize=8)

            ax.set_ylabel("CA (FCFA)")
            ax.grid(True, alpha=0.3)
            fig.tight_layout()

            canvas = FigureCanvasQTAgg(fig)
            self.chart_container.addWidget(canvas)
        except ImportError:
            lbl = QLabel("(matplotlib non disponible - installez-le pour les graphiques)")
            lbl.setStyleSheet(f"color: {Theme.c('gray')};")
            lbl.setAlignment(Qt.AlignCenter)
            self.chart_container.addWidget(lbl)

    def _charger_top_produits(self):
        from modules.rapports import Rapport
        try:
            top = Rapport.top_produits(20)
            lignes = []
            for i, p in enumerate(top, 1):
                # (nom, categorie, total_vendu, ca_total)
                lignes.append([i, p[0], p[1], p[2], f"{p[3]:,.0f}"])
            self.top_model.charger_donnees(lignes)
            self.top_table.ajuster_colonnes()

            # Bar chart
            self._afficher_top_chart(top[:10])
        except Exception as e:
            erreur(self, "Erreur", f"Erreur chargement top produits :\n{e}")

    def _afficher_top_chart(self, top):
        while self.top_chart_container.count():
            item = self.top_chart_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        try:
            from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
            from matplotlib.figure import Figure

            fig = Figure(figsize=(8, 3), dpi=100)
            fig.patch.set_facecolor('none')
            ax = fig.add_subplot(111)

            if top:
                noms = [p[0][:20] for p in top]
                qtes = [p[2] for p in top]
                colors = [Theme.c('primary')] * len(noms)

                ax.barh(range(len(noms)), qtes, color=colors, height=0.6)
                ax.set_yticks(range(len(noms)))
                ax.set_yticklabels(noms, fontsize=8)
                ax.set_xlabel("Quantite vendue")
                ax.invert_yaxis()

            fig.tight_layout()
            canvas = FigureCanvasQTAgg(fig)
            self.chart_container.addWidget(canvas)
        except ImportError:
            pass

    def _charger_caisse(self):
        from modules.paiements import Paiement

        date = self.caisse_date.date().toString("yyyy-MM-dd")
        try:
            rapport = Paiement.rapport_caisse_jour(date)

            # Update cards
            for key in ["especes", "orange_money", "mtn_momo", "moov_money"]:
                val = rapport.get(f"total_{key}", 0)
                self._maj_card(self._caisse_cards[key], f"{val:,.0f} FCFA")

            # Table
            lignes = []
            for d in rapport.get('details_par_mode', []):
                lignes.append([d['label'], d['nb'], f"{d['total']:,.0f}"])
            self.caisse_model.charger_donnees(lignes)
            self.caisse_table.ajuster_colonnes()

            self.lbl_total_caisse.setText(
                f"Total general : {rapport.get('total_general', 0):,.0f} FCFA  "
                f"({rapport.get('nb_transactions', 0)} transactions)"
            )
        except Exception as e:
            erreur(self, "Erreur", f"Erreur chargement caisse :\n{e}")

    def _charger_tva(self):
        from modules.fiscalite import Fiscalite

        try:
            active = Fiscalite.tva_active()
            if active:
                self.tva_banner.setText("TVA ACTIVE")
                self.tva_banner.setStyleSheet(
                    f"background-color: {Theme.c('success')}; color: white; "
                    f"border-radius: 6px; padding: 5px;"
                )

                rapport = Fiscalite.rapport_tva_mensuel()
                self._maj_card(self._tva_cards["ca_ttc"], f"{rapport['total_ttc']:,.0f} FCFA")
                self._maj_card(self._tva_cards["ca_ht"], f"{rapport['total_ht']:,.0f} FCFA")
                self._maj_card(self._tva_cards["tva_collectee"], f"{rapport['total_tva']:,.0f} FCFA")
            else:
                self.tva_banner.setText("TVA INACTIVE")
                self.tva_banner.setStyleSheet(
                    f"background-color: {Theme.c('gray')}; color: white; "
                    f"border-radius: 6px; padding: 5px;"
                )
                for card in self._tva_cards.values():
                    self._maj_card(card, "N/A")

            # Taux par categorie
            taux = Fiscalite.lister_taux_tva()
            lignes = []
            for t in (taux or []):
                # (id, categorie, taux, description)
                lignes.append([t[0], t[1], f"{t[2]}%", t[3] or ""])
            self.tva_model.charger_donnees(lignes)
            self.tva_table.ajuster_colonnes()
        except Exception as e:
            erreur(self, "Erreur", f"Erreur chargement TVA :\n{e}")

    def _charger_stock(self):
        from modules.produits import Produit

        try:
            produits = Produit.obtenir_stock_faible()
            nb = len(produits) if produits else 0

            self.lbl_stock_alert.setText(f"{nb} produit(s) en stock faible")
            if nb > 0:
                self.lbl_stock_alert.setStyleSheet(f"color: {Theme.c('danger')};")
            else:
                self.lbl_stock_alert.setStyleSheet(f"color: {Theme.c('success')};")

            lignes = []
            for p in (produits or []):
                # produit tuple: (id, nom, categorie, prix_achat, prix_vente, stock_actuel, stock_alerte, ...)
                lignes.append([p[1], p[2], p[5], p[6], f"{p[4]:,.0f}"])
            self.stock_model.charger_donnees(lignes)
            self.stock_table.ajuster_colonnes()
        except Exception as e:
            erreur(self, "Erreur", f"Erreur chargement stock :\n{e}")

    def _exporter_excel(self):
        try:
            import pandas as pd
            from modules.rapports import Rapport
            from modules.produits import Produit
            from config import EXPORTS_DIR
            from datetime import datetime
            import os

            os.makedirs(EXPORTS_DIR, exist_ok=True)

            stats = Rapport.statistiques_generales()
            top = Rapport.top_produits(20)
            stock = Produit.obtenir_stock_faible()

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = os.path.join(EXPORTS_DIR, f"rapport_{timestamp}.xlsx")

            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                # Stats
                df_stats = pd.DataFrame([stats])
                df_stats.to_excel(writer, sheet_name="Statistiques", index=False)

                # Top produits
                if top:
                    df_top = pd.DataFrame(top, columns=["Produit", "Categorie", "Qte Vendue", "CA"])
                    df_top.to_excel(writer, sheet_name="Top Produits", index=False)

                # Stock faible
                if stock:
                    df_stock = pd.DataFrame(
                        [[p[1], p[2], p[5], p[6], p[4]] for p in stock],
                        columns=["Produit", "Categorie", "Stock", "Seuil", "Prix"]
                    )
                    df_stock.to_excel(writer, sheet_name="Stock Faible", index=False)

            information(self, "Export reussi", f"Rapport exporte :\n{filepath}")
        except ImportError:
            erreur(self, "Erreur", "pandas et openpyxl sont necessaires pour l'export Excel.\n"
                   "Installez-les avec : pip install pandas openpyxl")
        except Exception as e:
            erreur(self, "Erreur", f"Erreur lors de l'export :\n{e}")
