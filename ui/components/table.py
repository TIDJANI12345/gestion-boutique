"""
Composant tableau reutilisable pour l'application.
QTableView preconfigure avec tri, filtrage et style.
"""
from PySide6.QtWidgets import (
    QTableView, QHeaderView, QAbstractItemView, QWidget,
    QVBoxLayout, QHBoxLayout, QLineEdit, QLabel
)
from PySide6.QtCore import (
    Qt, QSortFilterProxyModel, QModelIndex, Signal
)
from PySide6.QtGui import QStandardItemModel, QStandardItem


class BoutiqueTableModel(QStandardItemModel):
    """Modele de donnees pour les tableaux de l'application."""

    def __init__(self, colonnes: list[str], parent=None):
        super().__init__(0, len(colonnes), parent)
        self.setHorizontalHeaderLabels(colonnes)
        self._colonnes = colonnes

    def charger_donnees(self, lignes: list[list]):
        """Remplace toutes les donnees du modele.

        Args:
            lignes: Liste de listes, chaque sous-liste = une ligne.
        """
        self.removeRows(0, self.rowCount())
        for ligne in lignes:
            items = []
            for valeur in ligne:
                item = QStandardItem()
                if isinstance(valeur, (int, float)):
                    item.setData(valeur, Qt.DisplayRole)
                else:
                    item.setText(str(valeur) if valeur is not None else "")
                item.setEditable(False)
                items.append(item)
            self.appendRow(items)

    def ajouter_ligne(self, ligne: list):
        """Ajoute une ligne a la fin du modele."""
        items = []
        for valeur in ligne:
            item = QStandardItem()
            if isinstance(valeur, (int, float)):
                item.setData(valeur, Qt.DisplayRole)
            else:
                item.setText(str(valeur) if valeur is not None else "")
            item.setEditable(False)
            items.append(item)
        self.appendRow(items)

    def supprimer_ligne(self, row: int):
        """Supprime une ligne par son index."""
        self.removeRow(row)

    def obtenir_ligne(self, row: int) -> list:
        """Retourne les valeurs d'une ligne."""
        result = []
        for col in range(self.columnCount()):
            index = self.index(row, col)
            data = self.data(index, Qt.DisplayRole)
            result.append(data)
        return result


class BoutiqueTableView(QTableView):
    """QTableView preconfigure pour l'application.

    Fonctionnalites :
    - Tri par clic sur les en-tetes
    - Selection par ligne entiere
    - Lignes alternees
    - Redimensionnement intelligent des colonnes
    """

    ligne_selectionnee = Signal(int)  # index de la ligne source (pas proxy)
    ligne_double_clic = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Apparence
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setShowGrid(False)
        self.verticalHeader().setVisible(False)
        self.setSortingEnabled(True)

        # En-tetes
        header = self.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        header.setMinimumSectionSize(60)

        # Hauteur des lignes
        self.verticalHeader().setDefaultSectionSize(38)

        # Signaux
        self.clicked.connect(self._on_click)
        self.doubleClicked.connect(self._on_double_click)

    def _on_click(self, index: QModelIndex):
        source_index = self._map_to_source(index)
        self.ligne_selectionnee.emit(source_index.row())

    def _on_double_click(self, index: QModelIndex):
        source_index = self._map_to_source(index)
        self.ligne_double_clic.emit(source_index.row())

    def _map_to_source(self, index: QModelIndex) -> QModelIndex:
        """Convertit un index proxy vers l'index source."""
        model = self.model()
        if isinstance(model, QSortFilterProxyModel):
            return model.mapToSource(index)
        return index

    def ligne_courante(self) -> int:
        """Retourne l'index source de la ligne selectionnee, ou -1."""
        indexes = self.selectedIndexes()
        if not indexes:
            return -1
        return self._map_to_source(indexes[0]).row()

    def ajuster_colonnes(self):
        """Redimensionne les colonnes pour s'adapter au contenu."""
        for i in range(self.model().columnCount()):
            self.resizeColumnToContents(i)


class TableauRecherche(QWidget):
    """Widget combinant un champ de recherche et un tableau filtrable.

    Usage typique pour les listes de produits, clients, ventes, etc.
    """

    ligne_selectionnee = Signal(int)
    ligne_double_clic = Signal(int)

    def __init__(self, colonnes: list[str], placeholder: str = "Rechercher...",
                 parent=None):
        super().__init__(parent)

        self._model = BoutiqueTableModel(colonnes)
        self._proxy = QSortFilterProxyModel()
        self._proxy.setSourceModel(self._model)
        self._proxy.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self._proxy.setFilterKeyColumn(-1)  # Rechercher dans toutes les colonnes

        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Barre de recherche
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(0, 0, 0, 0)

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText(placeholder)
        self._search_input.setClearButtonEnabled(True)
        self._search_input.textChanged.connect(self._on_search)
        search_layout.addWidget(self._search_input)

        self._label_count = QLabel("0 elements")
        self._label_count.setStyleSheet("color: #6B7280; font-size: 12px;")
        search_layout.addWidget(self._label_count)

        layout.addLayout(search_layout)

        # Tableau
        self._table = BoutiqueTableView()
        self._table.setModel(self._proxy)
        self._table.ligne_selectionnee.connect(self.ligne_selectionnee.emit)
        self._table.ligne_double_clic.connect(self.ligne_double_clic.emit)
        layout.addWidget(self._table)

    @property
    def model(self) -> BoutiqueTableModel:
        return self._model

    @property
    def table(self) -> BoutiqueTableView:
        return self._table

    @property
    def proxy(self) -> QSortFilterProxyModel:
        return self._proxy

    def charger_donnees(self, lignes: list[list]):
        """Charge les donnees et met a jour le compteur."""
        self._model.charger_donnees(lignes)
        self._update_count()
        self._table.ajuster_colonnes()

    def _on_search(self, text: str):
        self._proxy.setFilterFixedString(text)
        self._update_count()

    def _update_count(self):
        total = self._model.rowCount()
        filtre = self._proxy.rowCount()
        if total == filtre:
            self._label_count.setText(f"{total} elements")
        else:
            self._label_count.setText(f"{filtre}/{total} elements")

    def ligne_courante(self) -> int:
        """Retourne l'index source de la ligne selectionnee, ou -1."""
        return self._table.ligne_courante()

    def obtenir_ligne(self, row: int) -> list:
        """Retourne les valeurs d'une ligne source."""
        return self._model.obtenir_ligne(row)

    def focus_recherche(self):
        """Met le focus sur le champ de recherche."""
        self._search_input.setFocus()
        self._search_input.selectAll()
