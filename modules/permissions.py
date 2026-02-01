"""
Module de gestion des permissions et controles d'acces
"""
from database import db
from modules.logger import get_logger

logger = get_logger('permissions')

class Permissions:
    PERMISSIONS = {
        'patron': [
            'gerer_utilisateurs',
            'voir_toutes_ventes',
            'gerer_produits',
            'gerer_stocks',
            'gerer_clients',
            'effectuer_ventes',
            'parametres_systeme',
            'rapports_globaux',
            'sauvegarde_restore',
        ],
        'gestionnaire': [
            'gerer_produits',
            'gerer_stocks',
            'gerer_clients',
            'voir_mes_ventes',
            'effectuer_ventes',  # Optionnel selon config
        ],
        'caissier': [
            'effectuer_ventes',
            'voir_mes_ventes',
        ]
    }

    @staticmethod
    def peut(utilisateur, permission):
        """Vérifier si un utilisateur a une permission"""
        if not utilisateur:
            return False

        role = utilisateur.get('role')
        user_permissions = Permissions.PERMISSIONS.get(role, []).copy()

        # Ajouter permission vente pour gestionnaire si configuré
        if role == 'gestionnaire' and permission == 'effectuer_ventes':
            if db.get_parametre('gestionnaire_peut_vendre', '1') == '1':
                return True # Gestionnaire peut vendre si le paramètre est activé

        # Vérifier si l'utilisateur est un super-admin et a toutes les permissions
        # Note: L'attribut 'super_admin' est un flag boolean dans la BDD,
        # il devrait etre recupere dans l'objet utilisateur apres login
        if utilisateur.get('super_admin') == 1:
            return True # Super-admin a toutes les permissions

        return permission in user_permissions