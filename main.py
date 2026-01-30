import tkinter as tk
from interface.splash_screen import SplashScreen
from interface.fenetre_principale import FenetrePrincipale
from interface.fenetre_licence import FenetreLicence
from modules.licence import GestionLicence
from database import db 

def lancer_dashboard():
    """Lance l'application principale"""
    app = FenetrePrincipale()
    app.lancer()

def main():
    # 0. Splash screen
    splash = SplashScreen(duree=3000)
    splash.afficher()
    
    # 1. Vérifier licence
    manager = GestionLicence()
    est_valide, message = manager.verifier_locale()
    
    if not est_valide:
        # Activation licence
        root = tk.Tk()
        root.withdraw()
        
        def apres_activation():
            root.destroy()
            # Après activation, demander login
            demander_login()
        
        fenetre = FenetreLicence(root, apres_activation)
        root.mainloop()
    else:
        # Licence OK, demander login
        demander_login()

def demander_login():
    """Demander connexion utilisateur"""
    from interface.fenetre_login import FenetreLogin
    
    def apres_login(utilisateur):
        # Router selon le rôle
        if utilisateur['role'] == 'caissier':
            # Dashboard caissier simplifié
            from interface.fenetre_principale_caissier import FenetrePrincipaleCaissier
            app = FenetrePrincipaleCaissier(utilisateur)
            app.lancer()
        else:
            # Dashboard patron complet
            from interface.fenetre_principale import FenetrePrincipale
            app = FenetrePrincipale(utilisateur)
            app.lancer()
    
    login = FenetreLogin(apres_login)
    login.afficher()

if __name__ == "__main__":
    main()