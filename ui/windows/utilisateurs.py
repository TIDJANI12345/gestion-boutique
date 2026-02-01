"""
Fenetre de gestion des utilisateurs - PySide6
Creation, activation/desactivation, changement de role.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QWidget, QComboBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from ui.theme import Theme
from ui.components.table import BoutiqueTableView, BoutiqueTableModel
from ui.components.dialogs import confirmer, information, erreur


class UtilisateursWindow(QDialog):
    """Fenetre de gestion des utilisateurs."""

    def __init__(self, utilisateur_connecte: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestion des Utilisateurs")
        self.setMinimumSize(1000, 650)
        self.setModal(True)

        self._utilisateur_connecte = utilisateur_connecte
        self._user_selectionne_id = None

        self._setup_ui()
        self._charger_utilisateurs()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # En-tete
        header = QFrame()
        header.setFixedHeight(60)
        header.setStyleSheet(f"background-color: {Theme.c('primary')};")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(30, 0, 30, 0)

        titre = QLabel("Gestion des Utilisateurs")
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
        left.setFixedWidth(350)
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

        lbl_form = QLabel("Nouvel utilisateur")
        lbl_form.setFont(QFont("Segoe UI", 13, QFont.Bold))
        fl.addWidget(lbl_form)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color: {Theme.c('separator')};")
        fl.addWidget(sep)

        fl.addWidget(QLabel("Nom *"))
        self._entry_nom = QLineEdit()
        self._entry_nom.setPlaceholderText("Nom de famille")
        fl.addWidget(self._entry_nom)

        fl.addWidget(QLabel("Prenom *"))
        self._entry_prenom = QLineEdit()
        self._entry_prenom.setPlaceholderText("Prenom")
        fl.addWidget(self._entry_prenom)

        fl.addWidget(QLabel("Email *"))
        self._entry_email = QLineEdit()
        self._entry_email.setPlaceholderText("adresse@email.com")
        fl.addWidget(self._entry_email)

        fl.addWidget(QLabel("Mot de passe *"))
        self._entry_password = QLineEdit()
        self._entry_password.setEchoMode(QLineEdit.Password)
        self._entry_password.setPlaceholderText("8 caracteres min., 1 chiffre")
        fl.addWidget(self._entry_password)

        fl.addWidget(QLabel("Role"))
        self._combo_role = QComboBox()
        self._combo_role.addItems(["caissier", "gestionnaire"])
        fl.addWidget(self._combo_role)

        btn_enregistrer = QPushButton("Enregistrer")
        btn_enregistrer.setFont(QFont("Segoe UI", 11, QFont.Bold))
        btn_enregistrer.setMinimumHeight(42)
        btn_enregistrer.setCursor(Qt.PointingHandCursor)
        btn_enregistrer.setProperty("class", "success")
        btn_enregistrer.clicked.connect(self._creer_utilisateur)
        fl.addWidget(btn_enregistrer)

        left_layout.addWidget(form_frame)
        left_layout.addStretch()

        main_layout.addWidget(left)

        # === COLONNE DROITE (liste) ===
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        # Tableau
        colonnes = ['ID', 'Nom', 'Prenom', 'Email', 'Role', 'Statut']
        self._table_model = BoutiqueTableModel(colonnes)
        self._table_view = BoutiqueTableView()
        self._table_view.setModel(self._table_model)
        self._table_view.ligne_selectionnee.connect(self._selectionner_utilisateur)
        right_layout.addWidget(self._table_view, 1)

        # Boutons d'action
        actions_row = QHBoxLayout()

        self._btn_activer = QPushButton("Activer/Desactiver")
        self._btn_activer.setCursor(Qt.PointingHandCursor)
        self._btn_activer.setProperty("class", "primary")
        self._btn_activer.clicked.connect(self._toggle_statut)
        actions_row.addWidget(self._btn_activer)

        self._btn_super_admin = QPushButton("Passer en Super-Admin")
        self._btn_super_admin.setCursor(Qt.PointingHandCursor)
        self._btn_super_admin.clicked.connect(lambda: self._changer_role("patron"))
        actions_row.addWidget(self._btn_super_admin)

        self._btn_gestionnaire = QPushButton("Passer en Gestionnaire")
        self._btn_gestionnaire.setCursor(Qt.PointingHandCursor)
        self._btn_gestionnaire.clicked.connect(lambda: self._changer_role("gestionnaire"))
        actions_row.addWidget(self._btn_gestionnaire)

        self._btn_caissier = QPushButton("Passer en Caissier")
        self._btn_caissier.setCursor(Qt.PointingHandCursor)
        self._btn_caissier.clicked.connect(lambda: self._changer_role("caissier"))
        actions_row.addWidget(self._btn_caissier)

        self._btn_reset_mdp = QPushButton("🔑 Réinitialiser MDP")
        self._btn_reset_mdp.setCursor(Qt.PointingHandCursor)
        self._btn_reset_mdp.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.c('warning')};
                color: white;
                font-weight: bold;
                padding: 8px 12px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: #D97706;
            }}
        """)
        self._btn_reset_mdp.clicked.connect(self._reinitialiser_mot_de_passe)
        actions_row.addWidget(self._btn_reset_mdp)

        btn_actualiser = QPushButton("Actualiser")
        btn_actualiser.setCursor(Qt.PointingHandCursor)
        btn_actualiser.clicked.connect(self._charger_utilisateurs)
        actions_row.addWidget(btn_actualiser)

        right_layout.addLayout(actions_row)

        main_layout.addWidget(right, 1)
        layout.addWidget(main, 1)

    # === Chargement ===

    def _charger_utilisateurs(self):
        from modules.utilisateurs import Utilisateur

        utilisateurs = Utilisateur.obtenir_tous()

        lignes = []
        for u in utilisateurs:
            statut = "Actif" if u[6] else "Inactif"
            role_display = u[5] or ""
            # Si super-admin, ajouter badge
            if len(u) > 8 and u[8] == 1:  # super_admin column
                role_display = f"⭐ {role_display}"
            lignes.append([
                u[0],          # ID
                u[1] or "",     # Nom
                u[2] or "",     # Prenom
                u[3] or "",     # Email
                role_display,   # Role (avec badge si super-admin)
                statut,         # Statut
            ])

        self._table_model.charger_donnees(lignes)
        self._table_view.ajuster_colonnes()

    # === Selection ===

    def _selectionner_utilisateur(self, row: int):
        ligne = self._table_model.obtenir_ligne(row)
        if not ligne:
            self._user_selectionne_id = None
            # Re-enable all buttons if no user is selected
            self._btn_activer.setEnabled(True)
            self._btn_super_admin.setEnabled(True)
            self._btn_gestionnaire.setEnabled(True)
            self._btn_caissier.setEnabled(True)
            self._btn_reset_mdp.setEnabled(True)
            return
        self._user_selectionne_id = ligne[0]

        from modules.utilisateurs import Utilisateur
        is_super_admin = Utilisateur.est_super_admin(self._user_selectionne_id)

        # Disable buttons if the selected user is a super-admin
        self._btn_activer.setEnabled(not is_super_admin)
        self._btn_super_admin.setEnabled(not is_super_admin) # Cannot change role of super-admin
        self._btn_gestionnaire.setEnabled(not is_super_admin)
        self._btn_caissier.setEnabled(not is_super_admin)
        self._btn_reset_mdp.setEnabled(True) # Super-admin's password can be reset by another super-admin


    # === Actions ===

    def _creer_utilisateur(self):
        nom = self._entry_nom.text().strip()
        prenom = self._entry_prenom.text().strip()
        email = self._entry_email.text().strip()
        password = self._entry_password.text()
        role = self._combo_role.currentText()

        if not nom or not prenom or not email or not password:
            erreur(self, "Erreur", "Tous les champs marques * sont obligatoires.")
            return

        from modules.utilisateurs import Utilisateur
        succes, message = Utilisateur.creer_utilisateur(nom, prenom, email, password, role)

        if succes:
            information(self, "Succes", message)
            self._entry_nom.clear()
            self._entry_prenom.clear()
            self._entry_email.clear()
            self._entry_password.clear()
            self._combo_role.setCurrentIndex(0)
            self._charger_utilisateurs()
        else:
            erreur(self, "Erreur", message)

    def _toggle_statut(self):
        if not self._user_selectionne_id:
            erreur(self, "Erreur", "Selectionnez un utilisateur.")
            return

        # Empecher l'auto-desactivation
        connected_id = self._utilisateur_connecte.get('id')
        if self._user_selectionne_id == connected_id:
            erreur(self, "Erreur", "Vous ne pouvez pas desactiver votre propre compte.")
            return

        # Trouver le statut actuel
        row = self._table_view.ligne_courante()
        if row < 0:
            return
        ligne = self._table_model.obtenir_ligne(row)
        statut_actuel = ligne[5] if ligne else ""
        nouveau_statut = statut_actuel != "Actif"

        action = "activer" if nouveau_statut else "desactiver"
        if not confirmer(self, "Confirmation", f"Voulez-vous {action} cet utilisateur ?"):
            return

        from modules.utilisateurs import Utilisateur
        result = Utilisateur.changer_statut(self._user_selectionne_id, nouveau_statut)

        if result:
            information(self, "Succes", f"Utilisateur {'active' if nouveau_statut else 'desactive'}.")
            self._charger_utilisateurs()
        else:
            erreur(self, "Erreur", "Impossible de changer le statut.")

    def _changer_role(self, nouveau_role: str):
        if not self._user_selectionne_id:
            erreur(self, "Erreur", "Selectionnez un utilisateur.")
            return

        if not confirmer(self, "Confirmation",
                         f"Changer le role en '{nouveau_role}' ?"):
            return

        from modules.utilisateurs import Utilisateur
        result = Utilisateur.modifier_role(self._user_selectionne_id, nouveau_role)

        if result:
            information(self, "Succes", f"Role modifie en '{nouveau_role}'.")
            self._charger_utilisateurs()
        else:
            erreur(self, "Erreur", "Impossible de changer le role.")

    def _reinitialiser_mot_de_passe(self):
        """Réinitialiser le mot de passe d'un utilisateur (Admin seulement)"""
        if not self._user_selectionne_id:
            erreur(self, "Erreur", "Sélectionnez un utilisateur.")
            return

        # Vérifier que l'utilisateur connecté est un super-admin
        if self._utilisateur_connecte.get('super_admin') != 1:
            erreur(self, "Accès refusé", "Seul le Super-Admin peut réinitialiser les mots de passe.")
            return

        # Empêcher la réinitialisation de son propre mot de passe (utiliser changement normal)
        if self._user_selectionne_id == self._utilisateur_connecte.get('id'):
            erreur(self, "Erreur", "Utilisez la fonction 'Changer mot de passe' pour votre propre compte.")
            return

        # Récupérer infos utilisateur
        from modules.utilisateurs import Utilisateur
        user = Utilisateur.obtenir_par_id(self._user_selectionne_id)
        if not user:
            erreur(self, "Erreur", "Utilisateur introuvable.")
            return

        nom_complet = f"{user[2]} {user[1]}"  # prenom nom

        # Dialog de saisie nouveau mot de passe
        from PySide6.QtWidgets import QInputDialog
        nouveau_mdp, ok = QInputDialog.getText(
            self, "Réinitialiser mot de passe",
            f"Nouveau mot de passe pour {nom_complet} :\n(min. 8 caractères, 1 chiffre)",
            QLineEdit.Password
        )

        if not ok or not nouveau_mdp:
            return

        # Validation
        if len(nouveau_mdp) < 8:
            erreur(self, "Erreur", "Le mot de passe doit contenir au moins 8 caractères.")
            return

        if not any(c.isdigit() for c in nouveau_mdp):
            erreur(self, "Erreur", "Le mot de passe doit contenir au moins 1 chiffre.")
            return

        # Confirmation
        if not confirmer(self, "Confirmation",
                         f"Réinitialiser le mot de passe de {nom_complet} ?"):
            return

        # Modifier
        succes = Utilisateur.modifier_mot_de_passe(self._user_selectionne_id, nouveau_mdp)

        if succes:
            information(self, "Succès",
                        f"Mot de passe réinitialisé pour {nom_complet}.\n\n"
                        f"Communiquez-lui le nouveau mot de passe de manière sécurisée.")
            # Logger l'action
            Utilisateur.logger_action(
                self._utilisateur_connecte['id'],
                'reset_password',
                f"Réinitialisation MDP pour utilisateur ID {self._user_selectionne_id}"
            )
        else:
            erreur(self, "Erreur", "Impossible de réinitialiser le mot de passe.")
