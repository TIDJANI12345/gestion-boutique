#!/usr/bin/env python3
"""
Script de test rapide pour la hiérarchie des rôles
"""
import sys

def test_imports():
    """Test des imports"""
    print("🧪 Test 1: Imports...")
    try:
        from modules.utilisateurs import Utilisateur, ROLES_DISPONIBLES
        from modules.permissions import Permissions
        from database import db
        print("  ✅ Imports OK")
        return True
    except Exception as e:
        print(f"  ❌ Erreur import: {e}")
        return False

def test_roles():
    """Test des rôles disponibles"""
    print("\n🧪 Test 2: Rôles disponibles...")
    from modules.utilisateurs import ROLES_DISPONIBLES

    expected_roles = {'patron', 'gestionnaire', 'caissier'}
    actual_roles = set(ROLES_DISPONIBLES.keys())

    if actual_roles == expected_roles:
        print(f"  ✅ Rôles: {', '.join(actual_roles)}")
        return True
    else:
        print(f"  ❌ Rôles incorrects: {actual_roles}")
        return False

def test_permissions():
    """Test du système de permissions"""
    print("\n🧪 Test 3: Système de permissions...")
    from modules.permissions import Permissions

    # Mock utilisateur super-admin
    patron = {'id': 1, 'role': 'patron', 'super_admin': 1}
    gestionnaire = {'id': 2, 'role': 'gestionnaire', 'super_admin': 0}
    caissier = {'id': 3, 'role': 'caissier', 'super_admin': 0}

    tests = [
        (patron, 'gerer_utilisateurs', True, "Patron peut gérer utilisateurs"),
        (gestionnaire, 'gerer_produits', True, "Gestionnaire peut gérer produits"),
        (gestionnaire, 'gerer_utilisateurs', False, "Gestionnaire NE peut PAS gérer utilisateurs"),
        (caissier, 'effectuer_ventes', True, "Caissier peut vendre"),
        (caissier, 'gerer_produits', False, "Caissier NE peut PAS gérer produits"),
    ]

    all_ok = True
    for user, perm, expected, desc in tests:
        result = Permissions.peut(user, perm)
        if result == expected:
            print(f"  ✅ {desc}")
        else:
            print(f"  ❌ {desc} (attendu: {expected}, reçu: {result})")
            all_ok = False

    return all_ok

def test_database():
    """Test structure base de données"""
    print("\n🧪 Test 4: Structure base de données...")
    from database import db

    # Vérifier colonne super_admin existe
    try:
        result = db.fetch_one("SELECT super_admin FROM utilisateurs LIMIT 1")
        print("  ✅ Colonne super_admin existe")

        # Vérifier paramètre gestionnaire_peut_vendre
        param = db.get_parametre('gestionnaire_peut_vendre', None)
        if param:
            print(f"  ✅ Paramètre gestionnaire_peut_vendre = {param}")
        else:
            print("  ⚠️  Paramètre gestionnaire_peut_vendre absent")

        return True
    except Exception as e:
        print(f"  ❌ Erreur DB: {e}")
        return False

def test_super_admin():
    """Test vérification super-admin"""
    print("\n🧪 Test 5: Détection super-admin...")
    from modules.utilisateurs import Utilisateur
    from database import db

    try:
        # Compter super-admins
        count = db.fetch_one("SELECT COUNT(*) FROM utilisateurs WHERE super_admin = 1")
        if count and count[0] > 0:
            print(f"  ✅ {count[0]} super-admin(s) trouvé(s)")

            # Vérifier la méthode est_super_admin
            super_user = db.fetch_one("SELECT id FROM utilisateurs WHERE super_admin = 1 LIMIT 1")
            if super_user:
                is_super = Utilisateur.est_super_admin(super_user[0])
                if is_super:
                    print(f"  ✅ est_super_admin() fonctionne")
                else:
                    print(f"  ❌ est_super_admin() ne détecte pas le super-admin")
                    return False
            return True
        else:
            print("  ⚠️  Aucun super-admin dans la base (normal si DB vide)")
            return True
    except Exception as e:
        print(f"  ❌ Erreur: {e}")
        return False

def main():
    """Lancer tous les tests"""
    print("=" * 60)
    print("TEST HIÉRARCHIE DES RÔLES")
    print("=" * 60)

    tests = [
        test_imports,
        test_roles,
        test_permissions,
        test_database,
        test_super_admin,
    ]

    results = []
    for test_func in tests:
        try:
            results.append(test_func())
        except Exception as e:
            print(f"\n❌ Test {test_func.__name__} a planté: {e}")
            results.append(False)

    print("\n" + "=" * 60)
    print(f"RÉSULTAT: {sum(results)}/{len(results)} tests réussis")
    print("=" * 60)

    if all(results):
        print("✅ TOUS LES TESTS PASSENT - Prêt à commit !")
        return 0
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ - Vérifier les erreurs")
        return 1

if __name__ == "__main__":
    sys.exit(main())
