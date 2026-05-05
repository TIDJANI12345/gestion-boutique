"""
Fenêtre d'import CSV de produits en lot.
"""
import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QFileDialog, QProgressBar, QGroupBox, QTextEdit, QFrame
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor, QFont

from modules.import_csv import analyser_csv, importer_lignes, modele_csv, ENTETES_TOUS


class _ImportThread(QThread):
    finished = Signal(int, int, list)

    def __init__(self, lignes):
        super().__init__()
        self.lignes = lignes

    def run(self):
        nb_ok, nb_err, msgs = importer_lignes(self.lignes)
        self.finished.emit(nb_ok, nb_err, msgs)


class ImportCSVWindow(QDialog):
    import_termine = Signal(int)  # nb produits ajoutés

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import CSV — Produits en lot")
        self.resize(900, 620)
        self._lignes = []
        self._thread = None
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # === Étape 1 : Choisir le fichier ===
        grp_fichier = QGroupBox("1. Choisir le fichier CSV")
        fl = QHBoxLayout(grp_fichier)

        self._lbl_fichier = QLabel("Aucun fichier sélectionné")
        self._lbl_fichier.setStyleSheet("color: #6B7280;")
        fl.addWidget(self._lbl_fichier, 1)

        btn_parcourir = QPushButton("Parcourir…")
        btn_parcourir.clicked.connect(self._choisir_fichier)
        fl.addWidget(btn_parcourir)

        btn_modele = QPushButton("Télécharger le modèle")
        btn_modele.setStyleSheet(
            "background-color: #3B82F6; color: white; border-radius: 4px; padding: 4px 10px;"
        )
        btn_modele.clicked.connect(self._telecharger_modele)
        fl.addWidget(btn_modele)

        layout.addWidget(grp_fichier)

        # === Info colonnes ===
        info = QLabel(
            f"Colonnes reconnues : {', '.join(ENTETES_TOUS)}"
            "  •  Séparateur : <b>;</b> ou <b>,</b>  •  Encodage : UTF-8"
        )
        info.setTextFormat(Qt.RichText)
        info.setStyleSheet("color: #6B7280; font-size: 11px; padding: 2px 4px;")
        layout.addWidget(info)

        # === Étape 2 : Prévisualisation ===
        grp_preview = QGroupBox("2. Prévisualisation et validation")
        pv = QVBoxLayout(grp_preview)

        self._lbl_resume = QLabel("—")
        self._lbl_resume.setStyleSheet("font-size: 12px; padding: 2px;")
        pv.addWidget(self._lbl_resume)

        self._table = QTableWidget()
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        pv.addWidget(self._table)

        layout.addWidget(grp_preview, 1)

        # === Étape 3 : Résultat ===
        self._grp_resultat = QGroupBox("3. Résultat")
        rl = QVBoxLayout(self._grp_resultat)
        self._txt_resultat = QTextEdit()
        self._txt_resultat.setReadOnly(True)
        self._txt_resultat.setMaximumHeight(100)
        rl.addWidget(self._txt_resultat)
        self._grp_resultat.hide()
        layout.addWidget(self._grp_resultat)

        # Barre de progression
        self._progress = QProgressBar()
        self._progress.setRange(0, 0)
        self._progress.hide()
        layout.addWidget(self._progress)

        # Boutons bas
        btn_row = QHBoxLayout()
        self._btn_importer = QPushButton("Importer les lignes valides")
        self._btn_importer.setEnabled(False)
        self._btn_importer.setStyleSheet(
            "background-color: #22C55E; color: white; font-weight: bold;"
            " padding: 6px 16px; border-radius: 4px;"
        )
        self._btn_importer.clicked.connect(self._lancer_import)
        btn_row.addWidget(self._btn_importer)
        btn_row.addStretch()

        btn_fermer = QPushButton("Fermer")
        btn_fermer.clicked.connect(self.accept)
        btn_row.addWidget(btn_fermer)
        layout.addLayout(btn_row)

    # ------------------------------------------------------------------ #
    # Actions                                                              #
    # ------------------------------------------------------------------ #

    def _telecharger_modele(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Enregistrer le modèle", "modele_produits.csv",
            "Fichiers CSV (*.csv)"
        )
        if not path:
            return
        try:
            with open(path, 'w', encoding='utf-8-sig', newline='') as f:
                f.write(modele_csv())
            QMessageBox.information(self, "Modèle enregistré", f"Fichier sauvegardé :\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))

    def _choisir_fichier(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Choisir un fichier CSV", "",
            "Fichiers CSV (*.csv *.txt)"
        )
        if not path:
            return

        self._lbl_fichier.setText(os.path.basename(path))
        self._lbl_fichier.setStyleSheet("color: #1F2937; font-weight: bold;")

        try:
            with open(path, encoding='utf-8-sig', errors='replace') as f:
                contenu = f.read()
        except Exception as e:
            QMessageBox.critical(self, "Erreur de lecture", str(e))
            return

        self._analyser(contenu)

    def _analyser(self, contenu: str):
        from modules.import_csv import analyser_csv
        lignes, erreurs_globales = analyser_csv(contenu)

        if erreurs_globales:
            QMessageBox.critical(
                self, "Erreur de format",
                "\n".join(erreurs_globales)
            )
            self._btn_importer.setEnabled(False)
            return

        self._lignes = lignes
        nb_valides = sum(1 for l in lignes if l.valide)
        nb_erreurs = len(lignes) - nb_valides

        couleur = "#22C55E" if nb_erreurs == 0 else "#F59E0B"
        self._lbl_resume.setText(
            f"<span style='color:{couleur};'>"
            f"{len(lignes)} lignes lues — "
            f"<b>{nb_valides} valides</b>, {nb_erreurs} avec erreurs"
            f"</span>"
        )
        self._lbl_resume.setTextFormat(Qt.RichText)

        self._remplir_table(lignes)
        self._btn_importer.setEnabled(nb_valides > 0)
        self._grp_resultat.hide()

    def _remplir_table(self, lignes):
        cols = ['#', 'Statut', 'nom', 'categorie', 'prix_achat', 'prix_vente',
                'stock_actuel', 'stock_alerte', 'code_barre', 'unite_mesure', 'Erreurs']
        self._table.setColumnCount(len(cols))
        self._table.setHorizontalHeaderLabels(cols)
        self._table.setRowCount(len(lignes))

        for i, ligne in enumerate(lignes):
            d = ligne.donnees
            self._table.setItem(i, 0, QTableWidgetItem(str(ligne.numero)))
            statut = "✓" if ligne.valide else "✗"
            si = QTableWidgetItem(statut)
            si.setForeground(QColor("#22C55E" if ligne.valide else "#EF4444"))
            si.setFont(QFont("Segoe UI", 10, QFont.Bold))
            self._table.setItem(i, 1, si)
            self._table.setItem(i, 2, QTableWidgetItem(str(d.get('nom', ''))))
            self._table.setItem(i, 3, QTableWidgetItem(str(d.get('categorie', ''))))
            self._table.setItem(i, 4, QTableWidgetItem(str(d.get('prix_achat', ''))))
            self._table.setItem(i, 5, QTableWidgetItem(str(d.get('prix_vente', ''))))
            self._table.setItem(i, 6, QTableWidgetItem(str(d.get('stock_actuel', ''))))
            self._table.setItem(i, 7, QTableWidgetItem(str(d.get('stock_alerte', ''))))
            self._table.setItem(i, 8, QTableWidgetItem(str(d.get('code_barre', ''))))
            self._table.setItem(i, 9, QTableWidgetItem(str(d.get('unite_mesure', ''))))
            err_item = QTableWidgetItem('; '.join(ligne.erreurs))
            if not ligne.valide:
                err_item.setForeground(QColor("#EF4444"))
                for col in range(self._table.columnCount()):
                    item = self._table.item(i, col)
                    if item:
                        item.setBackground(QColor("#FEF2F2"))
            self._table.setItem(i, 10, err_item)

    def _lancer_import(self):
        valides = [l for l in self._lignes if l.valide]
        if not valides:
            return

        rep = QMessageBox.question(
            self, "Confirmer l'import",
            f"Importer <b>{len(valides)}</b> produit(s) ?",
            QMessageBox.Yes | QMessageBox.No
        )
        if rep != QMessageBox.Yes:
            return

        self._btn_importer.setEnabled(False)
        self._progress.show()

        self._thread = _ImportThread(valides)
        self._thread.finished.connect(self._on_import_fini)
        self._thread.start()

    def _on_import_fini(self, nb_ok: int, nb_err: int, msgs: list):
        self._progress.hide()
        self._grp_resultat.show()

        lignes = [f"✓ {nb_ok} produit(s) importé(s) avec succès."]
        if nb_err:
            lignes.append(f"✗ {nb_err} ligne(s) ignorée(s).")
        if msgs:
            lignes += msgs

        self._txt_resultat.setPlainText('\n'.join(lignes))

        if nb_ok > 0:
            self.import_termine.emit(nb_ok)
            self._btn_importer.setEnabled(False)
        else:
            self._btn_importer.setEnabled(True)
