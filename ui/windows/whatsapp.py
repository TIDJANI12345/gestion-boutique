"""
Export WhatsApp - Generer message catalogue pour revendeurs
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QPushButton, QLineEdit, QTextEdit, QCheckBox, QRadioButton,
    QScrollArea, QWidget, QApplication, QButtonGroup
)
from PySide6.QtCore import Qt

from ui.theme import Theme
from ui.components.dialogs import information
from modules.whatsapp import WhatsAppExport
from modules.produits import Produit


class WhatsAppWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Export WhatsApp")
        self.resize(1200, 750)
        self.setStyleSheet(Theme.stylesheet())

        self.categories_vars = {}
        self._setup_ui()
        self._charger_categories()
        self._generer_apercu()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QFrame()
        header.setStyleSheet(f"background-color: {Theme.c('warning')};")
        header.setFixedHeight(80)

        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(30, 0, 30, 0)

        title = QLabel("📱 Export WhatsApp")
        title.setStyleSheet("color: white; font-size: 22pt; font-weight: bold;")
        header_layout.addWidget(title)

        subtitle = QLabel("Générez un message formaté pour vos revendeurs")
        subtitle.setStyleSheet("color: white; font-size: 11pt;")
        header_layout.addWidget(subtitle)
        header_layout.addStretch()

        layout.addWidget(header)

        # Main content
        main = QFrame()
        main_layout = QHBoxLayout(main)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Left column
        left_col = QFrame()
        left_layout = QVBoxLayout(left_col)
        left_layout.setSpacing(15)

        # Message section
        msg_panel = self._create_panel("✏️ Message principal")
        msg_inner = QVBoxLayout()
        msg_inner.setContentsMargins(20, 15, 20, 15)

        msg_inner.addWidget(QLabel("Titre du message"))
        self.titre_entry = QLineEdit("🛒 PRODUITS DISPONIBLES")
        self.titre_entry.textChanged.connect(self._generer_apercu)
        msg_inner.addWidget(self.titre_entry)

        msg_inner.addSpacing(10)
        msg_inner.addWidget(QLabel("Message de fin (optionnel)"))
        self.message_fin = QTextEdit()
        self.message_fin.setFixedHeight(70)
        self.message_fin.textChanged.connect(self._generer_apercu)
        msg_inner.addWidget(self.message_fin)

        msg_panel.layout().addLayout(msg_inner)
        left_layout.addWidget(msg_panel)

        # Options section
        opt_panel = self._create_panel("🎨 Options de formatage")
        opt_inner = QVBoxLayout()
        opt_inner.setContentsMargins(20, 15, 20, 15)

        self.grouper_check = QCheckBox("📂 Grouper par catégories")
        self.grouper_check.setChecked(True)
        self.grouper_check.stateChanged.connect(self._generer_apercu)
        opt_inner.addWidget(self.grouper_check)

        self.stock_check = QCheckBox("📊 Afficher les stocks")
        self.stock_check.setChecked(True)
        self.stock_check.stateChanged.connect(self._generer_apercu)
        opt_inner.addWidget(self.stock_check)

        self.stock_only_check = QCheckBox("✅ Produits en stock uniquement")
        self.stock_only_check.setChecked(True)
        self.stock_only_check.stateChanged.connect(self._generer_apercu)
        opt_inner.addWidget(self.stock_only_check)

        self.prix_achat_check = QCheckBox("💵 Afficher prix d'achat")
        self.prix_achat_check.stateChanged.connect(self._generer_apercu)
        opt_inner.addWidget(self.prix_achat_check)

        opt_inner.addSpacing(10)
        opt_inner.addWidget(QLabel("Style d'emojis"))

        emoji_group = QButtonGroup(self)
        emoji_frame = QHBoxLayout()

        self.emoji_classic = QRadioButton("🛒 Classique")
        self.emoji_classic.setChecked(True)
        self.emoji_classic.toggled.connect(self._generer_apercu)
        emoji_group.addButton(self.emoji_classic)
        emoji_frame.addWidget(self.emoji_classic)

        self.emoji_modern = QRadioButton("🔥 Moderne")
        self.emoji_modern.toggled.connect(self._generer_apercu)
        emoji_group.addButton(self.emoji_modern)
        emoji_frame.addWidget(self.emoji_modern)

        self.emoji_pro = QRadioButton("📋 Professionnel")
        self.emoji_pro.toggled.connect(self._generer_apercu)
        emoji_group.addButton(self.emoji_pro)
        emoji_frame.addWidget(self.emoji_pro)

        emoji_frame.addStretch()
        opt_inner.addLayout(emoji_frame)

        opt_panel.layout().addLayout(opt_inner)
        left_layout.addWidget(opt_panel)

        # Categories section
        cat_panel = self._create_panel("📂 Catégories à inclure")
        cat_scroll = QScrollArea()
        cat_scroll.setWidgetResizable(True)
        cat_scroll.setFrameShape(QFrame.NoFrame)

        self.cat_widget = QWidget()
        self.cat_layout = QVBoxLayout(self.cat_widget)
        self.cat_layout.setAlignment(Qt.AlignTop)
        cat_scroll.setWidget(self.cat_widget)

        cat_panel.layout().addWidget(cat_scroll)
        left_layout.addWidget(cat_panel, 1)

        main_layout.addWidget(left_col, 1)

        # Right column
        right_col = QFrame()
        right_col.setFixedWidth(400)
        right_layout = QVBoxLayout(right_col)
        right_layout.setSpacing(15)

        # Preview section
        preview_panel = self._create_panel("👁️ Aperçu")
        preview_inner = QVBoxLayout()
        preview_inner.setContentsMargins(15, 15, 15, 15)

        self.apercu_text = QTextEdit()
        self.apercu_text.setReadOnly(True)
        self.apercu_text.setStyleSheet(f"background-color: {Theme.c('light')}; font-family: 'Courier New'; font-size: 9pt;")
        preview_inner.addWidget(self.apercu_text)

        preview_panel.layout().addLayout(preview_inner)
        right_layout.addWidget(preview_panel, 1)

        # Actions section
        actions_panel = self._create_panel("")
        actions_inner = QVBoxLayout()
        actions_inner.setContentsMargins(20, 20, 20, 20)

        copy_btn = QPushButton("📋 Copier le message")
        copy_btn.setObjectName("primaryButton")
        copy_btn.setStyleSheet(f"""
            QPushButton#primaryButton {{
                background-color: {Theme.c('success')};
                font-size: 12pt;
                font-weight: bold;
                padding: 15px;
            }}
        """)
        copy_btn.clicked.connect(self._copier_message)
        actions_inner.addWidget(copy_btn)

        save_btn = QPushButton("💾 Sauvegarder")
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.c('info')};
                color: white;
                font-size: 11pt;
                padding: 12px;
                border-radius: 4px;
            }}
        """)
        save_btn.clicked.connect(self._sauvegarder)
        actions_inner.addWidget(save_btn)

        actions_panel.layout().addLayout(actions_inner)
        right_layout.addWidget(actions_panel)

        main_layout.addWidget(right_col)

        layout.addWidget(main)

    def _create_panel(self, title):
        """Create a styled panel with title"""
        panel = QFrame()
        panel.setStyleSheet(f"background-color: white; border: 1px solid {Theme.c('card_border')}; border-radius: 4px;")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(0)

        if title:
            title_label = QLabel(title)
            title_label.setStyleSheet(f"font-size: 13pt; font-weight: bold; color: {Theme.c('dark')}; padding: 15px 20px 10px 20px;")
            panel_layout.addWidget(title_label)

            sep = QFrame()
            sep.setFrameShape(QFrame.HLine)
            sep.setStyleSheet(f"background-color: {Theme.c('light')};")
            sep.setFixedHeight(1)
            panel_layout.addWidget(sep)

        return panel

    def _charger_categories(self):
        """Load categories with checkboxes"""
        categories = Produit.obtenir_par_categorie()

        # All categories checkbox
        toutes_check = QCheckBox("✅ Toutes les catégories")
        toutes_check.setChecked(True)
        toutes_check.setStyleSheet("font-weight: bold;")
        toutes_check.stateChanged.connect(self._toggle_toutes)
        self.categories_vars['_TOUTES_'] = toutes_check
        self.cat_layout.addWidget(toutes_check)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"background-color: {Theme.c('light')};")
        sep.setFixedHeight(1)
        self.cat_layout.addWidget(sep)

        # Individual categories
        for categorie, produits in sorted(categories.items()):
            check = QCheckBox(f"{categorie} ({len(produits)})")
            check.setChecked(True)
            check.stateChanged.connect(self._generer_apercu)
            self.categories_vars[categorie] = check
            self.cat_layout.addWidget(check)

    def _toggle_toutes(self):
        """Toggle all categories"""
        etat = self.categories_vars['_TOUTES_'].isChecked()
        for key, check in self.categories_vars.items():
            if key != '_TOUTES_':
                check.setChecked(etat)
        self._generer_apercu()

    def _generer_apercu(self):
        """Generate preview"""
        categories_selectionnees = [
            cat for cat, check in self.categories_vars.items()
            if cat != '_TOUTES_' and check.isChecked()
        ]

        emoji_style = "classic"
        if self.emoji_modern.isChecked():
            emoji_style = "modern"
        elif self.emoji_pro.isChecked():
            emoji_style = "professional"

        options = {
            'titre': self.titre_entry.text(),
            'message_fin': self.message_fin.toPlainText().strip(),
            'grouper_categories': self.grouper_check.isChecked(),
            'afficher_stock': self.stock_check.isChecked(),
            'stock_min_only': self.stock_only_check.isChecked(),
            'inclure_prix_achat': self.prix_achat_check.isChecked(),
            'emoji_style': emoji_style,
            'categories': categories_selectionnees if categories_selectionnees else None
        }

        message = WhatsAppExport.generer_message(options)
        self.apercu_text.setPlainText(message)

    def _copier_message(self):
        """Copy message to clipboard"""
        message = self.apercu_text.toPlainText().strip()
        QApplication.clipboard().setText(message)
        information(self, "Succes", "✅ Message copié dans le presse-papiers!\n\nVous pouvez maintenant le coller dans WhatsApp.")

    def _sauvegarder(self):
        """Save export to file"""
        message = self.apercu_text.toPlainText().strip()
        filepath = WhatsAppExport.sauvegarder_export(message)
        if filepath:
            information(self, "Succes", f"✅ Export sauvegardé!\n\n{filepath}")
