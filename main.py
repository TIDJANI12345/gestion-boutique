import tkinter as tk
from interface.splash_screen import SplashScreen
from interface.fenetre_principale import FenetrePrincipale
from interface.fenetre_licence import FenetreLicence
from modules.licence import GestionLicence
from database import db

def main():
    # 0. Splash screen
    splash = SplashScreen(duree=3000)
    splash.afficher()

    # 1. Verifier licence
    manager = GestionLicence()
    est_valide, message = manager.verifier_locale()

    if not est_valide:
        # Activation licence
        root = tk.Tk()
        root.withdraw()

        def apres_activation():
            root.destroy()
            verifier_premier_lancement()

        fenetre = FenetreLicence(root, apres_activation)
        root.mainloop()
    else:
        # Licence OK
        verifier_premier_lancement()

def verifier_premier_lancement():
    """Verifier si c'est le premier lancement (aucun utilisateur)"""
    from modules.utilisateurs import Utilisateur

    if not Utilisateur.compte_existe():
        # Premier lancement : creer le compte admin
        from interface.fenetre_premier_lancement import FenetrePremierLancement
        premier = FenetrePremierLancement(callback_success=demander_login)
        premier.afficher()
    else:
        demander_login()

def demander_login():
    """Demander connexion utilisateur"""
    from interface.fenetre_login import FenetreLogin

    def apres_login(utilisateur):
        # Router selon le role
        if utilisateur['role'] == 'caissier':
            from interface.fenetre_principale_caissier import FenetrePrincipaleCaissier
            app = FenetrePrincipaleCaissier(utilisateur)
            app.lancer()
        else:
            from interface.fenetre_principale import FenetrePrincipale
            app = FenetrePrincipale(utilisateur)
            app.lancer()

    login = FenetreLogin(apres_login)
    login.afficher()

if __name__ == "__main__":
    main()
