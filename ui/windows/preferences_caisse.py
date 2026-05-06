"""
Fenêtre Paramètres Caisse - Configuration point de vente
"""
import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QPushButton, QRadioButton, QButtonGroup, QCheckBox, QScrollArea, QLineEdit,
    QComboBox, QFileDialog, QColorDialog, QSpinBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

from ui.theme import Theme
from ui.components.dialogs import information, erreur
from database import db


class PreferencesCaisseWindow(QDialog):

    def _chk(self, texte: str, bold: bool = True) -> QCheckBox:
        """Crée une QCheckBox thémée qui fonctionne en clair ET en sombre."""
        cb = QCheckBox(texte)
        weight = "bold" if bold else "normal"
        cb.setStyleSheet(f"""
            QCheckBox {{
                color: {Theme.c('text')};
                font-size: 11pt;
                font-weight: {weight};
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 18px; height: 18px;
                border-radius: 4px;
                border: 2px solid {Theme.c('input_border')};
                background: {Theme.c('input_bg')};
            }}
            QCheckBox::indicator:hover {{
                border-color: {Theme.c('primary')};
            }}
            QCheckBox::indicator:checked {{
                background: {Theme.c('primary')};
                border-color: {Theme.c('primary')};
            }}
            QCheckBox::indicator:checked:disabled {{
                background: {Theme.c('gray')};
                border-color: {Theme.c('gray')};
            }}
            QCheckBox:disabled {{ color: {Theme.c('gray')}; }}
        """)
        cb.stateChanged.connect(self._marquer_modifie)
        return cb

    def _radio(self, texte: str, bold: bool = True) -> QRadioButton:
        """QRadioButton thémé."""
        rb = QRadioButton(texte)
        weight = "bold" if bold else "normal"
        rb.setStyleSheet(f"""
            QRadioButton {{
                color: {Theme.c('text')};
                font-size: 11pt;
                font-weight: {weight};
                spacing: 8px;
            }}
            QRadioButton::indicator {{
                width: 18px; height: 18px;
                border-radius: 9px;
                border: 2px solid {Theme.c('input_border')};
                background: {Theme.c('input_bg')};
            }}
            QRadioButton::indicator:hover {{
                border-color: {Theme.c('primary')};
            }}
            QRadioButton::indicator:checked {{
                background: {Theme.c('primary')};
                border-color: {Theme.c('primary')};
            }}
        """)
        rb.toggled.connect(self._marquer_modifie)
        return rb

    def _section(self, titre: str, desc: str = '') -> QLabel:
        """Titre de section."""
        lbl = QLabel(titre)
        lbl.setStyleSheet(f"font-size: 13pt; font-weight: bold; color: {Theme.c('text')};")
        return lbl

    def _marquer_modifie(self, *_):
        self._modifie = True
        if hasattr(self, '_btn_enregistrer'):
            self._btn_enregistrer.setStyleSheet(self._style_save_actif())

    def _style_save_actif(self):
        return f"""
            QPushButton {{
                background: {Theme.c('success')}; color: white;
                padding: 12px 30px; font-size: 11pt; font-weight: bold;
                border-radius: 6px; border: none;
            }}
            QPushButton:hover {{ background: {Theme.c('success_hover')}; }}
        """

    def _style_save_neutre(self):
        return f"""
            QPushButton {{
                background: {Theme.c('card_border')}; color: {Theme.c('text_secondary')};
                padding: 12px 30px; font-size: 11pt; font-weight: bold;
                border-radius: 6px; border: none;
            }}
        """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Paramètres Caisse")
        self.setMinimumSize(700, 600)
        self._modifie = False

        self._setup_ui()
        self._charger_parametres()

        # Connecter les champs texte au marqueur de modification
        for w in self.findChildren(QLineEdit):
            w.textChanged.connect(self._marquer_modifie)
        for w in self.findChildren(QComboBox):
            w.currentIndexChanged.connect(self._marquer_modifie)

        # Centrer la fenêtre sur le parent
        if self.parent():
            self.adjustSize()
            parent_rect = self.parent().frameGeometry()
            center = parent_rect.center()
            dlg_rect = self.frameGeometry()
            dlg_rect.moveCenter(center)
            self.move(dlg_rect.topLeft())

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QFrame()
        header.setStyleSheet(f"background-color: {Theme.c('primary')};")
        header.setFixedHeight(70)

        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(30, 0, 30, 0)

        title = QLabel("⚙️ Paramètres Caisse")
        title.setStyleSheet("color: white; font-size: 18pt; font-weight: bold;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        layout.addWidget(header)

        # Content
        content = QFrame()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(20)

        # === COMPORTEMENT AU SCAN ===
        mode_label = QLabel("Comportement au scan")
        mode_label.setStyleSheet(f"font-size: 13pt; font-weight: bold; color: {Theme.c('text')};")
        content_layout.addWidget(mode_label)

        desc_label = QLabel("Comportement après la détection d'un code-barres.")
        desc_label.setStyleSheet(f"color: {Theme.c('text_secondary')}; font-size: 10pt;")
        desc_label.setWordWrap(True)
        content_layout.addWidget(desc_label)

        # Radio buttons
        mode_frame = QFrame()
        mode_frame.setStyleSheet(f"background-color: {Theme.c('light')}; border-radius: 8px; padding: 20px;")
        mode_layout = QVBoxLayout(mode_frame)
        mode_layout.setSpacing(15)

        self.radio_group = QButtonGroup(self)

        self.radio_auto = self._radio("🏪 Automatique — ajouter directement avec quantité 1")
        self.radio_group.addButton(self.radio_auto, 1)
        mode_layout.addWidget(self.radio_auto)
        auto_desc = QLabel("Re-scan du même article → quantité s'incrémente. Idéal pour supermarché / flux rapide.")
        auto_desc.setStyleSheet(f"color: {Theme.c('text_secondary')}; font-size: 9pt; margin-left: 26px;")
        mode_layout.addWidget(auto_desc)

        mode_layout.addSpacing(8)

        self.radio_manuel = self._radio("✍️ Manuel — demander la quantité à chaque scan")
        self.radio_group.addButton(self.radio_manuel, 0)
        mode_layout.addWidget(self.radio_manuel)
        manuel_desc = QLabel("Une popup s'ouvre à chaque scan. Plus sûr pour les quantités variables.")
        manuel_desc.setStyleSheet(f"color: {Theme.c('text_secondary')}; font-size: 9pt; margin-left: 26px;")
        mode_layout.addWidget(manuel_desc)

        content_layout.addWidget(mode_frame)

        # Info F9
        info_f9 = QLabel("💡 Astuce : Appuyez sur F9 dans la fenêtre Ventes pour basculer rapidement")
        info_f9.setStyleSheet(f"color: {Theme.c('info')}; font-size: 9pt; font-style: italic;")
        content_layout.addWidget(info_f9)

        content_layout.addSpacing(20)

        # === SON DE SCAN ===
        son_label = QLabel("Son de confirmation")
        son_label.setStyleSheet(f"font-size: 13pt; font-weight: bold; color: {Theme.c('text')};")
        content_layout.addWidget(son_label)

        son_frame = QFrame()
        son_frame.setStyleSheet(f"background-color: {Theme.c('light')}; border-radius: 8px; padding: 16px;")
        son_layout = QVBoxLayout(son_frame)
        son_layout.setSpacing(6)

        self.checkbox_son = self._chk("🔊 Activer le son de scan")
        son_layout.addWidget(self.checkbox_son)
        son_info = QLabel("Un bip court est joué à chaque ajout au panier.")
        son_info.setStyleSheet(f"color: {Theme.c('text_secondary')}; font-size: 9pt; margin-left: 26px;")
        son_layout.addWidget(son_info)

        content_layout.addWidget(son_frame)

        content_layout.addSpacing(20)

        # === CAMÉRA ===
        camera_label = QLabel("Scanner caméra")
        camera_label.setStyleSheet(f"font-size: 14pt; font-weight: bold; color: {Theme.c('dark')};")
        content_layout.addWidget(camera_label)

        camera_desc = QLabel(
            "Activez uniquement si vous n'avez pas de lecteur de codes-barres USB. "
            "La plupart des boutiques n'ont pas besoin de cette option."
        )
        camera_desc.setStyleSheet(f"color: {Theme.c('gray')}; font-size: 10pt;")
        camera_desc.setWordWrap(True)
        content_layout.addWidget(camera_desc)

        camera_frame = QFrame()
        camera_frame.setStyleSheet(f"background-color: {Theme.c('light')}; border-radius: 8px; padding: 20px;")
        camera_layout = QVBoxLayout(camera_frame)
        camera_layout.setSpacing(10)

        # Toggle maître
        self.checkbox_camera_actif = self._chk("📷 Activer le scanner caméra")
        camera_layout.addWidget(self.checkbox_camera_actif)

        camera_main_info = QLabel(
            "Affiche le bouton caméra dans la fenêtre Ventes.\n"
            "Désactivé par défaut — utilisez un lecteur USB pour de meilleures performances."
        )
        camera_main_info.setStyleSheet(f"color: {Theme.c('gray')}; font-size: 9pt; margin-left: 25px;")
        camera_layout.addWidget(camera_main_info)

        camera_layout.addSpacing(8)

        # Sous-options (grises si caméra désactivée)
        self._camera_suboptions = QFrame()
        sub_layout = QVBoxLayout(self._camera_suboptions)
        sub_layout.setContentsMargins(20, 0, 0, 0)
        sub_layout.setSpacing(8)

        self.checkbox_camera_auto = self._chk("Ouvrir la caméra automatiquement à l'ouverture des Ventes", bold=False)
        sub_layout.addWidget(self.checkbox_camera_auto)

        source_label = QLabel("Source caméra :")
        source_label.setStyleSheet("font-size: 10pt; font-weight: bold;")
        sub_layout.addWidget(source_label)

        source_layout = QHBoxLayout()
        self.input_camera_source = QLineEdit()
        self.input_camera_source.setPlaceholderText("0 (webcam PC)  ou  http://IP:PORT/video (téléphone)")
        self.input_camera_source.setStyleSheet(f"""
            QLineEdit {{
                padding: 8px;
                border: 1px solid {Theme.c('gray')};
                border-radius: 4px;
                font-size: 10pt;
            }}
        """)
        source_layout.addWidget(self.input_camera_source)

        test_btn = QPushButton("Tester")
        test_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.c('info')};
                color: white; padding: 8px 15px;
                border-radius: 4px; font-weight: bold;
            }}
            QPushButton:hover {{ background-color: #0284C7; }}
        """)
        test_btn.clicked.connect(self._tester_camera)
        source_layout.addWidget(test_btn)
        sub_layout.addLayout(source_layout)

        source_info = QLabel(
            "0 = webcam intégrée · 1 = 2ème webcam USB\n"
            "Téléphone : installez IP Webcam (Android) et entrez l'URL — ex: http://192.168.1.5:8080/video"
        )
        source_info.setStyleSheet(f"color: {Theme.c('gray')}; font-size: 9pt;")
        sub_layout.addWidget(source_info)

        camera_layout.addWidget(self._camera_suboptions)
        content_layout.addWidget(camera_frame)

        # Lier le toggle maître aux sous-options
        self.checkbox_camera_actif.toggled.connect(self._camera_suboptions.setEnabled)

        content_layout.addSpacing(20)

        # === REMISE PAR DÉFAUT ===
        remise_label = QLabel("Remise par défaut")
        remise_label.setStyleSheet(f"font-size: 13pt; font-weight: bold; color: {Theme.c('text')};")
        content_layout.addWidget(remise_label)
        remise_desc = QLabel("Mode de remise affiché par défaut dans la fenêtre Nouvelle Vente.")
        remise_desc.setStyleSheet(f"color: {Theme.c('text_secondary')}; font-size: 10pt;")
        content_layout.addWidget(remise_desc)

        remise_frame = QFrame()
        remise_frame.setStyleSheet(f"background-color: {Theme.c('light')}; border-radius: 8px; padding: 16px;")
        remise_frame_layout = QVBoxLayout(remise_frame)
        remise_frame_layout.setSpacing(8)

        self.radio_remise_group = QButtonGroup(self)
        self.radio_remise_pct = self._radio("% Pourcentage  (ex: 10%)")
        self.radio_remise_montant = self._radio("FCFA Montant fixe  (ex: 500 FCFA)")
        self.radio_remise_group.addButton(self.radio_remise_pct, 0)
        self.radio_remise_group.addButton(self.radio_remise_montant, 1)
        remise_frame_layout.addWidget(self.radio_remise_pct)
        remise_frame_layout.addWidget(self.radio_remise_montant)
        content_layout.addWidget(remise_frame)

        content_layout.addSpacing(20)

        # === CODE-BARRES PAR DÉFAUT ===
        cb_label = QLabel("Code-barres produit par défaut")
        cb_label.setStyleSheet(f"font-size: 13pt; font-weight: bold; color: {Theme.c('text')};")
        content_layout.addWidget(cb_label)
        cb_desc = QLabel("Mode par défaut lors de l'ajout d'un nouveau produit.")
        cb_desc.setStyleSheet(f"color: {Theme.c('text_secondary')}; font-size: 10pt;")
        content_layout.addWidget(cb_desc)

        cb_frame = QFrame()
        cb_frame.setStyleSheet(f"background-color: {Theme.c('light')}; border-radius: 8px; padding: 16px;")
        cb_frame_layout = QVBoxLayout(cb_frame)
        cb_frame_layout.setSpacing(8)

        self.radio_cb_group = QButtonGroup(self)
        self.radio_cb_auto = self._radio("Automatique — générer un code (produits sans étiquette)")
        self.radio_cb_manuel = self._radio("Manuel — saisir ou scanner le code existant (EAN-13 importé)")
        self.radio_cb_group.addButton(self.radio_cb_auto, 0)
        self.radio_cb_group.addButton(self.radio_cb_manuel, 1)
        cb_frame_layout.addWidget(self.radio_cb_auto)
        cb_frame_layout.addWidget(self.radio_cb_manuel)
        cb_hint = QLabel("💡 En mode Manuel, un lecteur USB scanne directement dans le champ Code.")
        cb_hint.setStyleSheet(f"color: {Theme.c('info')}; font-size: 9pt;")
        cb_frame_layout.addWidget(cb_hint)
        content_layout.addWidget(cb_frame)

        content_layout.addSpacing(20)

        # === VENTES & STOCK ===
        vs_label = QLabel("Ventes & Stock")
        vs_label.setStyleSheet(f"font-size: 13pt; font-weight: bold; color: {Theme.c('text')};")
        content_layout.addWidget(vs_label)
        vs_desc = QLabel("Paramètres par défaut pour les ventes et la gestion des stocks.")
        vs_desc.setStyleSheet(f"color: {Theme.c('text_secondary')}; font-size: 10pt;")
        content_layout.addWidget(vs_desc)

        vs_frame = QFrame()
        vs_frame.setStyleSheet(f"background-color: {Theme.c('light')}; border-radius: 8px; padding: 20px;")
        vs_layout = QVBoxLayout(vs_frame)
        vs_layout.setSpacing(10)

        # TVA par défaut
        tva_row = QHBoxLayout()
        tva_lbl = QLabel("TVA par défaut :")
        tva_lbl.setFixedWidth(160)
        tva_lbl.setStyleSheet("font-size: 10pt;")
        tva_row.addWidget(tva_lbl)
        self._combo_tva = QComboBox()
        for tva_label, tva_val in [("Pas de TVA (0 %)", "0"), ("TVA 10 %", "10"), ("TVA 18 % — Bénin", "18")]:
            self._combo_tva.addItem(tva_label, tva_val)
        tva_row.addWidget(self._combo_tva)
        tva_row.addStretch()
        vs_layout.addLayout(tva_row)

        tva_info = QLabel("Appliquée sur les reçus lorsque la TVA est activée sur la vente.")
        tva_info.setStyleSheet(f"color: {Theme.c('text_secondary')}; font-size: 9pt;")
        vs_layout.addWidget(tva_info)

        vs_layout.addSpacing(8)

        # Seuil alerte stock
        alerte_row = QHBoxLayout()
        alerte_lbl = QLabel("Alerte stock faible :")
        alerte_lbl.setFixedWidth(160)
        alerte_lbl.setStyleSheet("font-size: 10pt;")
        alerte_row.addWidget(alerte_lbl)
        self._spin_alerte_stock = QSpinBox()
        self._spin_alerte_stock.setRange(0, 9999)
        self._spin_alerte_stock.setSuffix(" unités")
        self._spin_alerte_stock.setFixedWidth(130)
        self._spin_alerte_stock.setStyleSheet(f"padding: 4px; border: 1px solid {Theme.c('gray')}; border-radius: 4px;")
        self._spin_alerte_stock.valueChanged.connect(self._marquer_modifie)
        alerte_row.addWidget(self._spin_alerte_stock)
        alerte_row.addStretch()
        vs_layout.addLayout(alerte_row)

        alerte_info = QLabel("Les produits sous ce seuil s'affichent en rouge dans l'inventaire et les rapports.")
        alerte_info.setStyleSheet(f"color: {Theme.c('text_secondary')}; font-size: 9pt;")
        vs_layout.addWidget(alerte_info)

        vs_layout.addSpacing(8)

        # Déconnexion automatique
        session_row = QHBoxLayout()
        session_lbl = QLabel("Déconnexion auto :")
        session_lbl.setFixedWidth(160)
        session_lbl.setStyleSheet("font-size: 10pt;")
        session_row.addWidget(session_lbl)
        self._combo_session = QComboBox()
        for s_label, s_val in [
            ("Jamais", "0"), ("15 minutes", "900"), ("30 minutes", "1800"),
            ("1 heure", "3600"), ("2 heures", "7200"),
        ]:
            self._combo_session.addItem(s_label, s_val)
        session_row.addWidget(self._combo_session)
        session_row.addStretch()
        vs_layout.addLayout(session_row)

        session_info = QLabel("Déconnecte l'utilisateur automatiquement après cette durée d'inactivité. "
                              "Recommandé si plusieurs personnes partagent le poste.")
        session_info.setStyleSheet(f"color: {Theme.c('text_secondary')}; font-size: 9pt;")
        session_info.setWordWrap(True)
        vs_layout.addWidget(session_info)

        content_layout.addWidget(vs_frame)

        content_layout.addSpacing(20)

        # === IMPRESSION THERMIQUE ===
        imp_label = QLabel("Impression thermique")
        imp_label.setStyleSheet(f"font-size: 14pt; font-weight: bold; color: {Theme.c('dark')};")
        content_layout.addWidget(imp_label)

        imp_frame = QFrame()
        imp_frame.setStyleSheet(f"background-color: {Theme.c('light')}; border-radius: 8px; padding: 10px;")
        imp_layout = QVBoxLayout(imp_frame)
        imp_layout.setSpacing(8)

        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("Mode :"))
        self.combo_imp_mode = QComboBox()
        self.combo_imp_mode.addItems(["USB", "Réseau (IP)", "Série (COM)"])
        mode_row.addWidget(self.combo_imp_mode, 1)
        imp_layout.addLayout(mode_row)

        btn_test_imp = QPushButton("Imprimer ticket de test")
        btn_test_imp.setProperty("class", "secondary")
        btn_test_imp.setCursor(Qt.PointingHandCursor)
        btn_test_imp.clicked.connect(self._tester_impression)
        imp_layout.addWidget(btn_test_imp)

        content_layout.addWidget(imp_frame)

        content_layout.addSpacing(20)

        # === INFORMATIONS BOUTIQUE ===
        boutique_label = QLabel("Informations boutique")
        boutique_label.setStyleSheet(f"font-size: 14pt; font-weight: bold; color: {Theme.c('dark')};")
        content_layout.addWidget(boutique_label)

        boutique_desc = QLabel("Ces informations apparaissent sur les reçus PDF et tickets thermiques.")
        boutique_desc.setStyleSheet(f"color: {Theme.c('gray')}; font-size: 10pt;")
        boutique_desc.setWordWrap(True)
        content_layout.addWidget(boutique_desc)

        boutique_frame = QFrame()
        boutique_frame.setStyleSheet(f"background-color: {Theme.c('light')}; border-radius: 8px; padding: 20px;")
        boutique_layout = QVBoxLayout(boutique_frame)
        boutique_layout.setSpacing(10)

        def _champ(label_txt, placeholder):
            row = QHBoxLayout()
            lbl = QLabel(label_txt)
            lbl.setFixedWidth(100)
            lbl.setStyleSheet("font-size: 10pt;")
            row.addWidget(lbl)
            entry = QLineEdit()
            entry.setPlaceholderText(placeholder)
            entry.setStyleSheet(f"padding: 6px; border: 1px solid {Theme.c('gray')}; border-radius: 4px;")
            row.addWidget(entry)
            boutique_layout.addLayout(row)
            return entry

        self.input_nom_boutique     = _champ("Nom :",      "Ma Boutique")
        self.input_adresse_boutique = _champ("Adresse :",  "Cotonou, Bénin")
        self.input_tel_boutique     = _champ("Téléphone :", "+229 XX XX XX XX")
        self.input_email_boutique   = _champ("Email :",    "contact@maboutique.bj")
        self.input_ifu_boutique     = _champ("IFU :",      "Numéro IFU (ex: 1234567890123)")
        self.input_rccm_boutique    = _champ("RCCM :",     "Numéro RCCM (ex: RB/ABC/24 B 12345)")

        # Réseaux sociaux
        boutique_layout.addSpacing(6)
        rs_title = QLabel("Réseaux sociaux (optionnel) :")
        rs_title.setStyleSheet("font-size: 10pt; font-weight: bold;")
        boutique_layout.addWidget(rs_title)

        self.input_facebook  = _champ("Facebook :",  "fb.com/maboutique ou @MaBoutique")
        self.input_instagram = _champ("Instagram :", "@maboutique")
        self.input_whatsapp  = _champ("WhatsApp :",  "+229 XX XX XX XX")

        boutique_layout.addSpacing(4)

        # Message pied de page
        msg_label = QLabel("Message pied de page :")
        msg_label.setStyleSheet("font-size: 10pt;")
        boutique_layout.addWidget(msg_label)
        self.input_message_pied = QLineEdit()
        self.input_message_pied.setPlaceholderText("Ex: Retour accepté sous 7 jours avec ticket de caisse")
        self.input_message_pied.setStyleSheet(f"padding: 6px; border: 1px solid {Theme.c('gray')}; border-radius: 4px;")
        boutique_layout.addWidget(self.input_message_pied)

        # Logo boutique
        boutique_layout.addSpacing(10)
        logo_title = QLabel("Logo boutique :")
        logo_title.setStyleSheet("font-size: 10pt;")
        boutique_layout.addWidget(logo_title)

        logo_row = QHBoxLayout()

        self._label_logo_preview = QLabel("Aucun\nlogo")
        self._label_logo_preview.setFixedSize(80, 80)
        self._label_logo_preview.setAlignment(Qt.AlignCenter)
        self._label_logo_preview.setStyleSheet(
            f"border: 1px dashed {Theme.c('gray')}; border-radius: 4px; "
            f"background: white; color: {Theme.c('gray')}; font-size: 9pt;"
        )
        logo_row.addWidget(self._label_logo_preview)

        logo_btns = QVBoxLayout()
        btn_choisir_logo = QPushButton("Choisir un logo…")
        btn_choisir_logo.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.c('info')};
                color: white; padding: 8px 12px;
                border-radius: 4px; font-weight: bold;
            }}
            QPushButton:hover {{ background-color: #0284C7; }}
        """)
        btn_choisir_logo.clicked.connect(self._choisir_logo)
        logo_btns.addWidget(btn_choisir_logo)

        self._btn_suppr_logo = QPushButton("Supprimer le logo")
        self._btn_suppr_logo.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.c('danger')};
                color: white; padding: 8px 12px;
                border-radius: 4px;
            }}
            QPushButton:hover {{ background-color: #DC2626; }}
        """)
        self._btn_suppr_logo.clicked.connect(self._supprimer_logo)
        logo_btns.addWidget(self._btn_suppr_logo)
        logo_btns.addStretch()

        logo_row.addLayout(logo_btns)
        logo_row.addStretch()
        boutique_layout.addLayout(logo_row)

        logo_hint = QLabel("PNG ou JPG recommandé · Sera affiché sur les reçus PDF et en filigrane.")
        logo_hint.setStyleSheet(f"color: {Theme.c('gray')}; font-size: 9pt;")
        boutique_layout.addWidget(logo_hint)

        content_layout.addWidget(boutique_frame)

        content_layout.addSpacing(20)

        # === APPARENCE ===
        app_label = QLabel("Apparence")
        app_label.setStyleSheet(f"font-size: 14pt; font-weight: bold; color: {Theme.c('dark')};")
        content_layout.addWidget(app_label)

        app_desc = QLabel("Personnalisez la couleur principale de l'interface. Le changement s'applique immédiatement, sans redémarrage.")
        app_desc.setStyleSheet(f"color: {Theme.c('gray')}; font-size: 10pt;")
        app_desc.setWordWrap(True)
        content_layout.addWidget(app_desc)

        app_frame = QFrame()
        app_frame.setStyleSheet(f"background-color: {Theme.c('light')}; border-radius: 8px; padding: 20px;")
        app_frame_layout = QHBoxLayout(app_frame)
        app_frame_layout.setSpacing(12)

        couleur_lbl = QLabel("Couleur principale :")
        couleur_lbl.setStyleSheet("font-size: 10pt;")
        app_frame_layout.addWidget(couleur_lbl)

        self._btn_couleur_primaire = QPushButton()
        self._btn_couleur_primaire.setFixedSize(40, 40)
        self._btn_couleur_primaire.setToolTip("Cliquer pour changer la couleur")
        self._btn_couleur_primaire.setCursor(Qt.PointingHandCursor)
        self._btn_couleur_primaire.clicked.connect(self._choisir_couleur_primaire)
        app_frame_layout.addWidget(self._btn_couleur_primaire)

        self._lbl_couleur_hex = QLabel()
        self._lbl_couleur_hex.setStyleSheet(f"color: {Theme.c('gray')}; font-size: 10pt; font-family: Consolas;")
        app_frame_layout.addWidget(self._lbl_couleur_hex)

        app_frame_layout.addStretch()

        btn_reset_couleur = QPushButton("Réinitialiser")
        btn_reset_couleur.setProperty("class", "secondary")
        btn_reset_couleur.setCursor(Qt.PointingHandCursor)
        btn_reset_couleur.clicked.connect(self._reinitialiser_couleur)
        app_frame_layout.addWidget(btn_reset_couleur)

        content_layout.addWidget(app_frame)

        content_layout.addSpacing(20)

        # === CACHETS PDF ===
        cachet_label = QLabel("Cachets sur le reçu PDF")
        cachet_label.setStyleSheet(f"font-size: 13pt; font-weight: bold; color: {Theme.c('text')};")
        content_layout.addWidget(cachet_label)
        cachet_desc = QLabel(
            "Affiche un tampon diagonal (PAYÉ / À CRÉDIT) sur les reçus PDF générés. "
            "Désactivez si vous préférez un reçu sans mention de statut."
        )
        cachet_desc.setStyleSheet(f"color: {Theme.c('text_secondary')}; font-size: 10pt;")
        cachet_desc.setWordWrap(True)
        content_layout.addWidget(cachet_desc)

        cachet_frame = QFrame()
        cachet_frame.setStyleSheet(f"background-color: {Theme.c('light')}; border-radius: 8px; padding: 16px;")
        cachet_frame_layout = QVBoxLayout(cachet_frame)
        cachet_frame_layout.setSpacing(8)

        self.checkbox_cachet_vente = self._chk("Afficher 'PAYÉ' sur les reçus de vente normale")
        cachet_frame_layout.addWidget(self.checkbox_cachet_vente)

        self.checkbox_cachet_credit = self._chk("Afficher 'À CRÉDIT' sur les reçus de vente à crédit")
        cachet_frame_layout.addWidget(self.checkbox_cachet_credit)

        self.checkbox_cachet_encaissement = self._chk("Afficher 'SOLDÉ' / 'À CRÉDIT' sur les reçus de remboursement ardoise")
        cachet_frame_layout.addWidget(self.checkbox_cachet_encaissement)

        content_layout.addWidget(cachet_frame)

        content_layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        close_btn = QPushButton("Fermer")
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: {Theme.c('light')}; color: {Theme.c('text')};
                padding: 12px 24px; font-size: 11pt;
                border-radius: 6px; border: 1px solid {Theme.c('card_border')};
            }}
            QPushButton:hover {{ background: {Theme.c('card_border')}; }}
        """)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.reject)
        btn_layout.addWidget(close_btn)

        self._btn_enregistrer = QPushButton("Enregistrer")
        self._btn_enregistrer.setCursor(Qt.PointingHandCursor)
        self._btn_enregistrer.setStyleSheet(self._style_save_neutre())
        self._btn_enregistrer.clicked.connect(self._enregistrer)
        btn_layout.addWidget(self._btn_enregistrer)

        content_layout.addLayout(btn_layout)

        # QScrollArea sans scroll horizontal
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        scroll.setWidget(content)
        layout.addWidget(scroll)

    def _charger_parametres(self):
        """Charger les paramètres actuels"""
        # Mode de scan
        mode_auto = db.get_parametre('mode_scan_auto', '1') == '1'
        if mode_auto:
            self.radio_auto.setChecked(True)
        else:
            self.radio_manuel.setChecked(True)

        # Son de scan
        son_actif = db.get_parametre('son_scan_actif', '1') == '1'
        self.checkbox_son.setChecked(son_actif)

        # Scanner caméra — toggle maître (désactivé par défaut)
        camera_actif = db.get_parametre('scanner_camera_actif', '0') == '1'
        self.checkbox_camera_actif.setChecked(camera_actif)
        self._camera_suboptions.setEnabled(camera_actif)

        # Caméra auto-start
        camera_auto = db.get_parametre('camera_auto_start', '0') == '1'
        self.checkbox_camera_auto.setChecked(camera_auto)

        # Source caméra
        camera_source = db.get_parametre('camera_source', '0')
        self.input_camera_source.setText(camera_source)

        # Mode imprimante
        mode_imp = db.get_parametre('imprimante_mode', 'usb')
        mode_map = {'usb': 0, 'reseau': 1, 'serie': 2}
        self.combo_imp_mode.setCurrentIndex(mode_map.get(mode_imp, 0))

        # Infos boutique
        from config import BOUTIQUE_NOM, BOUTIQUE_ADRESSE, BOUTIQUE_TELEPHONE, BOUTIQUE_EMAIL
        self.input_nom_boutique.setText(db.get_parametre('boutique_nom', BOUTIQUE_NOM))
        self.input_adresse_boutique.setText(db.get_parametre('boutique_adresse', BOUTIQUE_ADRESSE))
        self.input_tel_boutique.setText(db.get_parametre('boutique_telephone', BOUTIQUE_TELEPHONE))
        self.input_email_boutique.setText(db.get_parametre('boutique_email', BOUTIQUE_EMAIL))
        self.input_ifu_boutique.setText(db.get_parametre('boutique_ifu', ''))
        self.input_rccm_boutique.setText(db.get_parametre('boutique_rccm', ''))
        self.input_facebook.setText(db.get_parametre('boutique_facebook', ''))
        self.input_instagram.setText(db.get_parametre('boutique_instagram', ''))
        self.input_whatsapp.setText(db.get_parametre('boutique_whatsapp', ''))
        self.input_message_pied.setText(db.get_parametre('recu_message_pied', ''))
        self._actualiser_apercu_logo(db.get_parametre('boutique_logo_path', ''))

        # Remise par défaut
        remise_pct = db.get_parametre('remise_type_defaut', 'pct') == 'pct'
        self.radio_remise_pct.setChecked(remise_pct)
        self.radio_remise_montant.setChecked(not remise_pct)

        # Code-barres par défaut
        cb_auto = db.get_parametre('barcode_mode_defaut', 'auto') == 'auto'
        self.radio_cb_auto.setChecked(cb_auto)
        self.radio_cb_manuel.setChecked(not cb_auto)

        # TVA par défaut
        tva_val = db.get_parametre('tva_taux_defaut', '18')
        for i in range(self._combo_tva.count()):
            if self._combo_tva.itemData(i) == tva_val:
                self._combo_tva.setCurrentIndex(i)
                break

        # Seuil alerte stock
        try:
            alerte_val = int(db.get_parametre('stock_alerte_seuil_defaut', '5'))
        except ValueError:
            alerte_val = 5
        self._spin_alerte_stock.setValue(alerte_val)

        # Durée de session (session_timeout est en secondes, 0 = jamais)
        session_val = db.get_parametre('session_timeout', '0')
        for i in range(self._combo_session.count()):
            if self._combo_session.itemData(i) == session_val:
                self._combo_session.setCurrentIndex(i)
                break

        # Cachets PDF
        self.checkbox_cachet_vente.setChecked(db.get_parametre('cachet_recu_vente', '1') == '1')
        self.checkbox_cachet_credit.setChecked(db.get_parametre('cachet_recu_credit', '1') == '1')
        self.checkbox_cachet_encaissement.setChecked(db.get_parametre('cachet_recu_encaissement', '1') == '1')

        # Couleur primaire
        couleur = db.get_parametre('theme_couleur_primaire', Theme.c('primary'))
        self._actualiser_btn_couleur(couleur)

    def _enregistrer(self):
        """Sauvegarder les paramètres"""
        # Mode de scan
        mode_auto = '1' if self.radio_auto.isChecked() else '0'
        db.set_parametre('mode_scan_auto', mode_auto)

        # Son de scan
        son_actif = '1' if self.checkbox_son.isChecked() else '0'
        db.set_parametre('son_scan_actif', son_actif)
        db.set_parametre('son_scan_type', 'beep')

        # Scanner caméra
        db.set_parametre('scanner_camera_actif', '1' if self.checkbox_camera_actif.isChecked() else '0')
        db.set_parametre('camera_auto_start', '1' if self.checkbox_camera_auto.isChecked() else '0')
        db.set_parametre('camera_source', self.input_camera_source.text().strip() or '0')

        # Mode imprimante
        mode_imp_map = ['usb', 'reseau', 'serie']
        db.set_parametre('imprimante_mode', mode_imp_map[self.combo_imp_mode.currentIndex()])

        # Infos boutique
        nom = self.input_nom_boutique.text().strip()
        adresse = self.input_adresse_boutique.text().strip()
        tel = self.input_tel_boutique.text().strip()
        email = self.input_email_boutique.text().strip()
        if nom:
            db.set_parametre('boutique_nom', nom)
        if adresse:
            db.set_parametre('boutique_adresse', adresse)
        if tel:
            db.set_parametre('boutique_telephone', tel)
        if email:
            db.set_parametre('boutique_email', email)
        db.set_parametre('boutique_ifu', self.input_ifu_boutique.text().strip())
        db.set_parametre('boutique_rccm', self.input_rccm_boutique.text().strip())
        db.set_parametre('boutique_facebook', self.input_facebook.text().strip())
        db.set_parametre('boutique_instagram', self.input_instagram.text().strip())
        db.set_parametre('boutique_whatsapp', self.input_whatsapp.text().strip())
        db.set_parametre('recu_message_pied', self.input_message_pied.text().strip())

        # Remise par défaut
        db.set_parametre('remise_type_defaut', 'pct' if self.radio_remise_pct.isChecked() else 'montant')

        # Code-barres par défaut
        db.set_parametre('barcode_mode_defaut', 'auto' if self.radio_cb_auto.isChecked() else 'manuel')

        # TVA par défaut
        db.set_parametre('tva_taux_defaut', self._combo_tva.currentData())

        # Seuil alerte stock
        db.set_parametre('stock_alerte_seuil_defaut', str(self._spin_alerte_stock.value()))

        # Durée de session (en secondes, 0 = jamais)
        db.set_parametre('session_timeout', self._combo_session.currentData())

        # Cachets PDF
        db.set_parametre('cachet_recu_vente',        '1' if self.checkbox_cachet_vente.isChecked()         else '0')
        db.set_parametre('cachet_recu_credit',       '1' if self.checkbox_cachet_credit.isChecked()        else '0')
        db.set_parametre('cachet_recu_encaissement', '1' if self.checkbox_cachet_encaissement.isChecked()  else '0')

        self._modifie = False
        self._btn_enregistrer.setStyleSheet(self._style_save_neutre())
        information(self, "Paramètres sauvegardés", "Paramètres enregistrés avec succès.")
        self.accept()

    def reject(self):
        if self._modifie:
            from PySide6.QtWidgets import QMessageBox
            rep = QMessageBox.question(
                self, "Modifications non sauvegardées",
                "Vous avez des modifications non enregistrées.\n\nVoulez-vous les enregistrer avant de fermer ?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save
            )
            if rep == QMessageBox.Save:
                self._enregistrer()
                return
            elif rep == QMessageBox.Cancel:
                return
        super().reject()

    def closeEvent(self, event):
        if self._modifie:
            from PySide6.QtWidgets import QMessageBox
            rep = QMessageBox.question(
                self, "Modifications non sauvegardées",
                "Vous avez des modifications non enregistrées.\n\nVoulez-vous les enregistrer avant de fermer ?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save
            )
            if rep == QMessageBox.Save:
                self._enregistrer()
                event.accept()
            elif rep == QMessageBox.Discard:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    def _choisir_logo(self):
        chemin, _ = QFileDialog.getOpenFileName(
            self, "Choisir un logo", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif *.webp)"
        )
        if not chemin:
            return
        from config import IMAGES_DIR
        dest = os.path.join(IMAGES_DIR, 'logo_boutique.png')
        try:
            px = QPixmap(chemin)
            if px.isNull():
                erreur(self, "Erreur", "Impossible de lire cette image.")
                return
            px.save(dest, 'PNG')
            db.set_parametre('boutique_logo_path', dest)
            self._actualiser_apercu_logo(dest)
            information(self, "Logo enregistré", "Le logo a été enregistré avec succès.")
        except Exception as e:
            erreur(self, "Erreur", f"Impossible d'enregistrer le logo : {e}")

    def _supprimer_logo(self):
        db.set_parametre('boutique_logo_path', '')
        self._actualiser_apercu_logo('')
        information(self, "Logo supprimé", "Le logo a été supprimé.")

    def _actualiser_apercu_logo(self, logo_path):
        if logo_path and os.path.exists(logo_path):
            px = QPixmap(logo_path).scaled(76, 76, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self._label_logo_preview.setPixmap(px)
            self._label_logo_preview.setText('')
        else:
            self._label_logo_preview.clear()
            self._label_logo_preview.setText("Aucun\nlogo")

    def _actualiser_btn_couleur(self, hex_color: str):
        from PySide6.QtGui import QColor
        if not QColor(hex_color).isValid():
            hex_color = Theme.c('primary')
        self._btn_couleur_primaire.setStyleSheet(
            f"QPushButton {{ background-color: {hex_color}; border-radius: 6px; border: 2px solid rgba(0,0,0,0.2); }}"
            f"QPushButton:hover {{ border: 2px solid rgba(0,0,0,0.4); }}"
        )
        self._lbl_couleur_hex.setText(hex_color.upper())

    def _choisir_couleur_primaire(self):
        from PySide6.QtGui import QColor
        couleur_actuelle = db.get_parametre('theme_couleur_primaire', Theme.c('primary'))
        couleur = QColorDialog.getColor(QColor(couleur_actuelle), self, "Choisir la couleur principale")
        if couleur.isValid():
            hex_color = couleur.name()
            Theme.appliquer_couleur_primaire(hex_color, sauvegarder=True)
            self._actualiser_btn_couleur(hex_color)

    def _reinitialiser_couleur(self):
        hex_default = '#3B82F6'
        Theme.appliquer_couleur_primaire(hex_default, sauvegarder=True)
        self._actualiser_btn_couleur(hex_default)

    def _tester_impression(self):
        """Tester l'impression thermique"""
        from modules.imprimante import ImprimanteThermique

        if not ImprimanteThermique.est_disponible():
            erreur(self, "Module manquant", "python-escpos n'est pas installé.\nInstallez-le avec : pip install python-escpos")
            return

        mode_imp_map = ['usb', 'reseau', 'serie']
        db.set_parametre('imprimante_mode', mode_imp_map[self.combo_imp_mode.currentIndex()])

        ok, msg = ImprimanteThermique.imprimer_test()
        if ok:
            information(self, "Test réussi", msg)
        else:
            erreur(self, "Échec du test", msg)

    def _tester_camera(self):
        """Tester la connexion à la caméra"""
        try:
            import cv2
        except ImportError:
            erreur(self, "Erreur", "opencv-python n'est pas installé.\nInstallez-le avec : pip install opencv-python")
            return

        source = self.input_camera_source.text().strip() or '0'

        # Convertir en int si possible
        try:
            source = int(source)
        except ValueError:
            pass  # C'est une URL

        cap = cv2.VideoCapture(source)
        if cap.isOpened():
            ret, frame = cap.read()
            cap.release()
            if ret:
                information(self, "Test réussi", f"✓ Caméra connectée avec succès !\nSource : {source}")
            else:
                erreur(self, "Erreur", f"Caméra trouvée mais impossible de lire les images.\nVérifiez que la caméra n'est pas utilisée par une autre application.")
        else:
            erreur(self, "Erreur de connexion",
                f"Impossible de se connecter à la caméra.\n\n"
                f"Source testée : {source}\n\n"
                f"Vérifications :\n"
                f"• Pour webcam PC : essayez 0, 1 ou 2\n"
                f"• Pour téléphone : vérifiez l'URL (http://IP:PORT/video)\n"
                f"• Assurez-vous que l'app mobile est lancée\n"
                f"• Vérifiez que PC et téléphone sont sur le même WiFi"
            )
