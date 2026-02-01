"""
Fenetre de gestion des produits - PySide6
CRUD produits, codes-barres, filtres, pagination.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QMessageBox, QWidget, QComboBox,
    QTextEdit, QRadioButton, QButtonGroup, QScrollArea,
    QSpinBox
)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QFont, QDesktopServices, QDoubleValidator, QIntValidator

from ui.theme import Theme
from ui.components.table import BoutiqueTableView, BoutiqueTableModel
from ui.components.dialogs import confirmer, information, erreur

from config import BARCODE_TYPES


class ProduitsWindow(QDialog):
    """Fenetre de gestion des produits - CRUD complet."""

    PAGE_SIZE = 10

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestion des Produits")
        self.setMinimumSize(1300, 750)
        self.setModal(True)

        self._page = 0
        self._total = 0
        self._produit_selectionne_id = None

        self._setup_ui()
        self._charger_categories()
        self._charger_page()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # En-tete
        header = QFrame()
        header.setFixedHeight(60)
        header.setStyleSheet(f"background-color: {Theme.c('success')};")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(30, 0, 30, 0)

        titre = QLabel("Gestion des Produits")
        titre.setFont(QFont("Segoe UI", 20, QFont.Bold))
        titre.setStyleSheet("color: white; background: transparent;")
        header_layout.addWidget(titre)

        layout.addWidget(header)

        # Conteneur principal 2 colonnes
        main = QWidget()
        main_layout = QHBoxLayout(main)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # === COLONNE GAUCHE (formulaire scrollable) ===
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedWidth(420)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setContentsMargins(0, 0, 5, 0)
        form_layout.setSpacing(12)

        # -- Section Code-barre --
        barcode_frame = self._creer_section("Code-barres")
        bl = barcode_frame.layout()

        # Mode auto/manuel
        mode_row = QHBoxLayout()
        self._radio_auto = QRadioButton("Automatique")
        self._radio_manual = QRadioButton("Manuel")
        self._radio_auto.setChecked(True)
        mode_group = QButtonGroup(self)
        mode_group.addButton(self._radio_auto)
        mode_group.addButton(self._radio_manual)
        self._radio_manual.toggled.connect(self._on_mode_change)
        mode_row.addWidget(self._radio_auto)
        mode_row.addWidget(self._radio_manual)
        mode_row.addStretch()
        bl.addLayout(mode_row)

        # Type code-barre
        type_row = QHBoxLayout()
        type_row.addWidget(QLabel("Type:"))
        self._combo_type_code = QComboBox()
        for key, label in BARCODE_TYPES.items():
            self._combo_type_code.addItem(label, key)
        type_row.addWidget(self._combo_type_code, 1)
        bl.addLayout(type_row)

        # Champ code-barre
        code_row = QHBoxLayout()
        self._entry_code = QLineEdit()
        self._entry_code.setPlaceholderText("Code-barres (auto-genere)")
        self._entry_code.setEnabled(False)
        code_row.addWidget(self._entry_code, 1)

        btn_gen = QPushButton("Generer")
        btn_gen.setStyleSheet(
            f"background-color: {Theme.c('info')}; color: white; "
            f"border: none; border-radius: 4px; padding: 8px 12px;"
        )
        btn_gen.setCursor(Qt.PointingHandCursor)
        btn_gen.clicked.connect(self._generer_code)
        code_row.addWidget(btn_gen)
        bl.addLayout(code_row)

        form_layout.addWidget(barcode_frame)

        # -- Section Informations --
        info_frame = self._creer_section("Informations produit")
        il = info_frame.layout()

        il.addWidget(QLabel("Nom *"))
        self._entry_nom = QLineEdit()
        self._entry_nom.setPlaceholderText("Nom du produit")
        il.addWidget(self._entry_nom)

        il.addWidget(QLabel("Categorie"))
        self._entry_categorie = QComboBox()
        self._entry_categorie.setEditable(True)
        self._entry_categorie.setPlaceholderText("Categorie")
        il.addWidget(self._entry_categorie)

        il.addWidget(QLabel("Description"))
        self._entry_description = QTextEdit()
        self._entry_description.setMaximumHeight(70)
        self._entry_description.setPlaceholderText("Description optionnelle")
        il.addWidget(self._entry_description)

        form_layout.addWidget(info_frame)

        # -- Section Prix --
        prix_frame = self._creer_section("Prix")
        pl = prix_frame.layout()

        prix_row = QHBoxLayout()

        col_pa = QVBoxLayout()
        col_pa.addWidget(QLabel("Prix d'achat"))
        self._entry_prix_achat = QLineEdit()
        self._entry_prix_achat.setPlaceholderText("0")
        self._entry_prix_achat.setValidator(QDoubleValidator(0, 999999999, 0))
        col_pa.addWidget(self._entry_prix_achat)
        prix_row.addLayout(col_pa)

        col_pv = QVBoxLayout()
        col_pv.addWidget(QLabel("Prix de vente *"))
        self._entry_prix_vente = QLineEdit()
        self._entry_prix_vente.setPlaceholderText("0")
        self._entry_prix_vente.setValidator(QDoubleValidator(0, 999999999, 0))
        col_pv.addWidget(self._entry_prix_vente)
        prix_row.addLayout(col_pv)

        pl.addLayout(prix_row)
        form_layout.addWidget(prix_frame)

        # -- Section Stock --
        stock_frame = self._creer_section("Stock")
        sl = stock_frame.layout()

        stock_row = QHBoxLayout()

        col_si = QVBoxLayout()
        col_si.addWidget(QLabel("Stock initial"))
        self._spin_stock = QSpinBox()
        self._spin_stock.setRange(0, 999999)
        self._spin_stock.setValue(0)
        col_si.addWidget(self._spin_stock)
        stock_row.addLayout(col_si)

        col_sa = QVBoxLayout()
        col_sa.addWidget(QLabel("Seuil alerte"))
        self._spin_alerte = QSpinBox()
        self._spin_alerte.setRange(0, 999999)
        self._spin_alerte.setValue(5)
        col_sa.addWidget(self._spin_alerte)
        stock_row.addLayout(col_sa)

        sl.addLayout(stock_row)
        form_layout.addWidget(stock_frame)

        # -- Boutons formulaire --
        btn_row = QHBoxLayout()

        btn_enregistrer = QPushButton("Enregistrer")
        btn_enregistrer.setFont(QFont("Segoe UI", 11, QFont.Bold))
        btn_enregistrer.setMinimumHeight(42)
        btn_enregistrer.setCursor(Qt.PointingHandCursor)
        btn_enregistrer.setProperty("class", "success")
        btn_enregistrer.clicked.connect(self._enregistrer_produit)
        btn_row.addWidget(btn_enregistrer)

        btn_reset = QPushButton("Reinitialiser")
        btn_reset.setMinimumHeight(42)
        btn_reset.setCursor(Qt.PointingHandCursor)
        btn_reset.clicked.connect(self._reinitialiser_formulaire)
        btn_row.addWidget(btn_reset)

        form_layout.addLayout(btn_row)
        form_layout.addStretch()

        scroll.setWidget(form_widget)
        main_layout.addWidget(scroll)

        # === COLONNE DROITE (liste) ===
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        # Recherche + filtres
        search_frame = QFrame()
        search_frame.setStyleSheet(
            f"QFrame {{ background-color: {Theme.c('card_bg')}; "
            f"border: 1px solid {Theme.c('card_border')}; border-radius: 8px; }}"
        )
        sf_layout = QVBoxLayout(search_frame)
        sf_layout.setContentsMargins(15, 12, 15, 12)
        sf_layout.setSpacing(8)

        # Ligne recherche
        search_row = QHBoxLayout()
        self._entry_recherche = QLineEdit()
        self._entry_recherche.setPlaceholderText("Rechercher (nom, categorie, code)...")
        self._entry_recherche.setClearButtonEnabled(True)
        self._entry_recherche.returnPressed.connect(self._rechercher)
        search_row.addWidget(self._entry_recherche)

        btn_rechercher = QPushButton("Rechercher")
        btn_rechercher.setCursor(Qt.PointingHandCursor)
        btn_rechercher.clicked.connect(self._rechercher)
        search_row.addWidget(btn_rechercher)
        sf_layout.addLayout(search_row)

        # Ligne filtres
        filter_row = QHBoxLayout()

        filter_row.addWidget(QLabel("Categorie:"))
        self._combo_filtre_cat = QComboBox()
        self._combo_filtre_cat.addItem("Toutes")
        self._combo_filtre_cat.currentTextChanged.connect(lambda: self._rechercher())
        filter_row.addWidget(self._combo_filtre_cat)

        filter_row.addWidget(QLabel("Stock:"))
        self._combo_filtre_stock = QComboBox()
        self._combo_filtre_stock.addItems(["Tous", "Stock faible", "Rupture"])
        self._combo_filtre_stock.currentTextChanged.connect(lambda: self._rechercher())
        filter_row.addWidget(self._combo_filtre_stock)

        filter_row.addWidget(QLabel("Prix min:"))
        self._entry_prix_min = QLineEdit()
        self._entry_prix_min.setFixedWidth(70)
        self._entry_prix_min.setValidator(QIntValidator(0, 999999999))
        filter_row.addWidget(self._entry_prix_min)

        filter_row.addWidget(QLabel("max:"))
        self._entry_prix_max = QLineEdit()
        self._entry_prix_max.setFixedWidth(70)
        self._entry_prix_max.setValidator(QIntValidator(0, 999999999))
        filter_row.addWidget(self._entry_prix_max)

        sf_layout.addLayout(filter_row)
        right_layout.addWidget(search_frame)

        # Boutons d'action
        actions_row = QHBoxLayout()

        btn_modifier = QPushButton("Modifier")
        btn_modifier.setCursor(Qt.PointingHandCursor)
        btn_modifier.setProperty("class", "primary")
        btn_modifier.clicked.connect(self._modifier_produit)
        actions_row.addWidget(btn_modifier)

        btn_supprimer = QPushButton("Supprimer")
        btn_supprimer.setCursor(Qt.PointingHandCursor)
        btn_supprimer.setProperty("class", "danger")
        btn_supprimer.clicked.connect(self._supprimer_produit)
        actions_row.addWidget(btn_supprimer)

        btn_voir_cb = QPushButton("Voir code-barres")
        btn_voir_cb.setCursor(Qt.PointingHandCursor)
        btn_voir_cb.clicked.connect(self._voir_code_barre)
        actions_row.addWidget(btn_voir_cb)

        btn_actualiser = QPushButton("Actualiser")
        btn_actualiser.setCursor(Qt.PointingHandCursor)
        btn_actualiser.clicked.connect(self._actualiser)
        actions_row.addWidget(btn_actualiser)

        right_layout.addLayout(actions_row)

        # Tableau
        colonnes = ['ID', 'Nom', 'Categorie', 'Prix Vente', 'Stock', 'Type', 'Code-barre']
        self._table_model = BoutiqueTableModel(colonnes)
        self._table_view = BoutiqueTableView()
        self._table_view.setModel(self._table_model)
        self._table_view.ligne_selectionnee.connect(self._selectionner_produit)
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

    def _creer_section(self, titre: str) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(
            f"QFrame {{ background-color: {Theme.c('card_bg')}; "
            f"border: 1px solid {Theme.c('card_border')}; border-radius: 8px; }}"
        )
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(6)
        lbl = QLabel(titre)
        lbl.setFont(QFont("Segoe UI", 11, QFont.Bold))
        layout.addWidget(lbl)
        return frame

    # === Mode code-barre ===

    def _on_mode_change(self, manual: bool):
        self._entry_code.setEnabled(manual)
        if not manual:
            self._entry_code.clear()
            self._entry_code.setPlaceholderText("Code-barres (auto-genere)")
        else:
            self._entry_code.setPlaceholderText("Saisir le code-barres")

    def _generer_code(self):
        from modules.produits import Produit
        type_code = self._combo_type_code.currentData() or 'code128'
        code = Produit.generer_code_barre(type_code)
        self._entry_code.setText(code)

    # === Chargement ===

    def _charger_categories(self):
        from modules.produits import Produit
        categories = Produit.obtenir_categories()
        self._combo_filtre_cat.blockSignals(True)
        self._combo_filtre_cat.clear()
        self._combo_filtre_cat.addItem("Toutes")
        self._combo_filtre_cat.addItems(categories)
        self._combo_filtre_cat.blockSignals(False)

        # Aussi mettre a jour le combo du formulaire
        self._entry_categorie.clear()
        for cat in categories:
            self._entry_categorie.addItem(cat)

    def _get_filtres(self):
        terme = self._entry_recherche.text().strip()
        categorie = self._combo_filtre_cat.currentText()
        if categorie == "Toutes":
            categorie = None
        stock_filter = self._combo_filtre_stock.currentText()
        if stock_filter == "Tous":
            stock_filter = None

        prix_min = None
        prix_max = None
        try:
            val = self._entry_prix_min.text().strip()
            if val:
                prix_min = int(val)
        except ValueError:
            pass
        try:
            val = self._entry_prix_max.text().strip()
            if val:
                prix_max = int(val)
        except ValueError:
            pass

        return terme, categorie, stock_filter, prix_min, prix_max

    def _charger_page(self):
        from modules.produits import Produit

        terme, categorie, stock_filter, prix_min, prix_max = self._get_filtres()
        offset = self._page * self.PAGE_SIZE

        produits = Produit.rechercher_filtre(
            terme=terme, categorie=categorie, stock_filter=stock_filter,
            prix_min=prix_min, prix_max=prix_max,
            limit=self.PAGE_SIZE, offset=offset
        )
        self._total = Produit.compter_filtre(
            terme=terme, categorie=categorie, stock_filter=stock_filter,
            prix_min=prix_min, prix_max=prix_max
        )

        lignes = []
        for p in produits:
            lignes.append([
                p[0],                                       # ID
                p[1] or "",                                  # Nom
                p[2] or "",                                  # Categorie
                f"{p[4]:,.0f}" if p[4] is not None else "0", # Prix vente
                p[5] if p[5] is not None else 0,             # Stock
                p[8] or "code128",                           # Type code-barre
                p[7] or "",                                  # Code-barre
            ])

        self._table_model.charger_donnees(lignes)
        self._table_view.ajuster_colonnes()

        # Pagination labels
        total_pages = max(1, (self._total + self.PAGE_SIZE - 1) // self.PAGE_SIZE)
        self._label_page.setText(f"Page {self._page + 1} / {total_pages}")
        self._label_total.setText(f"({self._total} produits)")
        self._btn_prev.setEnabled(self._page > 0)
        self._btn_next.setEnabled((self._page + 1) * self.PAGE_SIZE < self._total)

    def _rechercher(self):
        self._page = 0
        self._charger_page()

    def _actualiser(self):
        self._charger_categories()
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

    def _selectionner_produit(self, row: int):
        ligne = self._table_model.obtenir_ligne(row)
        if not ligne:
            return

        produit_id = ligne[0]
        self._produit_selectionne_id = produit_id

        from modules.produits import Produit
        p = Produit.obtenir_par_id(produit_id)
        if not p:
            return

        # Remplir le formulaire
        self._entry_nom.setText(p[1] or "")

        # Categorie
        idx = self._entry_categorie.findText(p[2] or "")
        if idx >= 0:
            self._entry_categorie.setCurrentIndex(idx)
        else:
            self._entry_categorie.setEditText(p[2] or "")

        self._entry_description.setPlainText(p[10] or "" if len(p) > 10 else "")
        self._entry_prix_achat.setText(str(int(p[3])) if p[3] is not None else "0")
        self._entry_prix_vente.setText(str(int(p[4])) if p[4] is not None else "0")
        self._spin_stock.setValue(p[5] if p[5] is not None else 0)
        self._spin_alerte.setValue(p[6] if p[6] is not None else 5)

        # Code-barre
        self._entry_code.setText(p[7] or "")
        type_code = p[8] or 'code128'
        idx_type = self._combo_type_code.findData(type_code)
        if idx_type >= 0:
            self._combo_type_code.setCurrentIndex(idx_type)

    # === CRUD ===

    def _enregistrer_produit(self):
        """Ajouter un nouveau produit."""
        nom = self._entry_nom.text().strip()
        if not nom:
            erreur(self, "Erreur", "Le nom du produit est obligatoire.")
            return

        categorie = self._entry_categorie.currentText().strip()
        description = self._entry_description.toPlainText().strip()

        try:
            prix_achat = float(self._entry_prix_achat.text() or 0)
        except ValueError:
            prix_achat = 0
        try:
            prix_vente = float(self._entry_prix_vente.text() or 0)
        except ValueError:
            erreur(self, "Erreur", "Le prix de vente est invalide.")
            return

        stock = self._spin_stock.value()
        alerte = self._spin_alerte.value()

        type_code = self._combo_type_code.currentData() or 'code128'

        # Code-barre
        code_barre = None
        if self._radio_manual.isChecked():
            code_barre = self._entry_code.text().strip()
            if not code_barre:
                erreur(self, "Erreur", "Le code-barres est vide (mode manuel).")
                return

        from modules.produits import Produit
        resultat = Produit.ajouter(
            nom, categorie, prix_achat, prix_vente, stock, alerte,
            code_barre=code_barre, type_code_barre=type_code, description=description
        )

        if resultat:
            # Generer l'image du code-barre
            try:
                from modules.codebarres import CodeBarre
                CodeBarre.generer_image(resultat, nom, prix_vente, type_code)
            except Exception:
                pass

            information(self, "Succes", f"Produit '{nom}' ajoute.\nCode-barres: {resultat}")
            self._reinitialiser_formulaire()
            self._charger_categories()
            self._charger_page()
        else:
            erreur(self, "Erreur", "Impossible d'ajouter le produit.\nVerifiez les donnees.")

    def _modifier_produit(self):
        """Modifier le produit selectionne."""
        if not self._produit_selectionne_id:
            erreur(self, "Erreur", "Selectionnez un produit a modifier.")
            return

        nom = self._entry_nom.text().strip()
        if not nom:
            erreur(self, "Erreur", "Le nom du produit est obligatoire.")
            return

        categorie = self._entry_categorie.currentText().strip()
        description = self._entry_description.toPlainText().strip()

        try:
            prix_achat = float(self._entry_prix_achat.text() or 0)
        except ValueError:
            prix_achat = 0
        try:
            prix_vente = float(self._entry_prix_vente.text() or 0)
        except ValueError:
            erreur(self, "Erreur", "Le prix de vente est invalide.")
            return

        stock = self._spin_stock.value()
        alerte = self._spin_alerte.value()

        from modules.produits import Produit
        succes = Produit.modifier(
            self._produit_selectionne_id, nom, categorie,
            prix_achat, prix_vente, stock, alerte, description
        )

        if succes:
            information(self, "Succes", f"Produit '{nom}' modifie.")
            self._charger_categories()
            self._charger_page()
        else:
            erreur(self, "Erreur", "Impossible de modifier le produit.")

    def _supprimer_produit(self):
        """Supprimer le produit selectionne."""
        if not self._produit_selectionne_id:
            erreur(self, "Erreur", "Selectionnez un produit a supprimer.")
            return

        if not confirmer(self, "Confirmation", "Supprimer ce produit ?"):
            return

        from modules.produits import Produit
        succes = Produit.supprimer(self._produit_selectionne_id)

        if succes:
            information(self, "Succes", "Produit supprime.")
            self._reinitialiser_formulaire()
            self._charger_page()
        else:
            erreur(self, "Erreur", "Impossible de supprimer le produit.")

    def _voir_code_barre(self):
        """Ouvrir l'image du code-barres."""
        if not self._produit_selectionne_id:
            erreur(self, "Erreur", "Selectionnez un produit.")
            return

        from modules.produits import Produit
        p = Produit.obtenir_par_id(self._produit_selectionne_id)
        if not p or not p[7]:
            erreur(self, "Erreur", "Ce produit n'a pas de code-barres.")
            return

        from modules.codebarres import CodeBarre
        chemin = CodeBarre.obtenir_chemin_image(p[7])

        if not CodeBarre.code_barre_existe(p[7]):
            # Regenerer l'image
            try:
                CodeBarre.generer_image(p[7], p[1], p[4], p[8] or 'code128')
            except Exception:
                erreur(self, "Erreur", "Impossible de generer l'image du code-barres.")
                return

        QDesktopServices.openUrl(QUrl.fromLocalFile(chemin))

    def _reinitialiser_formulaire(self):
        self._produit_selectionne_id = None
        self._entry_nom.clear()
        self._entry_categorie.setCurrentIndex(-1)
        self._entry_categorie.setEditText("")
        self._entry_description.clear()
        self._entry_prix_achat.clear()
        self._entry_prix_vente.clear()
        self._spin_stock.setValue(0)
        self._spin_alerte.setValue(5)
        self._entry_code.clear()
        self._radio_auto.setChecked(True)
