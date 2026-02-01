"""
Fenetre Liste des Ventes - PySide6
Historique des ventes avec recherche, filtres par date, details et reimpression.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QWidget, QDateEdit, QMenu
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont, QDesktopServices, QAction

from ui.theme import Theme
from ui.components.table import BoutiqueTableView, BoutiqueTableModel
from ui.components.dialogs import confirmer, information, erreur


class ListeVentesWindow(QDialog):
    """Historique des ventes avec recherche et filtres."""

    def __init__(self, parent=None, utilisateur=None):
        super().__init__(parent)
        self.utilisateur = utilisateur
        self.setWindowTitle("Liste des Ventes")
        self.setMinimumSize(1200, 700)
        self.setModal(True)

        self._setup_ui()
        self._charger_ventes()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # En-tete
        header = QFrame()
        header.setFixedHeight(60)
        header.setStyleSheet(f"background-color: {Theme.c('success')};")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(30, 0, 30, 0)

        titre = QLabel("Liste des Ventes")
        titre.setFont(QFont("Segoe UI", 20, QFont.Bold))
        titre.setStyleSheet("color: white; background: transparent;")
        hl.addWidget(titre)

        layout.addWidget(header)

        # Conteneur principal
        main = QWidget()
        ml = QVBoxLayout(main)
        ml.setContentsMargins(20, 15, 20, 15)
        ml.setSpacing(12)

        # Barre de recherche et filtres
        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Rechercher (client, numero...)")
        self.search_input.setMinimumWidth(250)
        self.search_input.textChanged.connect(self._rechercher_ventes)
        filter_bar.addWidget(self.search_input)

        filter_bar.addWidget(QLabel("Du :"))
        self.date_debut = QDateEdit()
        self.date_debut.setCalendarPopup(True)
        self.date_debut.setDate(QDate.currentDate().addMonths(-1))
        self.date_debut.setDisplayFormat("dd/MM/yyyy")
        filter_bar.addWidget(self.date_debut)

        filter_bar.addWidget(QLabel("Au :"))
        self.date_fin = QDateEdit()
        self.date_fin.setCalendarPopup(True)
        self.date_fin.setDate(QDate.currentDate())
        self.date_fin.setDisplayFormat("dd/MM/yyyy")
        filter_bar.addWidget(self.date_fin)

        btn_filtrer = QPushButton("Filtrer")
        btn_filtrer.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.c('primary')}; color: white; "
            f"padding: 8px 16px; border-radius: 6px; font-weight: bold; }}"
            f"QPushButton:hover {{ background-color: {Theme.c('info')}; }}"
        )
        btn_filtrer.clicked.connect(self._charger_ventes)
        filter_bar.addWidget(btn_filtrer)

        btn_refresh = QPushButton("Actualiser")
        btn_refresh.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.c('gray')}; color: white; "
            f"padding: 8px 16px; border-radius: 6px; }}"
            f"QPushButton:hover {{ opacity: 0.8; }}"
        )
        btn_refresh.clicked.connect(self._charger_ventes)
        filter_bar.addWidget(btn_refresh)

        filter_bar.addStretch()
        ml.addLayout(filter_bar)

        # Stats globales
        self.lbl_stats = QLabel()
        self.lbl_stats.setFont(QFont("Segoe UI", 11))
        self.lbl_stats.setStyleSheet(f"color: {Theme.c('gray')};")
        ml.addWidget(self.lbl_stats)

        # Stats par vendeur (Admin seulement)
        if not (self.utilisateur and self.utilisateur.get('role') == 'caissier'):
            self.lbl_stats_vendeurs = QLabel()
            self.lbl_stats_vendeurs.setFont(QFont("Segoe UI", 10))
            self.lbl_stats_vendeurs.setStyleSheet(f"color: {Theme.c('info')}; font-style: italic;")
            self.lbl_stats_vendeurs.setWordWrap(True)
            ml.addWidget(self.lbl_stats_vendeurs)
        else:
            self.lbl_stats_vendeurs = None

        # Table (colonnes selon rôle)
        if self.utilisateur and self.utilisateur.get('role') == 'caissier':
            colonnes = ["ID", "Numero", "Date", "Heure", "Client", "Total (FCFA)", "Paiement", "Nb Articles"]
        else:
            # Admin/Gérant : ajouter colonne Vendeur
            colonnes = ["ID", "Numero", "Date", "Heure", "Vendeur", "Client", "Total (FCFA)", "Paiement", "Nb Articles"]
        self.model = BoutiqueTableModel(colonnes)
        self.table = BoutiqueTableView()
        self.table.setModel(self.model)
        self.table.ligne_double_clic.connect(self._voir_details)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._menu_contextuel)
        ml.addWidget(self.table)

        layout.addWidget(main)

    def _charger_ventes(self):
        from modules.ventes import Vente
        from modules.paiements import Paiement, MODE_LABELS
        from database import db

        d1 = self.date_debut.date().toString("yyyy-MM-dd") + " 00:00:00"
        d2 = self.date_fin.date().toString("yyyy-MM-dd") + " 23:59:59"

        # Requête avec JOIN pour récupérer nom vendeur
        est_caissier = self.utilisateur and self.utilisateur.get('role') == 'caissier'

        if est_caissier:
            # Caissier : uniquement ses ventes
            query = """
                SELECT v.id, v.numero_vente, v.date_vente, v.total, v.client
                FROM ventes v
                WHERE v.date_vente BETWEEN ? AND ?
                AND v.utilisateur_id = ?
                ORDER BY v.date_vente DESC
            """
            ventes = db.fetch_all(query, (d1, d2, self.utilisateur['id']))
        else:
            # Admin : toutes les ventes + nom vendeur
            query = """
                SELECT v.id, v.numero_vente, v.date_vente, v.total, v.client,
                       u.prenom, u.nom
                FROM ventes v
                LEFT JOIN utilisateurs u ON v.utilisateur_id = u.id
                WHERE v.date_vente BETWEEN ? AND ?
                ORDER BY v.date_vente DESC
            """
            ventes = db.fetch_all(query, (d1, d2))

        lignes = []
        total_ca = 0

        for v in ventes:
            vente_id = v[0]
            numero = v[1]
            date_str = str(v[2])[:10] if v[2] else ""
            heure_str = str(v[2])[11:16] if v[2] else ""
            client = v[4] or ""
            total = v[3] or 0
            total_ca += total

            # Nom vendeur (seulement pour admin)
            if not est_caissier:
                vendeur_prenom = v[5] or ""
                vendeur_nom = v[6] or ""
                vendeur = f"{vendeur_prenom} {vendeur_nom}".strip() if vendeur_prenom or vendeur_nom else "-"

            # Nombre d'articles
            details = Vente.obtenir_details_vente(vente_id)
            nb_articles = sum(d[2] for d in details) if details else 0

            # Mode de paiement
            paiements = Paiement.obtenir_paiements_vente(vente_id)
            if paiements:
                modes = [MODE_LABELS.get(p[2], p[2]) for p in paiements]
                mode_str = " + ".join(set(modes))
            else:
                mode_str = "-"

            # Ligne selon rôle
            if est_caissier:
                lignes.append([
                    vente_id, numero, date_str, heure_str, client,
                    f"{total:,.0f}", mode_str, nb_articles
                ])
            else:
                lignes.append([
                    vente_id, numero, date_str, heure_str, vendeur, client,
                    f"{total:,.0f}", mode_str, nb_articles
                ])

        self.model.charger_donnees(lignes)
        self.table.ajuster_colonnes()
        self.lbl_stats.setText(
            f"{len(lignes)} vente(s)  |  CA total : {total_ca:,.0f} FCFA"
        )

        # Stats par vendeur (Admin seulement)
        if self.lbl_stats_vendeurs and not est_caissier:
            stats_vendeurs = {}
            for v in ventes:
                vendeur_prenom = v[5] or ""
                vendeur_nom = v[6] or ""
                vendeur_key = f"{vendeur_prenom} {vendeur_nom}".strip() if vendeur_prenom or vendeur_nom else "Non assigné"
                total_vente = v[3] or 0

                if vendeur_key not in stats_vendeurs:
                    stats_vendeurs[vendeur_key] = {'nb': 0, 'ca': 0}
                stats_vendeurs[vendeur_key]['nb'] += 1
                stats_vendeurs[vendeur_key]['ca'] += total_vente

            # Afficher top 5 vendeurs
            top_vendeurs = sorted(stats_vendeurs.items(), key=lambda x: x[1]['ca'], reverse=True)[:5]
            if top_vendeurs:
                stats_text = "📊 Performance vendeurs : " + " | ".join([
                    f"{nom}: {stats['nb']} vente(s), {stats['ca']:,.0f} F"
                    for nom, stats in top_vendeurs
                ])
                self.lbl_stats_vendeurs.setText(stats_text)
            else:
                self.lbl_stats_vendeurs.setText("")

    def _rechercher_ventes(self):
        terme = self.search_input.text().lower().strip()
        if not terme:
            self._charger_ventes()
            return

        row_count = self.model.rowCount()
        lignes_filtrees = []
        for row in range(row_count):
            ligne = self.model.obtenir_ligne(row)
            texte = " ".join(str(v) for v in ligne).lower()
            if terme in texte:
                lignes_filtrees.append(ligne)

        self.model.charger_donnees(lignes_filtrees)
        self.table.ajuster_colonnes()

    def _menu_contextuel(self, pos):
        row = self.table.ligne_courante()
        if row < 0:
            return
        menu = QMenu(self)
        act_voir = QAction("Voir details", self)
        act_voir.triggered.connect(lambda: self._voir_details(row))
        menu.addAction(act_voir)

        act_recu = QAction("Reimprimer recu", self)
        act_recu.triggered.connect(lambda: self._reimprimer_recu(row))
        menu.addAction(act_recu)

        menu.addSeparator()
        act_suppr = QAction("Supprimer", self)
        act_suppr.triggered.connect(lambda: self._supprimer_vente(row))
        menu.addAction(act_suppr)

        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _voir_details(self, row):
        from modules.ventes import Vente
        from modules.paiements import Paiement, MODE_LABELS

        ligne = self.model.obtenir_ligne(row)
        if not ligne:
            return
        vente_id = ligne[0]
        vente = Vente.obtenir_vente(vente_id)
        if not vente:
            erreur(self, "Erreur", "Vente introuvable.")
            return

        details = Vente.obtenir_details_vente(vente_id)
        paiements = Paiement.obtenir_paiements_vente(vente_id)

        dlg = QDialog(self)
        dlg.setWindowTitle(f"Detail vente {vente[1]}")
        dlg.setMinimumSize(700, 500)
        layout = QVBoxLayout(dlg)

        # Info vente
        info_frame = QFrame()
        info_frame.setStyleSheet(
            f"QFrame {{ background: {Theme.c('card_bg')}; border: 1px solid {Theme.c('card_border')}; "
            f"border-radius: 8px; }}"
        )
        info_l = QVBoxLayout(info_frame)
        info_l.setContentsMargins(15, 10, 15, 10)

        lbl_title = QLabel(f"Vente {vente[1]}")
        lbl_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        info_l.addWidget(lbl_title)

        date_str = str(vente[2])[:19] if vente[2] else ""
        client_str = vente[4] or "Client anonyme"
        info_l.addWidget(QLabel(f"Date : {date_str}"))
        info_l.addWidget(QLabel(f"Client : {client_str}"))
        info_l.addWidget(QLabel(f"Total : {vente[3]:,.0f} FCFA"))
        layout.addWidget(info_frame)

        # Produits
        layout.addWidget(QLabel("Produits :"))
        col_prod = ["Produit", "Quantite", "Prix unitaire", "Sous-total"]
        model_prod = BoutiqueTableModel(col_prod)
        table_prod = BoutiqueTableView()
        table_prod.setModel(model_prod)
        prod_lignes = []
        for d in details:
            # (id, nom, qte, prix_unit, sous_total, code_barre)
            prod_lignes.append([d[1], d[2], f"{d[3]:,.0f}", f"{d[4]:,.0f}"])
        model_prod.charger_donnees(prod_lignes)
        table_prod.ajuster_colonnes()
        layout.addWidget(table_prod)

        # Paiements
        layout.addWidget(QLabel("Paiements :"))
        col_paie = ["Mode", "Montant", "Reference"]
        model_paie = BoutiqueTableModel(col_paie)
        table_paie = BoutiqueTableView()
        table_paie.setModel(model_paie)
        paie_lignes = []
        for p in paiements:
            # (id, vente_id, mode, montant, reference, montant_recu, monnaie_rendue, date)
            paie_lignes.append([MODE_LABELS.get(p[2], p[2]), f"{p[3]:,.0f}", p[4] or ""])
        model_paie.charger_donnees(paie_lignes)
        table_paie.ajuster_colonnes()
        layout.addWidget(table_paie)

        # Boutons
        btns = QHBoxLayout()
        btns.addStretch()
        btn_recu = QPushButton("Reimprimer recu")
        btn_recu.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.c('primary')}; color: white; "
            f"padding: 8px 16px; border-radius: 6px; }}"
        )
        btn_recu.clicked.connect(lambda: self._reimprimer_recu_par_id(vente_id))
        btns.addWidget(btn_recu)

        btn_fermer = QPushButton("Fermer")
        btn_fermer.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.c('gray')}; color: white; "
            f"padding: 8px 16px; border-radius: 6px; }}"
        )
        btn_fermer.clicked.connect(dlg.close)
        btns.addWidget(btn_fermer)
        layout.addLayout(btns)

        dlg.exec()

    def _reimprimer_recu(self, row):
        ligne = self.model.obtenir_ligne(row)
        if not ligne:
            return
        self._reimprimer_recu_par_id(ligne[0])

    def _reimprimer_recu_par_id(self, vente_id):
        from modules.recus import generer_recu_pdf
        from PySide6.QtCore import QUrl
        try:
            chemin = generer_recu_pdf(vente_id)
            if chemin:
                QDesktopServices.openUrl(QUrl.fromLocalFile(chemin))
            else:
                erreur(self, "Erreur", "Impossible de generer le recu.")
        except Exception as e:
            erreur(self, "Erreur", f"Erreur lors de la generation du recu :\n{e}")

    def _supprimer_vente(self, row):
        ligne = self.model.obtenir_ligne(row)
        if not ligne:
            return
        vente_id = ligne[0]
        numero = ligne[1]

        if not confirmer(self, "Confirmer la suppression",
                         f"Supprimer la vente {numero} ?\n"
                         "Le stock sera restaure. Cette action est irreversible."):
            return

        from modules.ventes import Vente
        if Vente.annuler_vente(vente_id):
            information(self, "Succes", f"Vente {numero} supprimee.")
            self._charger_ventes()
        else:
            erreur(self, "Erreur", "Impossible de supprimer cette vente.")
