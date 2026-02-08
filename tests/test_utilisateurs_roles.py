"""
Tests pour la hierarchie des roles et contraintes super-admin
"""
import pytest
from tests.conftest import reset_db
from database import db
from modules.utilisateurs import Utilisateur


@pytest.fixture(autouse=True)
def setup_db():
    """Reset DB avant chaque test"""
    reset_db()
    db.execute_query("DELETE FROM utilisateurs")
    yield


def test_creation_super_admin_unique():
    """Un seul super-admin possible"""
    # Creer premier patron (super-admin)
    success1, msg1 = Utilisateur.creer_utilisateur(
        "Dupont", "Jean", "patron@test.com", "Password123", "patron"
    )
    assert success1

    # Tenter creer 2e patron (doit echouer)
    success2, msg2 = Utilisateur.creer_utilisateur(
        "Martin", "Paul", "patron2@test.com", "Password456", "patron"
    )
    assert not success2
    assert "super-admin existe déjà" in msg2


def test_modification_role_super_admin_bloque():
    """Impossible de modifier le role du super-admin"""
    # Creer super-admin
    Utilisateur.creer_utilisateur(
        "Boss", "Le", "boss@test.com", "BossPass1", "patron"
    )

    # Recuperer l'ID
    user = db.fetch_one("SELECT id FROM utilisateurs WHERE email = ?", ("boss@test.com",))
    user_id = user['id']

    # Tenter modifier role (doit echouer)
    success, msg = Utilisateur.modifier_role(user_id, "gestionnaire")
    assert not success
    assert "Super-Admin" in msg


def test_creation_gestionnaire_ok():
    """Creation gestionnaire possible meme avec super-admin existant"""
    # Creer patron
    Utilisateur.creer_utilisateur("P", "P", "p@t.com", "Pass1234", "patron")

    # Creer gestionnaire (doit reussir)
    success, msg = Utilisateur.creer_utilisateur(
        "Gest", "G", "g@t.com", "Pass5678", "gestionnaire"
    )
    assert success


def test_est_super_admin():
    """Verification correcte du flag super_admin"""
    # Creer patron
    Utilisateur.creer_utilisateur("P", "P", "p@t.com", "Pass1234", "patron")
    user = db.fetch_one("SELECT id FROM utilisateurs WHERE email = ?", ("p@t.com",))
    user_id = user['id']

    # Verifier flag
    assert Utilisateur.est_super_admin(user_id)


def test_gestionnaire_not_super_admin():
    """Gestionnaire n'est pas super-admin"""
    Utilisateur.creer_utilisateur("G", "G", "g@t.com", "Pass1234", "gestionnaire")
    user = db.fetch_one("SELECT id FROM utilisateurs WHERE email = ?", ("g@t.com",))
    user_id = user['id']

    # Verifier PAS super-admin
    assert not Utilisateur.est_super_admin(user_id)


def test_promotion_vers_patron_impossible():
    """Impossible de promouvoir un utilisateur vers patron si super-admin existe"""
    # Creer patron
    Utilisateur.creer_utilisateur("P", "P", "p@t.com", "Pass1234", "patron")

    # Creer gestionnaire
    Utilisateur.creer_utilisateur("G", "G", "g@t.com", "Pass5678", "gestionnaire")
    user = db.fetch_one("SELECT id FROM utilisateurs WHERE email = ?", ("g@t.com",))
    user_id = user['id']

    # Tenter promouvoir vers patron (doit echouer)
    success, msg = Utilisateur.modifier_role(user_id, "patron")
    assert not success
    assert "super-admin existe déjà" in msg
