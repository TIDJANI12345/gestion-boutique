"""
Fenetre de gestion des clients - PySide6
CRUD clients, recherche, pagination, historique achats.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QWidget, QTextEdit
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from ui.theme import Theme
from ui.components.table import BoutiqueTableView, BoutiqueTableModel
from ui.components.dialogs import confirmer, information, erreur


class ClientsWindow(QDialog):
    """Fenetre de gestion des clients - CRUD complet."""

    PAGE_SIZE = 10

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestion des Clients")
        self.setMinimumSize(1300, 750)
        self.setModal(True)

        self._page = 0
        self._total = 0
        self._client_selectionne_id = None

        self._setup_ui()
        self._charger_page()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # En-tete
        header = QFrame()
        header.setFixedHeight(60)
        header.setStyleSheet(f"background-color: {Theme.c('info')};")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(30, 0, 30, 0)

        titre = QLabel("Gestion des Clients")
        titre.setFont(QFont("Segoe UI", 20, QFont.Bold))
        titre.setStyleSheet("color: white; background: transparent;")
        header_layout.addWidget(titre)

        layout.addWidget(header)

        # Conteneur principal
        main = QWidget()
        main_layout = QHBoxLayout(main)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # === COLONNE GAUCHE (formulaire) ===
        left = QWidget()
        left.setFixedWidth(380)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(12)

        form_frame = QFrame()
        form_frame.setStyleSheet(
            f"QFrame {{ background-color: {Theme.c('card_bg')}; "
            f"border: 1px solid {Theme.c('card_border')}; border-radius: 8px; }}"
        )
        fl = QVBoxLayout(form_frame)
        fl.setContentsMargins(20, 15, 20, 20)
        fl.setSpacing(8)

        lbl_form = QLabel("Fiche client")
        lbl_form.setFont(QFont("Segoe UI", 13, QFont.Bold))
        fl.addWidget(lbl_form)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color: {Theme.c('separator')};")
        fl.addWidget(sep)

        fl.addWidget(QLabel("Nom *"))
        self._entry_nom = QLineEdit()
        self._entry_nom.setPlaceholderText("Nom du client")
        fl.addWidget(self._entry_nom)

        fl.addWidget(QLabel("Telephone"))
        self._entry_telephone = QLineEdit()
        self._entry_telephone.setPlaceholderText("Numero de telephone")
        fl.addWidget(self._entry_telephone)

        fl.addWidget(QLabel("Email"))
        self._entry_email = QLineEdit()
        self._entry_email.setPlaceholderText("Adresse email")
        fl.addWidget(self._entry_email)

        fl.addWidget(QLabel("Notes"))
        self._entry_notes = QTextEdit()
        self._entry_notes.setMaximumHeight(80)
        self._entry_notes.setPlaceholderText("Notes optionnelles")
        fl.addWidget(self._entry_notes)

        # Boutons
        btn_row = QHBoxLayout()

        btn_enregistrer = QPushButton("Enregistrer")
        btn_enregistrer.setFont(QFont("Segoe UI", 11, QFont.Bold))
        btn_enregistrer.setMinimumHeight(42)
        btn_enregistrer.setCursor(Qt.PointingHandCursor)
        btn_enregistrer.setProperty("class", "success")
        btn_enregistrer.clicked.connect(self._enregistrer_client)
        btn_row.addWidget(btn_enregistrer)

        btn_reset = QPushButton("Reinitialiser")
        btn_reset.setMinimumHeight(42)
        btn_reset.setCursor(Qt.PointingHandCursor)
        btn_reset.clicked.connect(self._reinitialiser_formulaire)
        btn_row.addWidget(btn_reset)

        fl.addLayout(btn_row)

        left_layout.addWidget(form_frame)
        left_layout.addStretch()

        main_layout.addWidget(left)

        # === COLONNE DROITE (liste) ===
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        # Recherche
        search_row = QHBoxLayout()
        self._entry_recherche = QLineEdit()
        self._entry_recherche.setPlaceholderText("Rechercher (nom, telephone, email)...")
        self._entry_recherche.setClearButtonEnabled(True)
        self._entry_recherche.returnPressed.connect(self._rechercher)
        self._entry_recherche.textChanged.connect(self._rechercher)
        search_row.addWidget(self._entry_recherche)
        right_layout.addLayout(search_row)

        # Boutons d'action
        actions_row = QHBoxLayout()

        btn_modifier = QPushButton("Modifier")
        btn_modifier.setCursor(Qt.PointingHandCursor)
        btn_modifier.setProperty("class", "primary")
        btn_modifier.clicked.connect(self._modifier_client)
        actions_row.addWidget(btn_modifier)

        btn_supprimer = QPushButton("Supprimer")
        btn_supprimer.setCursor(Qt.PointingHandCursor)
        btn_supprimer.setProperty("class", "danger")
        btn_supprimer.clicked.connect(self._supprimer_client)
        actions_row.addWidget(btn_supprimer)

        btn_historique = QPushButton("Historique")
        btn_historique.setCursor(Qt.PointingHandCursor)
        btn_historique.clicked.connect(self._voir_historique)
        actions_row.addWidget(btn_historique)

        btn_actualiser = QPushButton("Actualiser")
        btn_actualiser.setCursor(Qt.PointingHandCursor)
        btn_actualiser.clicked.connect(self._charger_page)
        actions_row.addWidget(btn_actualiser)

        right_layout.addLayout(actions_row)

        # Tableau
        colonnes = ['ID', 'Nom', 'Telephone', 'Email', 'Points', 'Total achats', 'Nb achats']
        self._table_model = BoutiqueTableModel(colonnes)
        self._table_view = BoutiqueTableView()
        self._table_view.setModel(self._table_model)
        self._table_view.ligne_selectionnee.connect(self._selectionner_client)
        right_layout.addWidget(self._table_view, 1)

        # Pagination
        pag_row = QHBoxLayout()
        self._btn_prev = QPushButton("< Precedent")
        self._btn_prev.setCursor(Qt.PointingHandCursor)
        self._btn_prev.clicked.connect(self._page_precedente)
        pag_row.addWidget(self._btn_prev)

        pag_row.addStretch()
        self._label_page = QLabel("Page 1")
        self._label_page.setFont(QFont("Segoe UI", 10))
        pag_row.addWidget(self._label_page)

        self._label_total = QLabel("")
        self._label_total.setFont(QFont("Segoe UI", 10))
        self._label_total.setStyleSheet(f"color: {Theme.c('gray')};")
        pag_row.addWidget(self._label_total)
        pag_row.addStretch()

        self._btn_next = QPushButton("Suivant >")
        self._btn_next.setCursor(Qt.PointingHandCursor)
        self._btn_next.clicked.connect(self._page_suivante)
        pag_row.addWidget(self._btn_next)

        right_layout.addLayout(pag_row)

        main_layout.addWidget(right, 1)
        layout.addWidget(main, 1)

    # === Chargement ===

    def _charger_page(self):
        from modules.clients import Client

        terme = self._entry_recherche.text().strip()
        offset = self._page * self.PAGE_SIZE

        clients = Client.rechercher_filtre(terme, limit=self.PAGE_SIZE, offset=offset)
        self._total = Client.compter_filtre(terme)

        lignes = []
        for c in clients:
            lignes.append([
                c[0],                                          # ID
                c[1] or "",                                     # Nom
                c[2] or "",                                     # Telephone
                c[3] or "",                                     # Email
                c[4] if c[4] is not None else 0,                # Points fidelite
                f"{c[5]:,.0f}" if c[5] is not None else "0",    # Total achats
                c[6] if c[6] is not None else 0,                # Nb achats
            ])

        self._table_model.charger_donnees(lignes)
        self._table_view.ajuster_colonnes()

        total_pages = max(1, (self._total + self.PAGE_SIZE - 1) // self.PAGE_SIZE)
        self._label_page.setText(f"Page {self._page + 1} / {total_pages}")
        self._label_total.setText(f"({self._total} clients)")
        self._btn_prev.setEnabled(self._page > 0)
        self._btn_next.setEnabled((self._page + 1) * self.PAGE_SIZE < self._total)

    def _rechercher(self):
        self._page = 0
        self._charger_page()

    def _page_precedente(self):
        if self._page > 0:
            self._page -= 1
            self._charger_page()

    def _page_suivante(self):
        if (self._page + 1) * self.PAGE_SIZE < self._total:
            self._page += 1
            self._charger_page()

    # === Selection ===

    def _selectionner_client(self, row: int):
        ligne = self._table_model.obtenir_ligne(row)
        if not ligne:
            return

        client_id = ligne[0]
        self._client_selectionne_id = client_id

        from modules.clients import Client
        c = Client.obtenir_par_id(client_id)
        if not c:
            return

        self._entry_nom.setText(c[1] or "")
        self._entry_telephone.setText(c[2] or "")
        self._entry_email.setText(c[3] or "")
        self._entry_notes.setPlainText(c[8] if len(c) > 8 and c[8] else "")

    # === CRUD ===

    def _enregistrer_client(self):
        nom = self._entry_nom.text().strip()
        if not nom:
            erreur(self, "Erreur", "Le nom du client est obligatoire.")
            return

        telephone = self._entry_telephone.text().strip() or None
        email = self._entry_email.text().strip() or None
        notes = self._entry_notes.toPlainText().strip() or None

        from modules.clients import Client
        result = Client.ajouter(nom, telephone, email, notes)

        if result:
            information(self, "Succes", f"Client '{nom}' ajoute.")
            self._reinitialiser_formulaire()
            self._charger_page()
        else:
            erreur(self, "Erreur", "Impossible d'ajouter le client.")

    def _modifier_client(self):
        if not self._client_selectionne_id:
            erreur(self, "Erreur", "Selectionnez un client a modifier.")
            return

        nom = self._entry_nom.text().strip()
        if not nom:
            erreur(self, "Erreur", "Le nom du client est obligatoire.")
            return

        telephone = self._entry_telephone.text().strip() or None
        email = self._entry_email.text().strip() or None
        notes = self._entry_notes.toPlainText().strip() or None

        from modules.clients import Client
        succes = Client.modifier(self._client_selectionne_id, nom, telephone, email, notes)

        if succes:
            information(self, "Succes", f"Client '{nom}' modifie.")
            self._charger_page()
        else:
            erreur(self, "Erreur", "Impossible de modifier le client.")

    def _supprimer_client(self):
        if not self._client_selectionne_id:
            erreur(self, "Erreur", "Selectionnez un client a supprimer.")
            return

        if not confirmer(self, "Confirmation", "Supprimer ce client ?"):
            return

        from modules.clients import Client
        succes = Client.supprimer(self._client_selectionne_id)

        if succes:
            information(self, "Succes", "Client supprime.")
            self._reinitialiser_formulaire()
            self._charger_page()
        else:
            erreur(self, "Erreur", "Impossible de supprimer le client.")

    def _voir_historique(self):
        if not self._client_selectionne_id:
            erreur(self, "Erreur", "Selectionnez un client.")
            return

        from modules.clients import Client
        client = Client.obtenir_par_id(self._client_selectionne_id)
        if not client:
            erreur(self, "Erreur", "Client introuvable.")
            return

        dlg = HistoriqueClientDialog(client, parent=self)
        dlg.exec()

    def _reinitialiser_formulaire(self):
        self._client_selectionne_id = None
        self._entry_nom.clear()
        self._entry_telephone.clear()
        self._entry_email.clear()
        self._entry_notes.clear()


class HistoriqueClientDialog(QDialog):
    """Sous-dialogue affichant l'historique d'achats d'un client."""

    def __init__(self, client_tuple, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Historique - {client_tuple[1]}")
        self.setMinimumSize(700, 500)
        self.setModal(True)

        self._client = client_tuple
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Fiche client
        info_frame = QFrame()
        info_frame.setStyleSheet(
            f"QFrame {{ background-color: {Theme.c('card_bg')}; "
            f"border: 1px solid {Theme.c('card_border')}; border-radius: 8px; }}"
        )
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(15, 12, 15, 12)

        c = self._client
        nom_label = QLabel(c[1] or "")
        nom_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        info_layout.addWidget(nom_label)

        details = []
        if c[2]:
            details.append(f"Tel: {c[2]}")
        if c[3]:
            details.append(f"Email: {c[3]}")
        points = c[4] if c[4] is not None else 0
        total = c[5] if c[5] is not None else 0
        nb = c[6] if c[6] is not None else 0
        details.append(f"Points: {points}  |  Total achats: {total:,.0f} FCFA  |  {nb} achats")

        for d in details:
            lbl = QLabel(d)
            lbl.setStyleSheet(f"color: {Theme.c('text_secondary')}; font-size: 11px;")
            info_layout.addWidget(lbl)

        layout.addWidget(info_frame)

        # Tableau historique
        lbl_hist = QLabel("Historique des achats")
        lbl_hist.setFont(QFont("Segoe UI", 13, QFont.Bold))
        layout.addWidget(lbl_hist)

        colonnes = ['ID', 'N° Vente', 'Date', 'Total', 'Statut']
        self._table_model = BoutiqueTableModel(colonnes)
        self._table_view = BoutiqueTableView()
        self._table_view.setModel(self._table_model)
        layout.addWidget(self._table_view, 1)

        # Charger l'historique
        from modules.clients import Client
        achats = Client.obtenir_historique_achats(c[0], limit=50)

        lignes = []
        for a in achats:
            lignes.append([
                a[0],                                         # ID vente
                a[1] or "",                                    # Numero vente
                a[2] or "",                                    # Date
                f"{a[3]:,.0f} FCFA" if a[3] is not None else "0", # Total
                a[4] or "",                                    # Statut
            ])

        self._table_model.charger_donnees(lignes)
        self._table_view.ajuster_colonnes()

        if not lignes:
            lbl_vide = QLabel("Aucun achat enregistre pour ce client.")
            lbl_vide.setAlignment(Qt.AlignCenter)
            lbl_vide.setStyleSheet(f"color: {Theme.c('gray')}; font-size: 12px;")
            layout.addWidget(lbl_vide)

        # Bouton fermer
        btn_fermer = QPushButton("Fermer")
        btn_fermer.setMinimumHeight(38)
        btn_fermer.setCursor(Qt.PointingHandCursor)
        btn_fermer.clicked.connect(self.accept)
        layout.addWidget(btn_fermer)
