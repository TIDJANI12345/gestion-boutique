"""
Fenêtre d'import de produits depuis WhatsApp
"""
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                               QLabel, QLineEdit, QTableWidget, QTableWidgetItem,
                               QFileDialog, QMessageBox, QProgressDialog, QCheckBox,
                               QHeaderView, QWidget, QGroupBox, QFormLayout)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QColor
from modules.ia_extraction import IAExtraction, GEMINI_AVAILABLE
from modules.produits import Produit
from database import db
from modules.logger import get_logger
import os

logger = get_logger('import_whatsapp')


class ImportThread(QThread):
    """Thread pour traiter l'import en arrière-plan"""
    finished = Signal(list, str)  # produits, erreur

    def __init__(self, zip_path, api_key):
        super().__init__()
        self.zip_path = zip_path
        self.api_key = api_key

    def run(self):
        produits, err = IAExtraction.traiter_export_whatsapp(self.zip_path, self.api_key)
        self.finished.emit(produits, err)


class ImportWhatsAppWindow(QDialog):
    """Fenêtre d'import WhatsApp avec validation"""
    produits_importes = Signal(int)  # Nombre de produits importés

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import depuis WhatsApp")
        self.setMinimumSize(1000, 700)

        self.produits_extraits = []
        self.api_key = db.get_parametre('gemini_api_key', '')

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Info mode extraction
        info_label = QLabel("ℹ️ Mode extraction automatique (parsing basique)")
        info_label.setStyleSheet("background-color: #e3f2fd; padding: 10px; border-radius: 5px; color: #1976d2;")
        layout.addWidget(info_label)

        # Section import
        import_group = QGroupBox("Import de fichier")
        import_layout = QHBoxLayout()

        self.file_path_label = QLabel("Aucun fichier sélectionné")
        btn_parcourir = QPushButton("Parcourir...")
        btn_parcourir.clicked.connect(self.parcourir_fichier)

        btn_extraire = QPushButton("Extraire les produits")
        btn_extraire.clicked.connect(self.extraire_produits)
        btn_extraire.setStyleSheet("background-color: #2196F3; color: white; padding: 8px;")

        import_layout.addWidget(self.file_path_label, 1)
        import_layout.addWidget(btn_parcourir)
        import_layout.addWidget(btn_extraire)

        import_group.setLayout(import_layout)
        layout.addWidget(import_group)

        # Table des produits
        table_label = QLabel("Produits extraits (double-clic pour éditer)")
        table_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(table_label)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "✓", "Nom", "Prix (FCFA)", "Catégorie", "Code-barre",
            "Type", "Confiance"
        ])

        # Configuration colonnes
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Checkbox
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Nom
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Prix
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Catégorie
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Code-barre
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Type
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Confiance

        self.table.setAlternatingRowColors(True)
        self.table.itemChanged.connect(self.on_table_edit)

        layout.addWidget(self.table)

        # Statistiques
        self.stats_label = QLabel("Aucun produit extrait")
        self.stats_label.setStyleSheet("color: #666; padding: 5px;")
        layout.addWidget(self.stats_label)

        # Boutons d'action
        btn_layout = QHBoxLayout()

        btn_tout_selectionner = QPushButton("Tout sélectionner")
        btn_tout_selectionner.clicked.connect(self.tout_selectionner)

        btn_tout_deselectionner = QPushButton("Tout désélectionner")
        btn_tout_deselectionner.clicked.connect(self.tout_deselectionner)

        btn_supprimer = QPushButton("Supprimer sélection")
        btn_supprimer.clicked.connect(self.supprimer_selection)
        btn_supprimer.setStyleSheet("background-color: #f44336; color: white;")

        btn_importer = QPushButton("Importer en base de données")
        btn_importer.clicked.connect(self.importer_produits)
        btn_importer.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px; font-weight: bold;")

        btn_annuler = QPushButton("Fermer")
        btn_annuler.clicked.connect(self.reject)

        btn_layout.addWidget(btn_tout_selectionner)
        btn_layout.addWidget(btn_tout_deselectionner)
        btn_layout.addWidget(btn_supprimer)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_importer)
        btn_layout.addWidget(btn_annuler)

        layout.addLayout(btn_layout)

    def parcourir_fichier(self):
        """Sélectionner un fichier ZIP"""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Sélectionner l'export WhatsApp",
            "",
            "Fichiers ZIP (*.zip)"
        )

        if filepath:
            self.file_path_label.setText(filepath)

    def extraire_produits(self):
        """Extraire les produits du fichier"""
        filepath = self.file_path_label.text()

        if filepath == "Aucun fichier sélectionné" or not os.path.exists(filepath):
            QMessageBox.warning(self, "Erreur", "Sélectionnez un fichier ZIP valide")
            return

        # Progress dialog
        self.progress = QProgressDialog("Extraction en cours (mode basique)...", None, 0, 0, self)
        self.progress.setWindowModality(Qt.WindowModal)
        self.progress.setCancelButton(None)
        self.progress.show()

        # Lancer thread (sans API key = mode basique)
        self.import_thread = ImportThread(filepath, None)
        self.import_thread.finished.connect(self.on_extraction_terminee)
        self.import_thread.start()

    def on_extraction_terminee(self, produits, erreur):
        """Callback quand l'extraction est terminée"""
        self.progress.close()

        if erreur != "OK":
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'extraction:\n{erreur}")
            return

        if not produits:
            QMessageBox.information(self, "Résultat", "Aucun produit trouvé dans les messages")
            return

        self.produits_extraits = produits
        self.afficher_produits()

    def afficher_produits(self):
        """Afficher les produits dans la table"""
        self.table.setRowCount(0)
        self.table.blockSignals(True)

        for i, produit in enumerate(self.produits_extraits):
            self.table.insertRow(i)

            # Checkbox
            checkbox = QCheckBox()
            checkbox.setChecked(True)
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.setAlignment(Qt.AlignCenter)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(i, 0, checkbox_widget)

            # Données
            self.table.setItem(i, 1, QTableWidgetItem(produit.get('nom', '')))
            self.table.setItem(i, 2, QTableWidgetItem(str(produit.get('prix', 0))))
            self.table.setItem(i, 3, QTableWidgetItem(produit.get('categorie_suggeree', '')))

            code = produit.get('code_barre', '')
            self.table.setItem(i, 4, QTableWidgetItem(code if code else '(auto)'))

            type_code = produit.get('type_code_barre', 'code128')
            self.table.setItem(i, 5, QTableWidgetItem(type_code))

            # Confiance avec couleur
            confiance = produit.get('confiance', 0.5)
            item_conf = QTableWidgetItem(f"{confiance:.0%}")
            if confiance >= 0.8:
                item_conf.setBackground(QColor("#c8e6c9"))  # Vert
            elif confiance >= 0.6:
                item_conf.setBackground(QColor("#fff9c4"))  # Jaune
            else:
                item_conf.setBackground(QColor("#ffcdd2"))  # Rouge
            self.table.setItem(i, 6, item_conf)

        self.table.blockSignals(False)

        # Stats
        total = len(self.produits_extraits)
        avec_code = sum(1 for p in self.produits_extraits if p.get('code_barre'))
        self.stats_label.setText(
            f"📊 {total} produits extraits | "
            f"{avec_code} avec code-barre | "
            f"{total - avec_code} sans code-barre (génération auto)"
        )

    def on_table_edit(self, item):
        """Mettre à jour le produit quand la table est éditée"""
        row = item.row()
        col = item.column()

        if col == 1:  # Nom
            self.produits_extraits[row]['nom'] = item.text()
        elif col == 2:  # Prix
            try:
                self.produits_extraits[row]['prix'] = float(item.text())
            except ValueError:
                pass
        elif col == 3:  # Catégorie
            self.produits_extraits[row]['categorie_suggeree'] = item.text()
        elif col == 4:  # Code-barre
            code = item.text()
            if code and code != '(auto)':
                self.produits_extraits[row]['code_barre'] = code
            else:
                self.produits_extraits[row]['code_barre'] = None

    def tout_selectionner(self):
        """Sélectionner tous les produits"""
        for i in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(i, 0).findChild(QCheckBox)
            checkbox.setChecked(True)

    def tout_deselectionner(self):
        """Désélectionner tous les produits"""
        for i in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(i, 0).findChild(QCheckBox)
            checkbox.setChecked(False)

    def supprimer_selection(self):
        """Supprimer les lignes sélectionnées"""
        indices_a_supprimer = []
        for i in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(i, 0).findChild(QCheckBox)
            if checkbox.isChecked():
                indices_a_supprimer.append(i)

        if not indices_a_supprimer:
            return

        reply = QMessageBox.question(
            self,
            "Confirmation",
            f"Supprimer {len(indices_a_supprimer)} produit(s) de la liste ?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            for i in reversed(indices_a_supprimer):
                del self.produits_extraits[i]
            self.afficher_produits()

    def importer_produits(self):
        """Importer les produits sélectionnés en base"""
        produits_a_importer = []

        for i in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(i, 0).findChild(QCheckBox)
            if checkbox.isChecked():
                produits_a_importer.append(self.produits_extraits[i])

        if not produits_a_importer:
            QMessageBox.warning(self, "Attention", "Aucun produit sélectionné")
            return

        # Confirmation
        reply = QMessageBox.question(
            self,
            "Confirmation",
            f"Importer {len(produits_a_importer)} produit(s) en base de données ?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        # Importer
        succes = 0
        erreurs = []

        for produit in produits_a_importer:
            nom = produit.get('nom', '').strip()
            prix = float(produit.get('prix', 0))
            categorie = produit.get('categorie_suggeree', 'Non catégorisé')
            code_barre = produit.get('code_barre')
            type_code = produit.get('type_code_barre', 'code128')
            description = produit.get('description', '')

            # Validation
            if not nom or prix <= 0:
                erreurs.append(f"{nom}: nom ou prix invalide")
                continue

            # Générer code-barre si absent
            if not code_barre:
                code_barre = Produit.generer_code_barre(type_code)

            # Vérifier doublon
            if Produit.code_barre_existe(code_barre):
                erreurs.append(f"{nom}: code-barre {code_barre} existe déjà")
                continue

            # Ajouter
            result = Produit.ajouter(
                nom=nom,
                categorie=categorie,
                prix_achat=0,
                prix_vente=prix,
                stock_actuel=0,
                stock_alerte=5,
                code_barre=code_barre,
                type_code_barre=type_code,
                description=description
            )

            if result:
                succes += 1
            else:
                erreurs.append(f"{nom}: erreur lors de l'ajout")

        # Résultat
        msg = f"✅ {succes} produit(s) importé(s) avec succès"
        if erreurs:
            msg += f"\n\n❌ {len(erreurs)} erreur(s):\n" + "\n".join(erreurs[:10])
            if len(erreurs) > 10:
                msg += f"\n... et {len(erreurs) - 10} autres"

        QMessageBox.information(self, "Résultat de l'import", msg)

        if succes > 0:
            self.produits_importes.emit(succes)
            self.accept()
