"""
Système de feature flags — contrôle des fonctionnalités par plan de licence.
Source de vérité unique : toute l'UI vérifie features.peut() avant d'agir.
"""
import hashlib
import base64
from datetime import date
from database import db
from modules.logger import get_logger

logger = get_logger('features')

# ---------------------------------------------------------------------------
# Définition des plans
# ---------------------------------------------------------------------------

PLANS: dict[str, list[str]] = {
    'demo': [
        # Standard
        'ventes', 'stock', 'recus_pdf', 'impression_thermique',
        'rapports_base', 'prix_gros', 'remises', 'scanner_camera',
        'parametres',
        # Les features Pro sont DÉSACTIVÉES en démo
        # (le démo = Standard + watermark + limites)
    ],
    'standard': [
        'ventes', 'stock', 'recus_pdf', 'impression_thermique',
        'rapports_base', 'prix_gros', 'remises', 'scanner_camera',
        'parametres',
    ],
    'pro': [
        'ventes', 'stock', 'recus_pdf', 'impression_thermique',
        'rapports_base', 'prix_gros', 'remises', 'scanner_camera',
        'parametres',
        # Pro uniquement
        'multi_caissiers', 'clients_fidelite', 'exports',
        'scanner_mobile', 'rapports_avances', 'sauvegarde_auto',
        'fiscalite_tva',
    ],
    'white_label': [
        # Tout Pro + white label
        'ventes', 'stock', 'recus_pdf', 'impression_thermique',
        'rapports_base', 'prix_gros', 'remises', 'scanner_camera',
        'parametres',
        'multi_caissiers', 'clients_fidelite', 'exports',
        'scanner_mobile', 'rapports_avances', 'sauvegarde_auto',
        'fiscalite_tva',
        'white_label',
    ],
}

# Limites numériques par plan
LIMITES: dict[str, dict] = {
    'demo':        {'caissiers': 1},
    'standard':    {'caissiers': 1},
    'pro':         {'caissiers': 999},
    'white_label': {'caissiers': 999},
}

# ---------------------------------------------------------------------------
# Features supplémentaires (clients sur mesure) — chargées au démarrage
# ---------------------------------------------------------------------------

_extra_features: set[str] = set()


def charger_extras():
    """Déchiffre et charge les features personnalisées depuis la DB."""
    global _extra_features
    try:
        extras_enc = db.get_parametre('licence_features_enc', '')
        if not extras_enc or extras_enc == '__none__':
            _extra_features = set()
            return

        plan_txt = _dechiffrer_plan(extras_enc)
        _extra_features = {f.strip() for f in plan_txt.split(',') if f.strip()}
        logger.info(f"Features extra chargées : {_extra_features}")
    except Exception as e:
        logger.warning(f"Impossible de charger les features extra : {e}")
        _extra_features = set()


# ---------------------------------------------------------------------------
# Chiffrement PBKDF2 + Fernet
# ---------------------------------------------------------------------------

_SEL = b'hishipos_salt_v1'
_ITERATIONS = 100_000


def _deriver_cle(key_hash: str) -> bytes:
    """Dérive une clé Fernet 32 bytes depuis le hash de la clé de licence."""
    dk = hashlib.pbkdf2_hmac('sha256', key_hash.encode(), _SEL, _ITERATIONS)
    return base64.urlsafe_b64encode(dk)


def chiffrer_plan(texte: str) -> str:
    """Chiffre un texte avec la clé dérivée de la licence."""
    try:
        from cryptography.fernet import Fernet
        key_hash = db.get_parametre('licence_key_hash', '')
        if not key_hash:
            return texte  # Fallback si pas de hash (démo)
        f = Fernet(_deriver_cle(key_hash))
        return f.encrypt(texte.encode()).decode()
    except Exception as e:
        logger.error(f"Erreur chiffrement plan : {e}")
        return texte


def _dechiffrer_plan(chiffre: str) -> str:
    """Déchiffre un plan stocké en DB."""
    try:
        from cryptography.fernet import Fernet
        key_hash = db.get_parametre('licence_key_hash', '')
        if not key_hash:
            return chiffre
        f = Fernet(_deriver_cle(key_hash))
        return f.decrypt(chiffre.encode()).decode()
    except Exception as e:
        logger.warning(f"Erreur déchiffrement plan : {e}")
        return 'standard'  # Fallback sécurisé


