"""
Systeme de theme pour l'interface PySide6.
Utilise QSS (Qt Style Sheets) pour un style coherent sur tous les OS.
"""
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont, QPalette, QColor
from PySide6.QtCore import Qt


# Palettes de couleurs (identiques a config.py)
THEME_CLAIR = {
    'primary': '#3B82F6',
    'primary_hover': '#2563EB',
    'primary_pressed': '#1D4ED8',
    'success': '#10B981',
    'success_hover': '#059669',
    'danger': '#EF4444',
    'danger_hover': '#DC2626',
    'warning': '#F59E0B',
    'warning_text': '#B45309',
    'info': '#06B6D4',
    'purple': '#8B5CF6',
    'gray': '#6B7280',
    'dark': '#1F2937',
    'light': '#F3F4F6',
    'white': '#FFFFFF',
    'bg': '#F9FAFB',
    'text': '#1F2937',
    'text_secondary': '#6B7280',
    'card_bg': '#FFFFFF',
    'card_border': '#E5E7EB',
    'input_bg': '#FFFFFF',
    'input_fg': '#1F2937',
    'input_border': '#D1D5DB',
    'input_focus': '#3B82F6',
    'separator': '#E5E7EB',
    'table_header': '#F3F4F6',
    'table_row_alt': '#F9FAFB',
    'table_selection': '#DBEAFE',
    'scrollbar': '#D1D5DB',
    'scrollbar_hover': '#9CA3AF',
}

THEME_SOMBRE = {
    'primary': '#3B82F6',
    'primary_hover': '#60A5FA',
    'primary_pressed': '#2563EB',
    'success': '#10B981',
    'success_hover': '#34D399',
    'danger': '#EF4444',
    'danger_hover': '#F87171',
    'warning': '#F59E0B',
    'warning_text': '#FCD34D',
    'info': '#06B6D4',
    'purple': '#8B5CF6',
    'gray': '#9CA3AF',
    'dark': '#F9FAFB',
    'light': '#374151',
    'white': '#1F2937',
    'bg': '#111827',
    'text': '#F9FAFB',
    'text_secondary': '#9CA3AF',
    'card_bg': '#1F2937',
    'card_border': '#374151',
    'input_bg': '#374151',
    'input_fg': '#F9FAFB',
    'input_border': '#4B5563',
    'input_focus': '#3B82F6',
    'separator': '#374151',
    'table_header': '#374151',
    'table_row_alt': '#1F2937',
    'table_selection': '#1E3A5F',
    'scrollbar': '#4B5563',
    'scrollbar_hover': '#6B7280',
}


