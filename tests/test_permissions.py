"""
Tests pour le systeme de permissions et hierarchie des roles
"""
import pytest
from modules.permissions import Permissions


def test_super_admin_all_permissions():
    """Super-admin a toutes les permissions"""
    user = {'super_admin': 1, 'role': 'patron'}
    assert Permissions.peut(user, 'gerer_utilisateurs')
    assert Permissions.peut(user, 'gerer_produits')
    assert Permissions.peut(user, 'effectuer_ventes')
    assert Permissions.peut(user, 'sauvegarde_restore')
    assert Permissions.peut(user, 'any_permission_imaginable')


def test_gestionnaire_no_users_access():
    """Gestionnaire ne peut pas gerer les utilisateurs"""
    user = {'super_admin': 0, 'role': 'gestionnaire'}
    assert not Permissions.peut(user, 'gerer_utilisateurs')
    assert Permissions.peut(user, 'gerer_produits')
    assert Permissions.peut(user, 'effectuer_ventes')
    assert not Permissions.peut(user, 'sauvegarde_restore')


def test_caissier_only_sales():
    """Caissier seulement ventes"""
    user = {'super_admin': 0, 'role': 'caissier'}
    assert Permissions.peut(user, 'effectuer_ventes')
    assert not Permissions.peut(user, 'gerer_produits')
    assert not Permissions.peut(user, 'gerer_utilisateurs')
    assert not Permissions.peut(user, 'sauvegarde_restore')


def test_patron_without_super_admin_flag():
    """Patron sans flag super_admin a les permissions du role patron uniquement"""
    user = {'super_admin': 0, 'role': 'patron'}
    # Devrait avoir les permissions du patron définies dans ROLES_PERMISSIONS
    assert Permissions.peut(user, 'gerer_utilisateurs')
    assert Permissions.peut(user, 'gerer_produits')
    assert Permissions.peut(user, 'effectuer_ventes')
    assert Permissions.peut(user, 'sauvegarde_restore')


def test_unknown_role():
    """Role inconnu n'a aucune permission"""
    user = {'super_admin': 0, 'role': 'inconnu'}
    assert not Permissions.peut(user, 'gerer_utilisateurs')
    assert not Permissions.peut(user, 'gerer_produits')
    assert not Permissions.peut(user, 'effectuer_ventes')


def test_missing_super_admin_key():
    """Si super_admin n'existe pas, traiter comme 0"""
    user = {'role': 'gestionnaire'}
    # Ne devrait pas crasher, super_admin devrait etre traite comme 0
    assert not Permissions.peut(user, 'gerer_utilisateurs')
    assert Permissions.peut(user, 'gerer_produits')
