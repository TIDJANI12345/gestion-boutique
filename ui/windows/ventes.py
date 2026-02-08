"""
Fenetre de ventes - PySide6
Panier en memoire, paiement, transaction DB atomique.
"""
from datetime import datetime

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QMessageBox, QWidget, QListWidget,
    QListWidgetItem
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QShortcut, QKeySequence

from ui.theme import Theme
from ui.components.table import BoutiqueTableView, BoutiqueTableModel
from ui.components.dialogs import DialogueQuantite, confirmer
from ui.components.camera_widget import CameraWidget


class VentesWindow(QDialog):
    """Fenetre de vente - panier en memoire, validation atomique."""

    vente_terminee = Signal()

    def __init__(self, parent=None, utilisateur=None):
        super().__init__(parent)
        print("DEBUG: Initialisation de VentesWindow commence.")
        try:
            self.setWindowTitle("Nouvelle Vente")
            self.setMinimumSize(1200, 700)
            self.setModal(True)

            # Panier en memoire
            self.panier: list[dict] = []
            self.client_id = None
            self.client_selectionne = None
            self.utilisateur = utilisateur  # Dict utilisateur connecté
            self.scanner_mobile_server = None  # Serveur scanner mobile
            self.scanner_mobile_http = None  # Serveur HTTP pour page mobile
            print("DEBUG: Variables initialisées.")

            self._setup_ui()
            print("DEBUG: _setup_ui() terminé.")

            self._setup_raccourcis()
            print("DEBUG: _setup_raccourcis() terminé.")

            self._actualiser_panier()
            print("DEBUG: _actualiser_panier() terminé.")

            self._check_camera_auto()
            print("DEBUG: _check_camera_auto() terminé.")

            self._check_scanner_mobile_auto()
            print("DEBUG: _check_scanner_mobile_auto() terminé.")

            # Focus scanner au demarrage
            QTimer.singleShot(0, self._entry_scan.setFocus)
            print("DEBUG: Initialisation de VentesWindow terminée avec succès.")
        except Exception as e:
            print(f"FATAL: Erreur dans VentesWindow.__init__: {e}")
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
        self._entry_scan.setPlaceholderText("Code-barres...")
        self._entry_scan.returnPressed.connect(self._scanner_produit)
        scan_row.addWidget(self._entry_scan)

        btn_camera = QPushButton("Camera")
        btn_camera.setStyleSheet(
            f"background-color: {Theme.c('info')}; color: white; "
            f"border: none; border-radius: 6px; padding: 10px 16px;"
        )
        btn_camera.setCursor(Qt.PointingHandCursor)
        btn_camera.clicked.connect(self._ouvrir_scanner_camera)
        scan_row.addWidget(btn_camera)

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

        # Separateur
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color: {Theme.c('separator')};")
        panier_layout.addWidget(sep)

        # Tableau
        colonnes = ['Produit', 'Prix Unit.', 'Qte', 'Sous-total']
        self._table_model = BoutiqueTableModel(colonnes)
        self._table_view = BoutiqueTableView()
        self._table_view.setModel(self._table_model)
        self._table_view.ligne_double_clic.connect(self._retirer_ligne)
        panier_layout.addWidget(self._table_view)

        # Label panier vide
        self._label_vide = QLabel(
            "Le panier est vide\n\nScannez un produit pour commencer"
        )
        self._label_vide.setFont(QFont("Segoe UI", 11))
        self._label_vide.setStyleSheet(f"color: {Theme.c('gray')};")
        self._label_vide.setAlignment(Qt.AlignCenter)
        panier_layout.addWidget(self._label_vide)

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

        # Total
        row_total = QHBoxLayout()
        lbl_total_label = QLabel("TOTAL:")
        lbl_total_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        row_total.addWidget(lbl_total_label)
        row_total.addStretch()

        self._label_total = QLabel("0 FCFA")
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

    def _check_scanner_mobile_auto(self):
        """Démarrer le serveur scanner mobile si configuré"""
        try:
            from database import db
            from modules.scanner_mobile_server import ScannerMobileServer, est_disponible
            from modules.scanner_mobile_http import ScannerMobileHTTP

            scanner_mobile_auto = db.get_parametre('scanner_mobile_auto', '0') == '1'

            if scanner_mobile_auto and est_disponible():
                try:
                    # Démarrer serveur WebSocket
                    self.scanner_mobile_server = ScannerMobileServer(host='0.0.0.0', port=8765)
                    self.scanner_mobile_server.code_recu.connect(self._traiter_code_camera)
                    self.scanner_mobile_server.start()

                    # Démarrer serveur HTTP
                    self.scanner_mobile_http = ScannerMobileHTTP(port=8080)
                    self.scanner_mobile_http.start()

                    print("DEBUG: Serveur scanner mobile démarré")
                except Exception as e:
                    print(f"ERREUR: Impossible de démarrer le scanner mobile : {e}")
        except ImportError:
            # Module scanner mobile non disponible (websockets manquant)
            print("DEBUG: Scanner mobile non disponible (websockets manquant)")
        except Exception as e:
            print(f"ERREUR: _check_scanner_mobile_auto : {e}")

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

    def _ajouter_au_panier(self, produit_tuple, quantite: int):
        """Ajouter un produit au panier memoire."""
        produit_id = produit_tuple['id']
        nom = produit_tuple['nom']
        prix_vente = produit_tuple['prix_vente']

        # Fusionner si deja present
        for item in self.panier:
            if item['produit_id'] == produit_id:
                item['quantite'] += quantite
                item['sous_total'] = item['prix_vente'] * item['quantite']
                self._actualiser_panier()
                # Son de confirmation
                self._play_scan_sound()
                return

        self.panier.append({
            'produit_id': produit_id,
            'nom': nom,
            'prix_vente': prix_vente,
            'quantite': quantite,
            'sous_total': prix_vente * quantite,
        })
        self._actualiser_panier()
        # Son de confirmation
        self._play_scan_sound()

    def _actualiser_panier(self):
        """Rafraichir le tableau et les labels."""
        if not self.panier:
            self._table_view.setVisible(False)
            self._label_vide.setVisible(True)
            self._label_nb_articles.setText("0")
            self._label_total.setText("0 FCFA")
            return

        self._table_view.setVisible(True)
        self._label_vide.setVisible(False)

        total_articles = 0
        total_prix = 0
        lignes = []

        for item in self.panier:
            total_articles += item['quantite']
            total_prix += item['sous_total']
            lignes.append([
                item['nom'],
                f"{item['prix_vente']:,.0f} F",
                item['quantite'],
                f"{item['sous_total']:,.0f} F",
            ])

        self._table_model.charger_donnees(lignes)
        self._table_view.ajuster_colonnes()
        self._label_nb_articles.setText(str(total_articles))
        self._label_total.setText(f"{total_prix:,.0f} FCFA")

    def _flash_ligne_ajoutee(self, produit_id):
        """Flash vert sur la ligne ajoutée (feedback visuel mode AUTO)"""
        # Trouver la ligne du produit dans le panier
        for i, item in enumerate(self.panier):
            if item['produit_id'] == produit_id:
                # Sélectionner la ligne
                self._table_view.selectRow(i)
                # Retirer la sélection après 500ms
                QTimer.singleShot(500, self._table_view.clearSelection)
                break

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

    def _retirer_ligne(self, row: int):
        """Retirer un article du panier (double-clic)."""
        if row < 0 or row >= len(self.panier):
            return

        nom = self.panier[row]['nom']
        if confirmer(self, "Confirmation", f"Retirer '{nom}' du panier?"):
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

    def _valider_vente(self):
        """Ouvrir la fenetre de paiement."""
        if not self.panier:
            QMessageBox.warning(self, "Attention", "Le panier est vide!")
            return

        total = sum(item['sous_total'] for item in self.panier)

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
            total = sum(item['sous_total'] for item in self.panier)

            # INSERT vente
            utilisateur_id = self.utilisateur['id'] if self.utilisateur else None
            vente_id = db.execute_query(
                """INSERT INTO ventes (numero_vente, date_vente, total, client, client_id, utilisateur_id)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (numero_vente,
                 datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                 total,
                 client_nom or None,
                 client_id,
                 utilisateur_id)
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
                db.execute_query(
                    """INSERT INTO details_ventes
                       (vente_id, produit_id, quantite, prix_unitaire, sous_total)
                       VALUES (?, ?, ?, ?, ?)""",
                    (vente_id, item['produit_id'], item['quantite'],
                     item['prix_vente'], item['sous_total'])
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

            # Generer le recu PDF
            from modules.recus import generer_recu_pdf
            chemin_recu = generer_recu_pdf(vente_id)

            # Preparer les infos pour la confirmation
            vente_info = {
                'numero': numero_vente,
                'date': datetime.now().strftime("%d/%m/%Y a %H:%M"),
                'total': total,
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

        # Arrêter les serveurs scanner mobile
        try:
            if self.scanner_mobile_server:
                self.scanner_mobile_server.arreter()
                self.scanner_mobile_server = None

            if self.scanner_mobile_http:
                self.scanner_mobile_http.arreter()
                self.scanner_mobile_http = None
        except Exception as e:
            print(f"ERREUR arrêt scanner mobile : {e}")

        super().closeEvent(event)
