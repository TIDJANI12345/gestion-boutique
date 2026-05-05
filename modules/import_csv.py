"""
Import CSV de produits en lot.
"""
import csv
import io
from dataclasses import dataclass, field
from modules.logger import get_logger

logger = get_logger('import_csv')

# Colonnes CSV : (nom_colonne, requis, type, valeur_defaut)
COLONNES = [
    ('nom',           True,  str,   ''),
    ('categorie',     True,  str,   ''),
    ('prix_achat',    True,  float, 0.0),
    ('prix_vente',    True,  float, 0.0),
    ('stock_actuel',  False, int,   0),
    ('stock_alerte',  False, int,   5),
    ('code_barre',    False, str,   ''),
    ('description',   False, str,   ''),
    ('prix_gros',     False, float, 0.0),
    ('seuil_gros',    False, int,   0),
    ('unite_mesure',  False, str,   'pièce'),
]

ENTETES_REQUIS = {c[0] for c in COLONNES if c[1]}
ENTETES_TOUS   = [c[0] for c in COLONNES]


def modele_csv() -> str:
    """Retourne une chaîne CSV contenant l'en-tête + une ligne d'exemple."""
    lignes = [
        ENTETES_TOUS,
        ['Coca Cola 33cl', 'Boissons', '400', '600', '50', '10',
         '', 'Canette réfrigérée', '550', '12', 'pièce'],
    ]
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=';')
    w.writerows(lignes)
    return buf.getvalue()


@dataclass
class LigneImport:
    numero: int
    donnees: dict
    erreurs: list[str] = field(default_factory=list)

    @property
    def valide(self) -> bool:
        return len(self.erreurs) == 0


def _coerce(valeur: str, typ, defaut):
    """Convertit une valeur CSV vers le type attendu."""
    v = valeur.strip()
    if not v:
        return defaut
    try:
        return typ(v.replace(',', '.') if typ == float else v)
    except (ValueError, TypeError):
        return None  # signale une erreur de conversion


def analyser_csv(contenu: str) -> tuple[list[LigneImport], list[str]]:
    """
    Parse le contenu CSV et valide chaque ligne.
    Returns: (lignes, erreurs_globales)
    """
    erreurs_globales = []

    # Détecter le séparateur (;  ou ,)
    separateur = ';' if contenu.count(';') >= contenu.count(',') else ','

    try:
        reader = csv.DictReader(io.StringIO(contenu), delimiter=separateur)
        entetes = reader.fieldnames or []
    except Exception as e:
        return [], [f"Fichier illisible : {e}"]

    # Vérifier colonnes obligatoires
    entetes_lower = [h.strip().lower() for h in entetes]
    manquantes = ENTETES_REQUIS - set(entetes_lower)
    if manquantes:
        erreurs_globales.append(f"Colonnes obligatoires manquantes : {', '.join(sorted(manquantes))}")
        return [], erreurs_globales

    # Mapper les entêtes insensibles à la casse
    mapping = {h.strip().lower(): h for h in entetes}

    lignes: list[LigneImport] = []
    for i, row in enumerate(reader, start=2):  # ligne 1 = en-tête
        donnees = {}
        erreurs = []

        for col, requis, typ, defaut in COLONNES:
            header_original = mapping.get(col)
            valeur_brute = row.get(header_original, '').strip() if header_original else ''

            if requis and not valeur_brute:
                erreurs.append(f"'{col}' obligatoire")
                donnees[col] = defaut
                continue

            coerced = _coerce(valeur_brute, typ, defaut)
            if coerced is None:
                erreurs.append(f"'{col}' invalide : '{valeur_brute}'")
                donnees[col] = defaut
            else:
                donnees[col] = coerced

        # Validations métier
        if donnees.get('prix_vente', 0) < 0:
            erreurs.append("prix_vente négatif")
        if donnees.get('prix_achat', 0) < 0:
            erreurs.append("prix_achat négatif")
        if donnees.get('stock_actuel', 0) < 0:
            erreurs.append("stock_actuel négatif")

        lignes.append(LigneImport(numero=i, donnees=donnees, erreurs=erreurs))

    return lignes, erreurs_globales


def importer_lignes(lignes: list[LigneImport]) -> tuple[int, int, list[str]]:
    """
    Insère en DB les lignes valides.
    Returns: (nb_ok, nb_erreurs, messages_erreur)
    """
    from modules.produits import Produit

    nb_ok = 0
    nb_err = 0
    msgs = []

    for ligne in lignes:
        if not ligne.valide:
            nb_err += 1
            msgs.append(f"Ligne {ligne.numero} ignorée : {'; '.join(ligne.erreurs)}")
            continue

        d = ligne.donnees
        result = Produit.ajouter(
            nom=d['nom'],
            categorie=d['categorie'],
            prix_achat=d['prix_achat'],
            prix_vente=d['prix_vente'],
            stock_actuel=d['stock_actuel'],
            stock_alerte=d['stock_alerte'],
            code_barre=d['code_barre'] or None,
            description=d['description'],
            prix_gros=d['prix_gros'],
            seuil_gros=d['seuil_gros'],
            unite_mesure=d['unite_mesure'] or 'pièce',
        )
        if result:
            nb_ok += 1
            logger.info(f"Importé : {d['nom']}")
        else:
            nb_err += 1
            msgs.append(f"Ligne {ligne.numero} : insertion échouée pour '{d['nom']}'")

    return nb_ok, nb_err, msgs
