"""
Tests d'integration pour le flux complet de ventes
"""
import pytest
from tests.conftest import reset_db
from database import db
from modules.produits import Produit
from modules.ventes import Vente


@pytest.fixture(autouse=True)
def setup_db():
    """Reset DB avant chaque test"""
    reset_db()
    db.execute_query("DELETE FROM details_ventes")
    db.execute_query("DELETE FROM ventes")
    db.execute_query("DELETE FROM historique_stock")
    db.execute_query("DELETE FROM produits")
    yield


def test_flux_vente_complet():
    """Test flux complet: Ajout produit → Vente → Verification stock"""
    # 1. Creer produit
    code = Produit.ajouter("Savon Lux", "Hygiene", 200, 350, 50, 10)
    produit = Produit.obtenir_par_code_barre(code)
    assert produit is not None
    produit_id = produit['id']

    # 2. Verifier stock initial
    assert produit['stock_actuel'] == 50

    # 3. Creer vente
    vente_id = Vente.creer_vente("Client Test Integration")
    assert vente_id is not None

    # 4. Ajouter produit au panier (5 unites)
    result = Vente.ajouter_produit(vente_id, produit_id, 5)
    assert result is True

    # 5. Verifier stock mis a jour
    produit_apres = Produit.obtenir_par_id(produit_id)
    assert produit_apres['stock_actuel'] == 45  # 50 - 5

    # 6. Verifier total vente
    total = Vente.calculer_total(vente_id)
    assert total == 1750  # 5 x 350

    # 7. Verifier details vente
    details = Vente.obtenir_details_vente(vente_id)
    assert len(details) == 1
    assert details[0]['quantite'] == 5
    assert details[0]['prix_unitaire'] == 350


def test_flux_vente_multi_produits():
    """Test vente avec plusieurs produits"""
    # Creer 3 produits
    code1 = Produit.ajouter("Savon", "Hygiene", 200, 350, 30, 5)
    code2 = Produit.ajouter("Dentifrice", "Hygiene", 500, 800, 40, 5)
    code3 = Produit.ajouter("Shampoing", "Hygiene", 1000, 1500, 25, 5)

    produit1 = Produit.obtenir_par_code_barre(code1)
    produit2 = Produit.obtenir_par_code_barre(code2)
    produit3 = Produit.obtenir_par_code_barre(code3)

    # Creer vente
    vente_id = Vente.creer_vente()

    # Ajouter les 3 produits
    Vente.ajouter_produit(vente_id, produit1['id'], 2)
    Vente.ajouter_produit(vente_id, produit2['id'], 3)
    Vente.ajouter_produit(vente_id, produit3['id'], 1)

    # Verifier total
    total = Vente.calculer_total(vente_id)
    expected = (2 * 350) + (3 * 800) + (1 * 1500)  # 700 + 2400 + 1500 = 4600
    assert total == expected

    # Verifier stocks
    assert Produit.obtenir_par_id(produit1['id'])['stock_actuel'] == 28
    assert Produit.obtenir_par_id(produit2['id'])['stock_actuel'] == 37
    assert Produit.obtenir_par_id(produit3['id'])['stock_actuel'] == 24


def test_flux_annulation_complete():
    """Test annulation vente complete restaure tout"""
    # Creer produit
    code = Produit.ajouter("Produit Test", "Test", 100, 200, 100, 5)
    produit = Produit.obtenir_par_code_barre(code)
    produit_id = produit['id']

    # Vente
    vente_id = Vente.creer_vente()
    Vente.ajouter_produit(vente_id, produit_id, 20)

    # Verifier stock reduit
    assert Produit.obtenir_par_id(produit_id)['stock_actuel'] == 80

    # Annuler vente
    Vente.annuler_vente(vente_id)

    # Verifier stock restaure
    assert Produit.obtenir_par_id(produit_id)['stock_actuel'] == 100

    # Verifier vente supprimee
    assert Vente.obtenir_vente(vente_id) is None


def test_protection_stock_negatif():
    """Protection contre stock negatif"""
    code = Produit.ajouter("Produit Limite", "Test", 100, 200, 5, 2)
    produit = Produit.obtenir_par_code_barre(code)
    produit_id = produit['id']

    vente_id = Vente.creer_vente()

    # Tenter ajouter plus que le stock
    result = Vente.ajouter_produit(vente_id, produit_id, 10)
    assert result is False

    # Verifier stock inchange
    assert Produit.obtenir_par_id(produit_id)['stock_actuel'] == 5


def test_suppression_ligne_vente():
    """Test suppression d'une ligne de vente"""
    code = Produit.ajouter("Produit", "Test", 100, 200, 50, 5)
    produit = Produit.obtenir_par_code_barre(code)
    produit_id = produit['id']

    vente_id = Vente.creer_vente()
    Vente.ajouter_produit(vente_id, produit_id, 10)

    # Stock reduit
    assert Produit.obtenir_par_id(produit_id)['stock_actuel'] == 40

    # Supprimer ligne
    details = Vente.obtenir_details_vente(vente_id)
    Vente.supprimer_ligne_vente(details[0]['id'], vente_id)

    # Stock restaure
    assert Produit.obtenir_par_id(produit_id)['stock_actuel'] == 50

    # Total vente = 0
    total = Vente.calculer_total(vente_id)
    assert total == 0
