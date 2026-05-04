"""
Fenetre de ventes - PySide6
Panier en memoire, paiement, transaction DB atomique.
"""
from datetime import datetime

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QMessageBox, QWidget, QListWidget,
    QListWidgetItem, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QShortcut, QKeySequence

from ui.theme import Theme
from ui.components.dialogs import DialogueQuantite, confirmer
from ui.components.camera_widget import CameraWidget


class VentesWindow(QDialog):
    """Fenetre de vente - panier en memoire, validation atomique."""

    vente_terminee = Signal()

    def __init__(self, parent=None, utilisateur=None):
        super().__init__(parent)
        try:
            self.setWindowTitle("Nouvelle Vente")
            self.setMinimumSize(1200, 700)
            self.setModal(True)

            self.panier: list[dict] = []
            self.client_id = None
            self.client_selectionne = None
            self.utilisateur = utilisateur
            self._remise_valeur = 0.0   # valeur saisie
            self._remise_montant = 0.0  # montant en FCFA calculé
            self._remise_pct = True     # True=%, False=montant fixe

            self._session_id = None  # rattaché à la session active

            self._setup_ui()
            self._verifier_session()

            for btn in self.findChildren(QPushButton):
                btn.setAutoDefault(False)
                btn.setDefault(False)

            self._setup_raccourcis()
            self._actualiser_panier()
            self._check_camera_auto()

            QTimer.singleShot(0, self._entry_scan.setFocus)
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Erreur Critique", f"Impossible d'ouvrir la fenêtre de vente:\n\n{e}")


    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # En-tete
        header = QFrame()
        header.setFixedHeight(70)
        header.setStyleSheet(f"background-color: {Theme.c('success')};")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(30, 0, 30, 0)

        titre = QLabel("Nouvelle Vente")
        titre.setFont(QFont("Segoe UI", 22, QFont.Bold))
        titre.setStyleSheet("color: white; background: transparent;")
        header_layout.addWidget(titre)

        header_layout.addStretch()

        self._label_panier_status = QLabel("Panier en cours...")
        self._label_panier_status.setFont(QFont("Segoe UI", 14))
        self._label_panier_status.setStyleSheet("color: white; background: transparent;")
        header_layout.addWidget(self._label_panier_status)

        layout.addWidget(header)

        # Conteneur principal 2 colonnes
        main = QWidget()
        main_layout = QHBoxLayout(main)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # === COLONNE GAUCHE ===
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(15)

        # Scanner
        scanner_frame = QFrame()
        scanner_frame.setStyleSheet(
            f"QFrame {{ background-color: {Theme.c('card_bg')}; "
            f"border: 1px solid {Theme.c('card_border')}; border-radius: 8px; }}"
        )
        scanner_layout = QVBoxLayout(scanner_frame)
        scanner_layout.setContentsMargins(20, 20, 20, 20)

        lbl_scanner = QLabel("Scanner un code-barre")
        lbl_scanner.setFont(QFont("Segoe UI", 14, QFont.Bold))
        scanner_layout.addWidget(lbl_scanner)

        scan_row = QHBoxLayout()
        self._entry_scan = QLineEdit()
        self._entry_scan.setFont(QFont("Segoe UI", 14))
        self._entry_scan.setPlaceholderText("Saisir ou scanner un code-barres...")
        self._entry_scan.returnPressed.connect(self._scanner_produit)
        self._entry_scan.textChanged.connect(self._on_scan_text_changed)
        scan_row.addWidget(self._entry_scan)

        self._btn_camera = QPushButton("📷 Caméra")
        self._btn_camera.setStyleSheet(
            f"background-color: {Theme.c('info')}; color: white; "
            f"border: none; border-radius: 6px; padding: 10px 16px;"
        )
        self._btn_camera.setCursor(Qt.PointingHandCursor)
        self._btn_camera.setAutoDefault(False)
        self._btn_camera.setDefault(False)
        self._btn_camera.clicked.connect(self._ouvrir_scanner_camera)
        scan_row.addWidget(self._btn_camera)

        scanner_layout.addLayout(scan_row)

        lbl_hint = QLabel("Scannez ou tapez le code-barres puis appuyez sur ENTREE")
        lbl_hint.setFont(QFont("Segoe UI", 9))
        lbl_hint.setStyleSheet(f"color: {Theme.c('gray')};")
        scanner_layout.addWidget(lbl_hint)

        left_layout.addWidget(scanner_frame)

        # Panier (tableau)
        panier_frame = QFrame()
        panier_frame.setStyleSheet(
            f"QFrame {{ background-color: {Theme.c('card_bg')}; "
            f"border: 1px solid {Theme.c('card_border')}; border-radius: 8px; }}"
        )
        panier_layout = QVBoxLayout(panier_frame)
        panier_layout.setContentsMargins(15, 15, 15, 15)

        panier_header = QHBoxLayout()
        lbl_panier = QLabel("Panier")
        lbl_panier.setFont(QFont("Segoe UI", 14, QFont.Bold))
        panier_header.addWidget(lbl_panier)
        panier_header.addStretch()

        btn_vider = QPushButton("Vider")
        btn_vider.setProperty("class", "danger")
        btn_vider.setCursor(Qt.PointingHandCursor)
        btn_vider.clicked.connect(self._vider_panier)
        panier_header.addWidget(btn_vider)

        panier_layout.addLayout(panier_header)

        # Label panier vide
        self._label_vide = QLabel("Le panier est vide\n\nScannez un produit pour commencer")
        self._label_vide.setFont(QFont("Segoe UI", 11))
        self._label_vide.setStyleSheet(f"color: {Theme.c('gray')};")
        self._label_vide.setAlignment(Qt.AlignCenter)
        self._label_vide.setMinimumHeight(80)
        panier_layout.addWidget(self._label_vide)

        # Zone scrollable des articles
        self._scroll_panier = QScrollArea()
        self._scroll_panier.setWidgetResizable(True)
        self._scroll_panier.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self._scroll_panier.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._panier_container = QWidget()
        self._panier_container.setStyleSheet("background: transparent;")
        self._panier_items_layout = QVBoxLayout(self._panier_container)
        self._panier_items_layout.setContentsMargins(0, 0, 0, 0)
        self._panier_items_layout.setSpacing(4)
        self._panier_items_layout.addStretch()

        self._scroll_panier.setWidget(self._panier_container)
        self._scroll_panier.setVisible(False)
        panier_layout.addWidget(self._scroll_panier)

        left_layout.addWidget(panier_frame, 1)
        main_layout.addWidget(left, 1)

        # === COLONNE DROITE ===
        right = QWidget()
        right.setFixedWidth(350)
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(15)

        # Resume
        resume_frame = QFrame()
        resume_frame.setStyleSheet(
            f"QFrame {{ background-color: {Theme.c('card_bg')}; "
            f"border: 1px solid {Theme.c('card_border')}; border-radius: 8px; }}"
        )
        resume_layout = QVBoxLayout(resume_frame)
        resume_layout.setContentsMargins(20, 15, 20, 20)

        lbl_resume = QLabel("Resume")
        lbl_resume.setFont(QFont("Segoe UI", 14, QFont.Bold))
        resume_layout.addWidget(lbl_resume)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet(f"color: {Theme.c('separator')};")
        resume_layout.addWidget(sep2)

        # Articles
        row_articles = QHBoxLayout()
        row_articles.addWidget(QLabel("Articles:"))
        self._label_nb_articles = QLabel("0")
        self._label_nb_articles.setFont(QFont("Segoe UI", 11, QFont.Bold))
        row_articles.addStretch()
        row_articles.addWidget(self._label_nb_articles)
        resume_layout.addLayout(row_articles)

        sep3 = QFrame()
        sep3.setFrameShape(QFrame.HLine)
        sep3.setStyleSheet(f"color: {Theme.c('separator')};")
        resume_layout.addWidget(sep3)

        # Sous-total
        row_soustotal = QHBoxLayout()
        lbl_st = QLabel("Sous-total:")
        lbl_st.setFont(QFont("Segoe UI", 10))
        row_soustotal.addWidget(lbl_st)
        row_soustotal.addStretch()
        self._label_soustotal = QLabel("0")
        self._label_soustotal.setFont(QFont("Segoe UI", 10))
        row_soustotal.addWidget(self._label_soustotal)
        resume_layout.addLayout(row_soustotal)

        # Remise
        remise_row = QHBoxLayout()
        lbl_remise = QLabel("Remise:")
        lbl_remise.setFont(QFont("Segoe UI", 10))
        remise_row.addWidget(lbl_remise)
        remise_row.addStretch()
        self._entry_remise = QLineEdit()
        self._entry_remise.setPlaceholderText("0")
        self._entry_remise.setFixedWidth(70)
        self._entry_remise.setFont(QFont("Segoe UI", 10))
        self._entry_remise.setStyleSheet(
            f"padding: 4px; border: 1px solid {Theme.c('gray')}; border-radius: 4px;"
        )
        self._entry_remise.textChanged.connect(self._on_remise_changed)
        remise_row.addWidget(self._entry_remise)
        self._btn_remise_mode = QPushButton("%")
        self._btn_remise_mode.setFixedSize(36, 28)
        self._btn_remise_mode.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self._btn_remise_mode.setCursor(Qt.PointingHandCursor)
        self._btn_remise_mode.setAutoDefault(False)
        self._btn_remise_mode.setStyleSheet(
            f"background-color: {Theme.c('info')}; color: white; "
            f"border: none; border-radius: 4px;"
        )
        self._btn_remise_mode.clicked.connect(self._toggle_remise_mode)
        remise_row.addWidget(self._btn_remise_mode)
        resume_layout.addLayout(remise_row)

        # Montant remise calculé (affiché en rouge si > 0)
        self._label_remise_montant = QLabel("")
        self._label_remise_montant.setFont(QFont("Segoe UI", 9))
        self._label_remise_montant.setStyleSheet(f"color: {Theme.c('danger')};")
        self._label_remise_montant.setAlignment(Qt.AlignRight)
        resume_layout.addWidget(self._label_remise_montant)

        sep_remise = QFrame()
        sep_remise.setFrameShape(QFrame.HLine)
        sep_remise.setStyleSheet(f"color: {Theme.c('separator')};")
        resume_layout.addWidget(sep_remise)

        # Total
        row_total = QHBoxLayout()
        lbl_total_label = QLabel("TOTAL:")
        lbl_total_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        row_total.addWidget(lbl_total_label)
        row_total.addStretch()

        self._label_total = QLabel("0")
        self._label_total.setFont(QFont("Segoe UI", 20, QFont.Bold))
        self._label_total.setStyleSheet(f"color: {Theme.c('success')};")
        row_total.addWidget(self._label_total)

        resume_layout.addLayout(row_total)

        # Separateur camera
        sep_camera = QFrame()
        sep_camera.setFrameShape(QFrame.HLine)
        sep_camera.setStyleSheet(f"color: {Theme.c('separator')};")
        resume_layout.addWidget(sep_camera)

        # Bouton toggle camera
        self.btn_toggle_camera = QPushButton("📷 Afficher caméra")
        self.btn_toggle_camera.setObjectName("toggleCamera")
        self.btn_toggle_camera.setCheckable(True)
        self.btn_toggle_camera.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.c('info')};
                color: white;
                font-size: 10pt;
                padding: 8px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {Theme.c('primary')};
            }}
        """)
        self.btn_toggle_camera.clicked.connect(self._toggle_camera_widget)
        resume_layout.addWidget(self.btn_toggle_camera)

        right_layout.addWidget(resume_frame)

        # Widget camera integre (masque par defaut)
        self._camera_widget = CameraWidget()
        self._camera_widget.code_scanne.connect(self._traiter_code_camera)
        self._camera_widget.hide()  # Masquer par defaut
        right_layout.addWidget(self._camera_widget)

        # Actions
        actions_frame = QFrame()
        actions_frame.setStyleSheet(
            f"QFrame {{ background-color: {Theme.c('card_bg')}; "
            f"border: 1px solid {Theme.c('card_border')}; border-radius: 8px; }}"
        )
        actions_layout = QVBoxLayout(actions_frame)
        actions_layout.setContentsMargins(20, 20, 20, 20)
        actions_layout.setSpacing(10)

        # Bouton valider
        btn_valider = QPushButton("Valider la vente")
        btn_valider.setFont(QFont("Segoe UI", 14, QFont.Bold))
        btn_valider.setMinimumHeight(60)
        btn_valider.setCursor(Qt.PointingHandCursor)
        btn_valider.setProperty("class", "success")
        btn_valider.clicked.connect(self._valider_vente)
        actions_layout.addWidget(btn_valider)

        # Client
        lbl_client = QLabel("Client (optionnel)")
        lbl_client.setFont(QFont("Segoe UI", 10, QFont.Bold))
        actions_layout.addWidget(lbl_client)

        client_row = QHBoxLayout()
        self._entry_client = QLineEdit()
        self._entry_client.setPlaceholderText("Rechercher un client...")
        self._entry_client.textChanged.connect(self._rechercher_client)
        client_row.addWidget(self._entry_client)

        btn_clear_client = QPushButton("X")
        btn_clear_client.setFixedWidth(36)
        btn_clear_client.setStyleSheet(
            f"background-color: {Theme.c('gray')}; color: white; "
            f"border: none; border-radius: 4px;"
        )
        btn_clear_client.setCursor(Qt.PointingHandCursor)
        btn_clear_client.clicked.connect(self._effacer_client)
        client_row.addWidget(btn_clear_client)

        actions_layout.addLayout(client_row)

        # Liste dropdown clients
        self._list_clients = QListWidget()
        self._list_clients.setMaximumHeight(130)
        self._list_clients.setVisible(False)
        self._list_clients.itemClicked.connect(self._selectionner_client)
        actions_layout.addWidget(self._list_clients)

        # Label fidelite
        self._label_fidelite = QLabel("")
        self._label_fidelite.setFont(QFont("Segoe UI", 9))
        self._label_fidelite.setStyleSheet(f"color: {Theme.c('primary')};")
        actions_layout.addWidget(self._label_fidelite)

        actions_layout.addStretch()

        # Bouton annuler
        btn_annuler = QPushButton("Annuler la vente")
        btn_annuler.setFont(QFont("Segoe UI", 11))
        btn_annuler.setMinimumHeight(45)
        btn_annuler.setCursor(Qt.PointingHandCursor)
        btn_annuler.setProperty("class", "danger")
        btn_annuler.clicked.connect(self._annuler_vente)
        actions_layout.addWidget(btn_annuler)

        right_layout.addWidget(actions_frame, 1)
        main_layout.addWidget(right)

        layout.addWidget(main, 1)

        # Barre de raccourcis
        shortcuts_bar = QFrame()
        shortcuts_bar.setStyleSheet(f"background-color: {Theme.c('light')}; padding: 8px;")
        shortcuts_layout = QHBoxLayout(shortcuts_bar)
        shortcuts_layout.setContentsMargins(15, 5, 15, 5)

        shortcuts_text = QLabel(
            "⌨️ Raccourcis : F5=Focus scan | F6=Caméra | F2=Valider | F8=Annuler | F9=Mode scan | Ctrl+Entrée=Valider"
        )
        shortcuts_text.setStyleSheet(f"color: {Theme.c('gray')}; font-size: 9pt;")
        shortcuts_layout.addWidget(shortcuts_text)
        shortcuts_layout.addStretch()

        layout.addWidget(shortcuts_bar)

    def _setup_raccourcis(self):
        # F5: Focus sur le champ de scan
        QShortcut(QKeySequence("F5"), self).activated.connect(
            self._entry_scan.setFocus
        )

        # F6: Ouvrir scanner caméra
        QShortcut(QKeySequence("F6"), self).activated.connect(
            self._ouvrir_scanner_camera
        )

        # F2 ou Ctrl+Entrée: Valider la vente
        QShortcut(QKeySequence("F2"), self).activated.connect(
            self._valider_vente
        )
        QShortcut(QKeySequence("Ctrl+Return"), self).activated.connect(
            self._valider_vente
        )

        # F8: Annuler la vente
        QShortcut(QKeySequence("F8"), self).activated.connect(
            self._annuler_vente
        )

        # F9: Basculer mode scan AUTO/MANUEL
        QShortcut(QKeySequence("F9"), self).activated.connect(
            self._toggle_mode_scan
        )

    # === SCANNER ===

    def _on_scan_text_changed(self, texte: str):
        if texte.strip():
            self._btn_camera.setText("↵ Valider")
            self._btn_camera.setStyleSheet(
                f"background-color: {Theme.c('success')}; color: white; "
                f"border: none; border-radius: 6px; padding: 10px 16px;"
            )
            self._btn_camera.clicked.disconnect()
            self._btn_camera.clicked.connect(self._scanner_produit)
        else:
            self._btn_camera.setText("📷 Caméra")
            self._btn_camera.setStyleSheet(
                f"background-color: {Theme.c('info')}; color: white; "
                f"border: none; border-radius: 6px; padding: 10px 16px;"
            )
            self._btn_camera.clicked.disconnect()
            self._btn_camera.clicked.connect(self._ouvrir_scanner_camera)

    def _scanner_produit(self):
        """Scanner un code-barre et ajouter au panier."""
        code_barre = self._entry_scan.text().strip()
        if not code_barre:
            return

        from modules.produits import Produit
        produit = Produit.obtenir_par_code_barre(code_barre)

        if not produit:
            QMessageBox.critical(
                self, "Erreur",
                f"Produit introuvable!\nCode: {code_barre}"
            )
            self._entry_scan.clear()
            return

        # Verifier le stock disponible
        stock_disponible = produit['stock_actuel']
        if stock_disponible <= 0:
            QMessageBox.critical(self, "Stock", "Produit en rupture de stock!")
            self._entry_scan.clear()
            return

        # Vérifier le mode de scan (AUTO ou MANUEL)
        from database import db
        mode_auto = db.get_parametre('mode_scan_auto', '1') == '1'  # Défaut AUTO

        if mode_auto:
            # Mode AUTOMATIQUE : verifier qu'il y a au moins 1 en stock
            if stock_disponible < 1:
                QMessageBox.critical(self, "Stock", "Stock insuffisant!")
                self._entry_scan.clear()
                return
            # Ajout direct quantité 1
            self._ajouter_au_panier(produit, 1)
            self._flash_ligne_ajoutee(produit['id'])  # Feedback visuel
        else:
            # Mode MANUEL : demander la quantité
            qte, ok = DialogueQuantite.saisir(
                self,
                f"Quantite - {produit['nom']}",
                f"Stock disponible: {produit['stock_actuel']}",
                valeur=1, minimum=1, maximum=produit['stock_actuel']
            )

            if ok and qte > 0:
                self._ajouter_au_panier(produit, qte)

        self._entry_scan.clear()
        self._entry_scan.setFocus()

    def _traiter_code_camera(self, code_barre: str):
        """Traiter un code scanné par la caméra intégrée."""
        if not code_barre:
            return

        from modules.produits import Produit
        produit = Produit.obtenir_par_code_barre(code_barre)

        if not produit:
            QMessageBox.critical(
                self, "Erreur",
                f"Produit introuvable!\nCode: {code_barre}"
            )
            return

        # Vérifier le stock disponible
        stock_disponible = produit['stock_actuel']
        if stock_disponible <= 0:
            QMessageBox.critical(self, "Stock", "Produit en rupture de stock!")
            return

        # Vérifier le mode de scan (AUTO ou MANUEL)
        from database import db
        mode_auto = db.get_parametre('mode_scan_auto', '1') == '1'

        if mode_auto:
            # Mode AUTOMATIQUE : verifier qu'il y a au moins 1 en stock
            if stock_disponible < 1:
                QMessageBox.critical(self, "Stock", "Stock insuffisant!")
                return
            # Ajout direct quantité 1
            self._ajouter_au_panier(produit, 1)
            self._flash_ligne_ajoutee(produit['id'])
        else:
            # Mode MANUEL : demander la quantité
            qte, ok = DialogueQuantite.saisir(
                self,
                f"Quantite - {produit['nom']}",
                f"Stock disponible: {produit['stock_actuel']}",
                valeur=1, minimum=1, maximum=produit['stock_actuel']
            )

            if ok and qte > 0:
                self._ajouter_au_panier(produit, qte)

    def _ouvrir_scanner_camera(self):
        """Ouvrir le scanner par webcam."""
        try:
            from ui.components.scanner_camera import SCANNER_DISPONIBLE, ScannerCameraDialog
        except ImportError:
            QMessageBox.information(
                self, "Info",
                "Scanner camera non disponible.\n"
                "Installez: pip install opencv-python pyzbar"
            )
            return

        if not SCANNER_DISPONIBLE:
            QMessageBox.information(
                self, "Info",
                "Scanner camera non disponible.\n"
                "Installez: pip install opencv-python pyzbar"
            )
            return

        def on_code_scanne(code):
            self._entry_scan.setText(code)
            self._scanner_produit()

        dlg = ScannerCameraDialog(on_code_scanne, parent=self)
        dlg.exec()

    def _check_camera_auto(self):
        """Vérifier si la caméra doit être affichée automatiquement"""
        from database import db
        camera_auto = db.get_parametre('camera_auto_start', '0') == '1'
        if camera_auto:
            self._camera_widget.show()
            self.btn_toggle_camera.setChecked(True)
            self.btn_toggle_camera.setText("📷 Masquer caméra")

    def _toggle_camera_widget(self):
        """Afficher/masquer le widget camera"""
        if self.btn_toggle_camera.isChecked():
            # Afficher camera
            self._camera_widget.show()
            self.btn_toggle_camera.setText("📷 Masquer caméra")
            # Démarrer si pas déjà actif
            if not self._camera_widget.actif:
                self._camera_widget._demarrer_camera()
        else:
            # Arreter camera si active
            self._camera_widget._arreter_camera()
            self._camera_widget.hide()
            self.btn_toggle_camera.setText("📷 Afficher caméra")

    def _play_scan_sound(self):
        """Jouer le son de scan si actif"""
        try:
            from ui.utils.sound import SoundManager
            SoundManager.play_scan_sound()
        except Exception:
            # Silencieux si erreur
            pass

    # === PANIER ===

    @staticmethod
    def _prix_effectif(item: dict) -> float:
        """Prix unitaire selon quantité : prix_gros si seuil atteint, sinon prix_vente."""
        pg = item.get('prix_gros') or 0
        sg = item.get('seuil_gros') or 0
        if pg > 0 and sg > 0 and item['quantite'] >= sg:
            return pg
        return item['prix_vente']

    def _ajouter_au_panier(self, produit_tuple, quantite: int):
        """Ajouter un produit au panier memoire."""
        produit_id = produit_tuple['id']
        nom = produit_tuple['nom']
        prix_vente = produit_tuple['prix_vente']
        try:
            prix_gros = float(produit_tuple['prix_gros'] or 0)
            seuil_gros = int(produit_tuple['seuil_gros'] or 0)
        except Exception:
            prix_gros = 0
            seuil_gros = 0
        try:
            unite = produit_tuple['unite_mesure'] or 'pièce'
        except Exception:
            unite = 'pièce'

        # Fusionner si deja present
        for item in self.panier:
            if item['produit_id'] == produit_id:
                item['quantite'] += quantite
                item['sous_total'] = self._prix_effectif(item) * item['quantite']
                self._actualiser_panier()
                self._play_scan_sound()
                return

        item = {
            'produit_id': produit_id,
            'nom': nom,
            'prix_vente': prix_vente,
            'prix_gros': prix_gros,
            'seuil_gros': seuil_gros,
            'unite_mesure': unite,
            'quantite': quantite,
            'sous_total': 0.0,
        }
        item['sous_total'] = self._prix_effectif(item) * quantite
        self.panier.append(item)
        self._actualiser_panier()
        self._play_scan_sound()

    def _actualiser_panier(self):
        """Reconstruire les widgets du panier."""
        # Vider les anciens widgets (sauf le stretch)
        while self._panier_items_layout.count() > 1:
            item = self._panier_items_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self.panier:
            self._scroll_panier.setVisible(False)
            self._label_vide.setVisible(True)
            self._label_nb_articles.setText("0")
            self._label_total.setText("0")
            return

        self._scroll_panier.setVisible(True)
        self._label_vide.setVisible(False)

        total_articles = 0
        total_prix = 0

        for idx, item in enumerate(self.panier):
            total_articles += item['quantite']
            total_prix += item['sous_total']
            widget = self._creer_widget_article(idx, item)
            self._panier_items_layout.insertWidget(idx, widget)

        self._label_nb_articles.setText(str(total_articles))
        from modules.fiscalite import get_devise
        devise = get_devise()

        self._label_soustotal.setText(f"{total_prix:,.0f} {devise}")

        # Calculer remise
        if self._remise_pct:
            self._remise_montant = round(total_prix * self._remise_valeur / 100, 0)
        else:
            self._remise_montant = min(self._remise_valeur, total_prix)

        if self._remise_montant > 0:
            self._label_remise_montant.setText(f"- {self._remise_montant:,.0f} {devise}")
        else:
            self._label_remise_montant.setText("")

        total_net = total_prix - self._remise_montant
        self._label_total.setText(f"{total_net:,.0f} {devise}")

    def _creer_widget_article(self, idx: int, item: dict) -> QWidget:
        """Créer un widget de ligne de panier avec contrôles +/−/×."""
        row = QFrame()
        row.setStyleSheet(
            f"QFrame {{ background-color: {Theme.c('light')}; "
            f"border-radius: 6px; border: 1px solid {Theme.c('card_border')}; }}"
        )
        layout = QHBoxLayout(row)
        layout.setContentsMargins(10, 6, 8, 6)
        layout.setSpacing(8)

        # Nom + prix unitaire
        prix_eff = self._prix_effectif(item)
        prix_gros_actif = (
            item.get('prix_gros', 0) > 0
            and item.get('seuil_gros', 0) > 0
            and item['quantite'] >= item.get('seuil_gros', 0)
        )

        info = QVBoxLayout()
        nom_txt = item['nom']
        lbl_nom = QLabel(nom_txt)
        lbl_nom.setFont(QFont("Segoe UI", 10, QFont.Bold))
        lbl_nom.setStyleSheet("border: none; background: transparent;")
        info.addWidget(lbl_nom)

        unite = item.get('unite_mesure', 'pièce') or 'pièce'
        if prix_gros_actif:
            lbl_prix = QLabel(
                f"{prix_eff:,.0f} F / {unite}  "
                f"<span style='color:#10B981; font-weight:bold;'>[Prix gros]</span>"
            )
            lbl_prix.setTextFormat(Qt.RichText)
        else:
            lbl_prix = QLabel(f"{prix_eff:,.0f} F / {unite}")
        lbl_prix.setFont(QFont("Segoe UI", 8))
        lbl_prix.setStyleSheet(f"color: {Theme.c('gray')}; border: none; background: transparent;")
        info.addWidget(lbl_prix)
        layout.addLayout(info, 1)

        # Bouton −
        btn_moins = QPushButton("−  Moins")
        btn_moins.setFixedSize(72, 30)
        btn_moins.setToolTip("Diminuer la quantité")
        btn_moins.setStyleSheet(
            f"background-color: {Theme.c('warning')}; color: white; "
            f"border: none; border-radius: 4px; font-size: 11px; font-weight: bold;"
        )
        btn_moins.setCursor(Qt.PointingHandCursor)
        btn_moins.setAutoDefault(False)
        btn_moins.clicked.connect(lambda _, i=idx: self._diminuer_quantite(i))
        layout.addWidget(btn_moins)

        # Quantité
        lbl_qte = QLabel(str(item['quantite']))
        lbl_qte.setFont(QFont("Segoe UI", 13, QFont.Bold))
        lbl_qte.setFixedWidth(32)
        lbl_qte.setAlignment(Qt.AlignCenter)
        lbl_qte.setStyleSheet("border: none; background: transparent;")
        layout.addWidget(lbl_qte)

        # Bouton +
        btn_plus = QPushButton("+ Plus")
        btn_plus.setFixedSize(62, 30)
        btn_plus.setToolTip("Augmenter la quantité")
        btn_plus.setStyleSheet(
            f"background-color: {Theme.c('success')}; color: white; "
            f"border: none; border-radius: 4px; font-size: 11px; font-weight: bold;"
        )
        btn_plus.setCursor(Qt.PointingHandCursor)
        btn_plus.setAutoDefault(False)
        btn_plus.clicked.connect(lambda _, i=idx: self._augmenter_quantite(i))
        layout.addWidget(btn_plus)

        # Sous-total
        lbl_total = QLabel(f"{item['sous_total']:,.0f} F")
        lbl_total.setFont(QFont("Segoe UI", 10, QFont.Bold))
        lbl_total.setFixedWidth(80)
        lbl_total.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lbl_total.setStyleSheet(f"color: {Theme.c('success')}; border: none; background: transparent;")
        layout.addWidget(lbl_total)

        # Bouton supprimer
        btn_retirer = QPushButton("Retirer")
        btn_retirer.setFixedSize(60, 28)
        btn_retirer.setToolTip("Retirer cet article du panier")
        btn_retirer.setStyleSheet(
            f"background-color: {Theme.c('danger')}; color: white; "
            f"border: none; border-radius: 4px; font-size: 10px; font-weight: bold;"
        )
        btn_retirer.setCursor(Qt.PointingHandCursor)
        btn_retirer.setAutoDefault(False)
        btn_retirer.clicked.connect(lambda _, i=idx: self._retirer_ligne(i))
        layout.addWidget(btn_retirer)

        return row

    def _augmenter_quantite(self, idx: int):
        if idx >= len(self.panier):
            return
        item = self.panier[idx]
        from modules.produits import Produit
        p = Produit.obtenir_par_id(item['produit_id'])
        stock_max = p['stock_actuel'] if p else 9999
        if item['quantite'] >= stock_max:
            QMessageBox.warning(self, "Stock", f"Stock max atteint ({stock_max})")
            return
        item['quantite'] += 1
        item['sous_total'] = self._prix_effectif(item) * item['quantite']
        self._actualiser_panier()

    def _diminuer_quantite(self, idx: int):
        if idx >= len(self.panier):
            return
        item = self.panier[idx]
        if item['quantite'] <= 1:
            self._retirer_ligne(idx)
        else:
            item['quantite'] -= 1
            item['sous_total'] = self._prix_effectif(item) * item['quantite']
            self._actualiser_panier()

    def _flash_ligne_ajoutee(self, produit_id):
        """Scroll vers l'article ajouté (feedback visuel mode AUTO)"""
        pass

    def _toggle_mode_scan(self):
        """Basculer entre mode AUTO et MANUEL (raccourci F9)"""
        from database import db
        actuel = db.get_parametre('mode_scan_auto', '1')
        nouveau = '0' if actuel == '1' else '1'
        db.set_parametre('mode_scan_auto', nouveau)

        mode_txt = "AUTOMATIQUE (supermarché)" if nouveau == '1' else "MANUEL (avec quantité)"
        QMessageBox.information(
            self, "Mode scan",
            f"✓ Mode scan basculé :\n\n{mode_txt}\n\nAppuyez F9 pour changer à tout moment."
        )

    def _on_remise_changed(self, texte: str):
        try:
            self._remise_valeur = float(texte.replace(',', '.')) if texte.strip() else 0.0
        except ValueError:
            self._remise_valeur = 0.0
        self._actualiser_panier()

    def _toggle_remise_mode(self):
        self._remise_pct = not self._remise_pct
        self._btn_remise_mode.setText("%" if self._remise_pct else "F")
        self._actualiser_panier()

    def _retirer_ligne(self, row: int):
        """Retirer un article du panier."""
        if row < 0 or row >= len(self.panier):
            return
        self.panier.pop(row)
        self._actualiser_panier()

    def _vider_panier(self):
        """Vider tout le panier."""
        if not self.panier:
            return
        if confirmer(self, "Confirmation", "Vider tout le panier?"):
            self.panier.clear()
            self._actualiser_panier()

    # === CLIENT ===

    def _rechercher_client(self, terme: str):
        """Rechercher des clients pendant la frappe."""
        if self.client_id:
            self.client_id = None
            self.client_selectionne = None
            self._label_fidelite.setText("")

        terme = terme.strip()
        if len(terme) < 2:
            self._list_clients.setVisible(False)
            return

        from modules.clients import Client
        resultats = Client.rechercher_filtre(terme, limit=5, offset=0)

        self._list_clients.clear()
        if resultats:
            for c in resultats:
                tel = f" - {c['telephone']}" if c['telephone'] else ""
                item = QListWidgetItem(f"{c['id']}: {c['nom']}{tel}")
                item.setData(Qt.UserRole, c['id'])  # stocker l'ID
                self._list_clients.addItem(item)
            self._list_clients.setVisible(True)
        else:
            self._list_clients.setVisible(False)

    def _selectionner_client(self, item: QListWidgetItem):
        """Selectionner un client dans la liste."""
        client_id = item.data(Qt.UserRole)
        if not client_id:
            return

        from modules.clients import Client
        client = Client.obtenir_par_id(client_id)
        if client:
            self.client_id = client_id
            self.client_selectionne = client
            self._entry_client.blockSignals(True)
            self._entry_client.setText(client['nom'])
            self._entry_client.blockSignals(False)
            self._list_clients.setVisible(False)
            self._label_fidelite.setText(f"Points fidelite: {client['points_fidelite']}")

    def _effacer_client(self):
        """Effacer la selection client."""
        self.client_id = None
        self.client_selectionne = None
        self._entry_client.blockSignals(True)
        self._entry_client.clear()
        self._entry_client.blockSignals(False)
        self._list_clients.setVisible(False)
        self._label_fidelite.setText("")

    # === VALIDATION ===

    def _verifier_session(self):
        """Vérifie si une session de caisse est ouverte (Pro only). Affiche bandeau sinon."""
        try:
            from modules.features import peut
            if not peut('session_caisse'):
                return  # Standard/Démo : pas de session requise
            from modules.sessions import session_actuelle
            session = session_actuelle()
            if session:
                self._session_id = session['id']
                return
            # Pas de session → bandeau rouge + bloquer paiement
            bandeau = QFrame()
            bandeau.setStyleSheet("background-color: #EF4444; padding: 6px;")
            bl = QHBoxLayout(bandeau)
            bl.setContentsMargins(20, 0, 20, 0)
            lbl = QLabel("⚠️  Caisse non ouverte — Ouvrez la caisse avant de vendre.")
            lbl.setStyleSheet("color: white; font-weight: bold; font-size: 11pt;")
            bl.addWidget(lbl)
            btn_ouvrir = QPushButton("Ouvrir la caisse")
            btn_ouvrir.setStyleSheet(
                "background: white; color: #EF4444; font-weight: bold; "
                "border: none; border-radius: 4px; padding: 4px 12px;"
            )
            btn_ouvrir.clicked.connect(self._ouvrir_session_dialog)
            bl.addWidget(btn_ouvrir)
            if self.layout():
                self.layout().insertWidget(0, bandeau)
            self._bandeau_session = bandeau
        except Exception:
            pass

    def _ouvrir_session_dialog(self):
        from ui.dialogs.ouverture_caisse import OuvertureCaisseDialog
        dlg = OuvertureCaisseDialog(self.utilisateur or {}, self)
        def on_ouverte(session_id):
            self._session_id = session_id
            if hasattr(self, '_bandeau_session'):
                self._bandeau_session.hide()
        dlg.session_ouverte.connect(on_ouverte)
        dlg.exec()

    def _valider_vente(self):
        """Ouvrir la fenetre de paiement."""
        if not self.panier:
            QMessageBox.warning(self, "Attention", "Le panier est vide!")
            return

        # Vérification session caisse (Pro)
        try:
            from modules.features import peut
            if peut('session_caisse'):
                from modules.sessions import session_actuelle
                if not session_actuelle():
                    QMessageBox.warning(
                        self, "Caisse non ouverte",
                        "Vous devez ouvrir la caisse avant de vendre."
                    )
                    return
        except Exception:
            pass

        # Vérification démo et expiration
        from modules.features import ventes_autorisees, est_demo, demo_peut_vendre, statut_expiration
        if not ventes_autorisees():
            QMessageBox.critical(
                self, "Licence expirée",
                "Votre licence a expiré.\n"
                "Contactez votre revendeur pour renouveler."
            )
            return
        if est_demo():
            ok, raison = demo_peut_vendre()
            if not ok:
                QMessageBox.critical(
                    self, "Limite démonstration",
                    f"{raison}\n\nActivez une licence pour continuer."
                )
                return

        total = sum(item['sous_total'] for item in self.panier) - self._remise_montant

        from ui.windows.paiement import PaiementWindow
        dlg = PaiementWindow(total, parent=self)
        dlg.paiement_confirme.connect(self._finaliser_vente)
        dlg.exec()

    def _finaliser_vente(self, paiements: list):
        """Transaction DB atomique apres paiement confirme."""
        client_nom = self._entry_client.text().strip()
        client_id = self.client_id

        try:
            from modules.ventes import Vente
            from modules.paiements import Paiement
            from database import db

            # Generer le numero de vente
            numero_vente = Vente.generer_numero_vente()

            # Total
            sous_total = sum(item['sous_total'] for item in self.panier)
            remise = self._remise_montant
            total = sous_total - remise

            # INSERT vente
            utilisateur_id = self.utilisateur['id'] if self.utilisateur else None
            # Récupérer session active si feature Pro
            session_id = getattr(self, '_session_id', None)
            try:
                from modules.features import peut
                from modules.sessions import session_actuelle
                if peut('session_caisse') and not session_id:
                    s = session_actuelle()
                    if s:
                        session_id = s['id']
            except Exception:
                pass

            vente_id = db.execute_query(
                """INSERT INTO ventes
                   (numero_vente, date_vente, total, remise, client, client_id, utilisateur_id, id_session)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (numero_vente,
                 datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                 total,
                 remise,
                 client_nom or None,
                 client_id,
                 utilisateur_id,
                 session_id)
            )

            # INSERT details + MAJ stock (avec re-verification)
            for item in self.panier:
                # RE-VÉRIFIER le stock AVANT l'insertion (protection race condition)
                stock_actuel = db.fetch_one(
                    "SELECT stock_actuel FROM produits WHERE id = ?",
                    (item['produit_id'],)
                )

                if not stock_actuel or stock_actuel['stock_actuel'] < item['quantite']:
                    # ROLLBACK + alerte utilisateur
                    db.conn.rollback()
                    QMessageBox.critical(
                        self, "Stock insuffisant",
                        f"Le produit '{item['nom']}' n'a plus assez de stock!\n"
                        f"Stock actuel: {stock_actuel['stock_actuel'] if stock_actuel else 0}\n"
                        f"Quantité demandée: {item['quantite']}\n\n"
                        f"La vente a été annulée."
                    )
                    return False

                # INSERT details
                prix_eff = self._prix_effectif(item)
                is_pg = 1 if prix_eff != item['prix_vente'] else 0
                db.execute_query(
                    """INSERT INTO details_ventes
                       (vente_id, produit_id, quantite, prix_unitaire, sous_total, is_prix_gros)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (vente_id, item['produit_id'], item['quantite'],
                     prix_eff, item['sous_total'], is_pg)
                )

                # UPDATE stock ATOMIQUE avec WHERE clause
                rows_affected = db.execute_query(
                    """UPDATE produits
                       SET stock_actuel = stock_actuel - ?
                       WHERE id = ? AND stock_actuel >= ?""",
                    (item['quantite'], item['produit_id'], item['quantite'])
                )

                # Vérifier que l'UPDATE a bien modifié une ligne
                if rows_affected == 0:
                    db.conn.rollback()
                    QMessageBox.critical(
                        self, "Erreur Stock",
                        f"Impossible de mettre à jour le stock de '{item['nom']}'\n"
                        f"La vente a été annulée."
                    )
                    return False

            # Enregistrer les paiements
            for p in paiements:
                Paiement.enregistrer_paiement(
                    vente_id, p['mode'], p['montant'],
                    reference=p.get('reference'),
                    montant_recu=p.get('montant_recu'),
                    monnaie_rendue=p.get('monnaie_rendue')
                )

            # Points fidelite
            if client_id:
                from modules.clients import Client as ClientModule
                ClientModule.ajouter_points(client_id, total)

            # Incrémenter le compteur démo si applicable
            try:
                from modules.features import demo_incrementer_ventes
                demo_incrementer_ventes()
            except Exception:
                pass

            # Generer le recu PDF
            chemin_recu = ""
            try:
                from modules.recus import generer_recu_pdf
                chemin_recu = generer_recu_pdf(vente_id) or ""
            except Exception as e_pdf:
                import traceback
                traceback.print_exc()
                QMessageBox.warning(
                    self, "PDF",
                    f"La vente est enregistrée mais le reçu PDF n'a pas pu être généré :\n{e_pdf}"
                )

            # Preparer les infos pour la confirmation
            vente_info = {
                'numero': numero_vente,
                'date': datetime.now().strftime("%d/%m/%Y a %H:%M"),
                'total': total,
                'remise': remise,
                'client': client_nom,
                'items': self.panier.copy(),
                'vente_id': vente_id,
                'paiements': paiements,
            }

            # Afficher la confirmation
            from ui.windows.confirmation_vente import ConfirmationVenteWindow
            dlg_confirm = ConfirmationVenteWindow(
                vente_info, chemin_recu or "", parent=self
            )
            dlg_confirm.nouvelle_vente.connect(self._reset_pour_nouvelle_vente)

            self.vente_terminee.emit()

            result = dlg_confirm.exec()

            # Si pas "nouvelle vente", fermer
            if result != QDialog.Accepted:
                self.accept()

        except Exception as e:
            QMessageBox.critical(
                self, "Erreur",
                f"Impossible de valider la vente:\n{e}"
            )
            import traceback
            traceback.print_exc()

    def _reset_pour_nouvelle_vente(self):
        """Reinitialiser le panier pour une nouvelle vente."""
        self.panier.clear()
        self._remise_valeur = 0.0
        self._remise_montant = 0.0
        self._entry_remise.blockSignals(True)
        self._entry_remise.clear()
        self._entry_remise.blockSignals(False)
        self._effacer_client()
        self._actualiser_panier()
        QTimer.singleShot(0, self._entry_scan.setFocus)

    def _annuler_vente(self):
        """Annuler et fermer."""
        if not self.panier:
            self.reject()
            return
        if confirmer(self, "Confirmation", "Annuler cette vente?"):
            self.reject()

    def closeEvent(self, event):
        """Confirmer si panier non vide."""
        if self.panier:
            if not confirmer(
                self, "Confirmation",
                "Des articles sont dans le panier.\nVoulez-vous vraiment fermer?"
            ):
                event.ignore()
                return

        super().closeEvent(event)
