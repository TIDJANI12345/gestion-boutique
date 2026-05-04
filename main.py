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


def initialiser_features():
    """Charge les features extras et initialise le démo si besoin."""
    try:
        from modules.features import charger_extras, est_demo, statut_expiration
        charger_extras()
        statut = statut_expiration()
        if statut == 'grace':
            from database import db
            expire = db.get_parametre('licence_expire', '')
            from modules.logger import get_logger
            get_logger('main').warning(f"Licence en grace period, expire le {expire}")
    except Exception:
        pass

    try:
        from modules.sauvegarde import sauvegarde_auto_si_necessaire
        sauvegarde_auto_si_necessaire()
    except Exception:
        pass


def verifier_licence() -> bool:
    """Verifie la licence. Affiche la fenetre d'activation si invalide."""
    from modules.licence import GestionLicence

    manager = GestionLicence()
    est_valide, message = manager.verifier_locale()

    if est_valide:
        initialiser_features()
        return True

    from ui.windows.licence import LicenceWindow
    dlg = LicenceWindow()
    result = dlg.exec() == QDialog.Accepted
    if result:
        initialiser_features()
    return result


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


def verifier_mises_a_jour_auto(fenetre_parent):
    """
    Vérifier automatiquement les mises à jour disponibles
    Appelé 3 secondes après l'ouverture du dashboard
    """
    from modules.updater import Updater
    from ui.dialogs.update_notification import UpdateNotificationDialog

    # Vérifier en arrière-plan (non bloquant)
    nouvelle_dispo, infos = Updater.verifier_mise_a_jour(APP_VERSION)

    if nouvelle_dispo and infos:
        # Vérifier si l'utilisateur a déjà ignoré cette version
        if not Updater.est_ignoree(infos.get('version', '')):
            # Afficher le dialog de notification
            dialog = UpdateNotificationDialog(infos, fenetre_parent)
            dialog.exec()


def verifier_config_initiale(fenetre):
    """Rappelle le patron de configurer la boutique si les paramètres essentiels manquent."""
    from database import db
    from PySide6.QtWidgets import QMessageBox
    from config import BOUTIQUE_NOM, BOUTIQUE_TELEPHONE

    nom = db.get_parametre('boutique_nom', '').strip()
    tel = db.get_parametre('boutique_telephone', '').strip()

    manquants = []
    # Valeur non modifiée = encore le placeholder de config.py
    if not nom or nom == BOUTIQUE_NOM:
        manquants.append("Nom de la boutique")
    if not tel or tel == BOUTIQUE_TELEPHONE:
        manquants.append("Téléphone de la boutique")

    if not manquants:
        return

    msg = QMessageBox(fenetre)
    msg.setWindowTitle("Configuration initiale requise")
    msg.setIcon(QMessageBox.Warning)
    msg.setText(
        "Certains paramètres essentiels ne sont pas encore configurés :\n\n"
        + "\n".join(f"  • {m}" for m in manquants)
        + "\n\nConfigurez-les maintenant pour que les reçus et calculs soient corrects."
    )
    btn_now = msg.addButton("Configurer maintenant", QMessageBox.AcceptRole)
    msg.addButton("Plus tard", QMessageBox.RejectRole)
    msg.exec()

    if msg.clickedButton() == btn_now and hasattr(fenetre, 'ouvrir_preferences_caisse'):
        fenetre.ouvrir_preferences_caisse()


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
        from ui.components.dialogs import erreur
        erreur(None, "Erreur de rôle", "Votre rôle n'est pas reconnu. Contactez l'administrateur.")
        app.quit()
        return

    def _fermer_tout():
        for w in app.topLevelWidgets():
            if w is not fenetre:
                w.close()
        fenetre.close()

    def on_session_expiree():
        _fermer_tout()
        nouveau_user = demander_login()
        if nouveau_user:
            lancer_dashboard(app, nouveau_user)
        else:
            app.quit()

    def on_deconnexion():
        _fermer_tout()
        nouveau_user = demander_login()
        if nouveau_user:
            lancer_dashboard(app, nouveau_user)
        else:
            app.quit()

    fenetre.session_expiree.connect(on_session_expiree)
    if hasattr(fenetre, 'deconnexion_demandee'):
        fenetre.deconnexion_demandee.connect(on_deconnexion)

    fenetre.showMaximized()

    # Rappel config initiale après 1 seconde (patron seulement)
    if utilisateur.get('super_admin') == 1:
        QTimer.singleShot(1000, lambda: verifier_config_initiale(fenetre))

    # Vérifier les mises à jour après 3 secondes (ne pas bloquer le démarrage)
    QTimer.singleShot(3000, lambda: verifier_mises_a_jour_auto(fenetre))


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