class Theme:
    """Gestionnaire de theme pour l'application Qt."""

    _current = dict(THEME_CLAIR)
    _is_dark = False

    @classmethod
    def couleurs(cls) -> dict:
        """Retourne la palette de couleurs active."""
        return cls._current

    @classmethod
    def c(cls, key: str) -> str:
        """Raccourci pour obtenir une couleur. Ex: Theme.c('primary')"""
        return cls._current[key]

    @classmethod
    def est_sombre(cls) -> bool:
        return cls._is_dark

    @classmethod
    def sauvegarder(cls):
        """Persiste le thème actuel en base de données."""
        try:
            from database import db
            db.set_parametre('theme', 'sombre' if cls._is_dark else 'clair')
        except Exception:
            pass

    @classmethod
    def _deriver_variantes(cls, hex_color: str) -> tuple:
        """Dérive hover, pressed, table_selection depuis une couleur primaire hex."""
        c = QColor(hex_color)
        hover = c.darker(115).name()
        pressed = c.darker(130).name()
        r, g, b = c.red(), c.green(), c.blue()
        sel = QColor(int(r * 0.2 + 255 * 0.8), int(g * 0.2 + 255 * 0.8), int(b * 0.2 + 255 * 0.8)).name()
        return hover, pressed, sel

    @classmethod
    def appliquer_couleur_primaire(cls, hex_color: str, sauvegarder: bool = True):
        """Changer la couleur primaire et recharger le style immédiatement."""
        if not QColor(hex_color).isValid():
            return
        hover, pressed, sel = cls._deriver_variantes(hex_color)
        cls._current['primary'] = hex_color
        cls._current['primary_hover'] = hover
        cls._current['primary_pressed'] = pressed
        cls._current['input_focus'] = hex_color
        cls._current['table_selection'] = sel
        if sauvegarder:
            try:
                from database import db
                db.set_parametre('theme_couleur_primaire', hex_color)
            except Exception:
                pass
        app = QApplication.instance()
        if app:
            app.setStyleSheet(cls.stylesheet())

    @classmethod
    def charger(cls):
        """Charge le thème sauvegardé depuis la base de données."""
        try:
            from database import db
            valeur = db.get_parametre('theme', 'clair')
            if valeur == 'sombre':
                cls._current = dict(THEME_SOMBRE)
                cls._is_dark = True
            else:
                cls._current = dict(THEME_CLAIR)
                cls._is_dark = False
            couleur = db.get_parametre('theme_couleur_primaire', '')
            if couleur and QColor(couleur).isValid():
                hover, pressed, sel = cls._deriver_variantes(couleur)
                cls._current['primary'] = couleur
                cls._current['primary_hover'] = hover
                cls._current['primary_pressed'] = pressed
                cls._current['input_focus'] = couleur
                cls._current['table_selection'] = sel
        except Exception:
            pass

    @classmethod
    def basculer(cls):
        """Bascule entre theme clair et sombre, et sauvegarde le choix."""
        if cls._is_dark:
            cls._current = dict(THEME_CLAIR)
        else:
            cls._current = dict(THEME_SOMBRE)
        cls._is_dark = not cls._is_dark
        cls.sauvegarder()
        app = QApplication.instance()
        if app:
            app.setStyleSheet(cls.stylesheet())

    @classmethod
    def appliquer_theme_clair(cls):
        cls._current = dict(THEME_CLAIR)
        cls._is_dark = False

    @classmethod
    def appliquer_theme_sombre(cls):
        cls._current = dict(THEME_SOMBRE)
        cls._is_dark = True

    @classmethod
    def appliquer(cls, app: QApplication):
        """Charge le thème sauvegardé puis applique à l'application Qt."""
        cls.charger()
        font = QFont("Segoe UI", 10)
        font.setStyleStrategy(QFont.PreferAntialias)
        app.setFont(font)
        app.setStyleSheet(cls.stylesheet())

    @classmethod
    def stylesheet(cls) -> str:
        """Genere le QSS global de l'application."""
        c = cls._current
        return f"""
        /* === BASE === */
        QMainWindow, QDialog {{
            background-color: {c['bg']};
            color: {c['text']};
        }}

        QWidget {{
            color: {c['text']};
        }}

        /* === LABELS === */
        QLabel {{
            color: {c['text']};
            background: transparent;
        }}

        /* === BOUTONS === */
        QPushButton {{
            background-color: {c['primary']};
            color: #FFFFFF;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-weight: bold;
            font-size: 13px;
            min-height: 20px;
        }}

        QPushButton:hover {{
            background-color: {c['primary_hover']};
        }}

        QPushButton:pressed {{
            background-color: {c['primary_pressed']};
        }}

        QPushButton:disabled {{
            background-color: {c['gray']};
            color: #AAAAAA;
        }}

        QPushButton[class="success"] {{
            background-color: {c['success']};
        }}
        QPushButton[class="success"]:hover {{
            background-color: {c['success_hover']};
        }}

        QPushButton[class="danger"] {{
            background-color: {c['danger']};
        }}
        QPushButton[class="danger"]:hover {{
            background-color: {c['danger_hover']};
        }}

        QPushButton[class="secondary"] {{
            background-color: {c['card_bg']};
            color: {c['text']};
            border: 1px solid {c['card_border']};
        }}
        QPushButton[class="secondary"]:hover {{
            background-color: {c['light']};
        }}
        QPushButton[class="secondary"]:disabled {{
            background-color: {c['card_bg']};
            color: {c['text_secondary']};
            border: 1px solid {c['separator']};
            opacity: 0.5;
        }}

        QPushButton[class="warning"] {{
            background-color: {c['warning']};
            color: white;
        }}
        QPushButton[class="warning"]:hover {{
            background-color: #D97706;
        }}
        QPushButton[class="warning"]:disabled {{
            background-color: {c['gray']};
            color: #AAAAAA;
        }}

        /* === CHAMPS DE SAISIE === */
        QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox,
        QDateEdit, QDateTimeEdit, QTimeEdit {{
            background-color: {c['input_bg']};
            color: {c['input_fg']};
            border: 1px solid {c['input_border']};
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 13px;
            min-height: 20px;
        }}

        QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus,
        QDateEdit:focus, QDateTimeEdit:focus, QTimeEdit:focus {{
            border: 2px solid {c['input_focus']};
            padding: 7px 11px;
        }}

        QDateEdit::drop-down, QDateTimeEdit::drop-down, QTimeEdit::drop-down {{
            border: none;
            padding-right: 8px;
        }}

        QDateEdit::down-arrow, QDateTimeEdit::down-arrow {{
            width: 12px;
            height: 12px;
        }}

        QCalendarWidget {{
            background-color: {c['card_bg']};
            color: {c['text']};
        }}

        QCalendarWidget QAbstractItemView {{
            background-color: {c['card_bg']};
            color: {c['text']};
            selection-background-color: {c['table_selection']};
            selection-color: {c['text']};
        }}

        QCalendarWidget QWidget#qt_calendar_navigationbar {{
            background-color: {c['primary']};
            color: white;
        }}

        QCalendarWidget QToolButton {{
            background-color: transparent;
            color: white;
        }}

        QComboBox::drop-down {{
            border: none;
            padding-right: 8px;
        }}

        QComboBox QAbstractItemView {{
            background-color: {c['card_bg']};
            color: {c['text']};
            border: 1px solid {c['card_border']};
            selection-background-color: {c['table_selection']};
        }}

        QTextEdit {{
            background-color: {c['input_bg']};
            color: {c['input_fg']};
            border: 1px solid {c['input_border']};
            border-radius: 6px;
            padding: 8px;
            font-size: 13px;
        }}

        /* === TABLEAUX === */
        QTableView {{
            background-color: {c['card_bg']};
            alternate-background-color: {c['table_row_alt']};
            color: {c['text']};
            border: 1px solid {c['card_border']};
            border-radius: 6px;
            gridline-color: {c['separator']};
            selection-background-color: {c['table_selection']};
            selection-color: {c['text']};
            font-size: 13px;
        }}

        QTableView::item {{
            padding: 6px 8px;
        }}

        QHeaderView::section {{
            background-color: {c['table_header']};
            color: {c['text']};
            border: none;
            border-bottom: 2px solid {c['separator']};
            padding: 8px 8px;
            font-weight: bold;
            font-size: 13px;
        }}

        /* === CARTES (QGroupBox) === */
        QGroupBox {{
            background-color: {c['card_bg']};
            border: 1px solid {c['card_border']};
            border-radius: 8px;
            margin-top: 16px;
            padding: 16px;
            font-weight: bold;
            font-size: 14px;
        }}

        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 6px;
            color: {c['text']};
        }}

        /* === ONGLETS === */
        QTabWidget::pane {{
            border: 1px solid {c['card_border']};
            border-radius: 6px;
            background-color: {c['card_bg']};
        }}

        QTabBar::tab {{
            background-color: {c['light']};
            color: {c['text_secondary']};
            border: none;
            padding: 10px 20px;
            font-size: 13px;
            margin-right: 2px;
        }}

        QTabBar::tab:selected {{
            background-color: {c['card_bg']};
            color: {c['primary']};
            border-bottom: 2px solid {c['primary']};
            font-weight: bold;
        }}

        QTabBar::tab:hover {{
            background-color: {c['card_bg']};
            color: {c['text']};
        }}

        /* === SCROLLBARS === */
        QScrollBar:vertical {{
            background-color: transparent;
            width: 10px;
            margin: 0;
        }}

        QScrollBar::handle:vertical {{
            background-color: {c['scrollbar']};
            border-radius: 5px;
            min-height: 30px;
        }}

        QScrollBar::handle:vertical:hover {{
            background-color: {c['scrollbar_hover']};
        }}

        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0;
        }}

        QScrollBar:horizontal {{
            background-color: transparent;
            height: 10px;
            margin: 0;
        }}

        QScrollBar::handle:horizontal {{
            background-color: {c['scrollbar']};
            border-radius: 5px;
            min-width: 30px;
        }}

        QScrollBar::handle:horizontal:hover {{
            background-color: {c['scrollbar_hover']};
        }}

        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0;
        }}

        /* === SEPARATEURS === */
        QFrame[frameShape="4"], QFrame[frameShape="5"] {{
            color: {c['separator']};
        }}

        /* === SPLITTER === */
        QSplitter::handle {{
            background-color: {c['separator']};
        }}

        QSplitter::handle:horizontal {{
            width: 2px;
        }}

        QSplitter::handle:vertical {{
            height: 2px;
        }}

        /* === DIALOGS SYSTEME === */
        QMessageBox {{
            background-color: {c['card_bg']};
            color: {c['text']};
        }}

        QMessageBox QLabel {{
            color: {c['text']};
            background: transparent;
        }}

        QInputDialog {{
            background-color: {c['card_bg']};
            color: {c['text']};
        }}

        QFileDialog {{
            background-color: {c['bg']};
            color: {c['text']};
        }}

        /* === TOOLTIPS === */
        QToolTip {{
            background-color: {c['dark']};
            color: #FFFFFF;
            border: none;
            border-radius: 4px;
            padding: 6px 10px;
            font-size: 12px;
        }}

        /* === MENUS === */
        QMenuBar {{
            background-color: {c['card_bg']};
            color: {c['text']};
            border-bottom: 1px solid {c['separator']};
        }}

        QMenuBar::item:selected {{
            background-color: {c['table_selection']};
        }}

        QMenu {{
            background-color: {c['card_bg']};
            color: {c['text']};
            border: 1px solid {c['card_border']};
            border-radius: 6px;
            padding: 4px;
        }}

        QMenu::item {{
            padding: 8px 24px;
            border-radius: 4px;
        }}

        QMenu::item:selected {{
            background-color: {c['table_selection']};
        }}

        /* === STATUS BAR === */
        QStatusBar {{
            background-color: {c['card_bg']};
            color: {c['text_secondary']};
            border-top: 1px solid {c['separator']};
        }}

        /* === PROGRESS BAR === */
        QProgressBar {{
            background-color: {c['light']};
            border: none;
            border-radius: 4px;
            text-align: center;
            color: {c['text']};
            font-size: 12px;
            min-height: 8px;
        }}

        QProgressBar::chunk {{
            background-color: {c['primary']};
            border-radius: 4px;
        }}

        /* === CARTES / PANELS DASHBOARD === */
        QFrame[role="card"] {{
            background-color: {c['card_bg']};
            border: 1px solid {c['card_border']};
            border-radius: 8px;
        }}

        QFrame[role="footer-bar"] {{
            background-color: {c['light']};
        }}

        QTextEdit[role="panel-text"] {{
            background-color: {c['card_bg']};
            color: {c['text']};
            border: none;
            font-size: 12px;
        }}

        /* === SCROLL AREA === */
        QScrollArea {{
            background-color: {c['bg']};
            border: none;
        }}

        QScrollArea > QWidget > QWidget {{
            background-color: {c['bg']};
        }}

        /* === LISTE === */
        QListWidget {{
            background-color: {c['card_bg']};
            color: {c['text']};
            border: 1px solid {c['card_border']};
            border-radius: 6px;
            font-size: 13px;
        }}

        QListWidget::item {{
            padding: 6px 10px;
            border-radius: 4px;
        }}

        QListWidget::item:selected {{
            background-color: {c['table_selection']};
            color: {c['text']};
        }}

        QListWidget::item:hover {{
            background-color: {c['light']};
        }}

        /* === CHECKBOX & RADIO === */
        QCheckBox, QRadioButton {{
            color: {c['text']};
            spacing: 8px;
            font-size: 13px;
        }}

        QCheckBox::indicator, QRadioButton::indicator {{
            width: 18px;
            height: 18px;
        }}
        """
