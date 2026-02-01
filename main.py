"""
Point d'entree PySide6 - GestionBoutique v2
Flux : Splash → Licence → Premier lancement → Login → Dashboard
"""
import sys
import os

# Ajouter le dossier racine au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication, QDialog
from PySide6.QtCore import QTimer

from ui.theme import Theme
from ui.platform import fix_encoding, ensure_directories, get_base_dir
from config import APP_NAME, APP_VERSION


def verifier_licence() -> bool:
    """Verifie la licence. Affiche la fenetre d'activation si invalide."""
    from modules.licence import GestionLicence

    manager = GestionLicence()
    est_valide, message = manager.verifier_locale()

    if est_valide:
        return True

    from ui.windows.licence import LicenceWindow
    dlg = LicenceWindow()
    return dlg.exec() == QDialog.Accepted


def verifier_premier_lancement() -> bool:
    """Verifie si un compte existe. Cree le premier compte si necessaire."""
    from modules.utilisateurs import Utilisateur

    if Utilisateur.compte_existe():
        return True

    from ui.windows.premier_lancement import PremierLancementWindow
    dlg = PremierLancementWindow()
    return dlg.exec() == QDialog.Accepted


def demander_login() -> dict | None:
    """Affiche la fenetre de login. Retourne les infos user ou None."""
    from ui.windows.login import LoginWindow

    user_info = None
    dlg = LoginWindow()

    def on_success(infos: dict):
        nonlocal user_info
        user_info = infos

    dlg.login_success.connect(on_success)
    if dlg.exec() == QDialog.Accepted:
        return user_info
    return None


def lancer_dashboard(app: QApplication, utilisateur: dict):
    """Lance le dashboard selon le role et gere la session."""

    from modules.utilisateurs import ROLES_DISPONIBLES # Import here to avoid circular dependency

    # Determine which window to launch based on role
    if utilisateur.get('super_admin') == 1:
        from ui.windows.principale import PrincipaleWindow
        fenetre = PrincipaleWindow(utilisateur)
    elif utilisateur['role'] == 'gestionnaire':
        from ui.windows.principale_gestionnaire import PrincipaleGestionnaireWindow
        fenetre = PrincipaleGestionnaireWindow(utilisateur)
    elif utilisateur['role'] == 'caissier':
        from ui.windows.principale_caissier import PrincipaleCaissierWindow
        fenetre = PrincipaleCaissierWindow(utilisateur)
    else:
        from ui.windows.dialogs import erreur
        erreur(None, "Erreur de rôle", "Votre rôle n'est pas reconnu. Contactez l'administrateur.")
        app.quit()
        return

    def on_session_expiree():
        fenetre.close()
        # Re-login apres expiration
        nouveau_user = demander_login()
        if nouveau_user:
            lancer_dashboard(app, nouveau_user)
        else:
            app.quit()

    def on_deconnexion():
        fenetre.close()
        nouveau_user = demander_login()
        if nouveau_user:
            lancer_dashboard(app, nouveau_user)
        else:
            app.quit()

    fenetre.session_expiree.connect(on_session_expiree)
    if hasattr(fenetre, 'deconnexion_demandee'):
        fenetre.deconnexion_demandee.connect(on_deconnexion)

    fenetre.show()


def main():
    # Corrections specifiques a l'OS
    fix_encoding()

    # Creer les dossiers necessaires
    ensure_directories(get_base_dir())

    # Application Qt
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName("GestionBoutique")

    # Appliquer le theme
    Theme.appliquer(app)

    # 0. Splash screen
    from ui.windows.splash import SplashScreen
    splash = SplashScreen(duree=2500)
    splash.show()
    app.processEvents()

    # Attendre la fin du splash avant de continuer
    import time
    debut = time.time()
    while time.time() - debut < 2.5:
        app.processEvents()
        time.sleep(0.05)
    splash.close()

    # 1. Verifier licence
    if not verifier_licence():
        sys.exit(0)

    # 2. Verifier premier lancement
    if not verifier_premier_lancement():
        sys.exit(0)

    # 3. Login
    utilisateur = demander_login()
    if not utilisateur:
        sys.exit(0)

    # 4. Dashboard avec routage par role
    lancer_dashboard(app, utilisateur)

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