# ---------------------------------------------------------------------------
# API publique
# ---------------------------------------------------------------------------

def plan_actuel() -> str:
    """Retourne le plan actif : 'demo', 'standard', 'pro', 'white_label'."""
    plan_enc = db.get_parametre('licence_plan_enc', '')
    if not plan_enc or plan_enc == '__demo__':
        return 'demo'
    try:
        plan = _dechiffrer_plan(plan_enc)
        if plan in PLANS:
            return plan
        return 'standard'
    except Exception:
        return 'standard'


def peut(feature: str) -> bool:
    """Retourne True si la feature est disponible pour le plan actif."""
    plan = plan_actuel()
    if feature in PLANS.get(plan, []):
        return True
    return feature in _extra_features


def limite_caissiers() -> int:
    """Nombre maximum de caissiers autorisés selon le plan."""
    plan = plan_actuel()
    return LIMITES.get(plan, LIMITES['standard'])['caissiers']


def est_demo() -> bool:
    return plan_actuel() == 'demo'


# ---------------------------------------------------------------------------
# Grace period & statut expiration
# ---------------------------------------------------------------------------

def statut_expiration() -> str:
    """
    Retourne :
      'ok'     — licence valide
      'grace'  — expirée depuis 1–7 jours (bandeau avertissement)
      'expire' — expirée depuis 8+ jours (ventes bloquées)
      'demo'   — mode démo, pas de date d'expiration
    """
    if est_demo():
        return 'demo'

    expire_str = db.get_parametre('licence_expire', '')
    if not expire_str:
        return 'ok'

    try:
        expire = date.fromisoformat(expire_str[:10])
        jours = (date.today() - expire).days
        if jours <= 0:
            return 'ok'
        if jours <= 7:
            return 'grace'
        return 'expire'
    except Exception:
        return 'ok'


def ventes_autorisees() -> bool:
    """Retourne False uniquement si licence expirée depuis 8+ jours."""
    statut = statut_expiration()
    return statut in ('ok', 'grace', 'demo')


# ---------------------------------------------------------------------------
# Démo : compteur de ventes et durée
# ---------------------------------------------------------------------------

DEMO_MAX_VENTES = 50
DEMO_MAX_JOURS = 14


def demo_peut_vendre() -> tuple[bool, str]:
    """
    Retourne (True, '') si le démo peut encore enregistrer des ventes,
    sinon (False, raison).
    """
    if not est_demo():
        return True, ''

    # Vérifier la durée (14 jours depuis premier lancement)
    import time
    debut = db.get_parametre('licence_demo_debut', '')
    if not debut:
        # Premier lancement démo → enregistrer la date
        db.set_parametre('licence_demo_debut', str(int(time.time())))
    else:
        try:
            jours = (time.time() - float(debut)) / 86400
            if jours > DEMO_MAX_JOURS:
                return False, f"La période de démonstration de {DEMO_MAX_JOURS} jours est terminée."
        except Exception:
            pass

    # Vérifier le nombre de ventes
    try:
        nb = int(db.get_parametre('licence_demo_ventes', '0'))
        if nb >= DEMO_MAX_VENTES:
            return False, f"Limite de {DEMO_MAX_VENTES} ventes en démonstration atteinte."
    except Exception:
        pass

    return True, ''


def demo_incrementer_ventes():
    """Incrémente le compteur de ventes en mode démo."""
    if not est_demo():
        return
    try:
        nb = int(db.get_parametre('licence_demo_ventes', '0'))
        db.set_parametre('licence_demo_ventes', str(nb + 1))
    except Exception:
        pass


def demo_infos() -> dict:
    """Retourne les infos démo pour affichage dans l'UI."""
    import time
    nb = int(db.get_parametre('licence_demo_ventes', '0'))
    debut_ts = db.get_parametre('licence_demo_debut', '')
    jours_restants = DEMO_MAX_JOURS
    if debut_ts:
        try:
            jours_ecoules = (time.time() - float(debut_ts)) / 86400
            jours_restants = max(0, int(DEMO_MAX_JOURS - jours_ecoules))
        except Exception:
            pass
    return {
        'ventes_utilisees': nb,
        'ventes_max': DEMO_MAX_VENTES,
        'jours_restants': jours_restants,
    }
