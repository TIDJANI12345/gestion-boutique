# Plan — Système de Feature Flags & Licences par Plan
> Révisé après audit — corrections sécurité + grace period + white label

---

## Pourquoi ce système

Aujourd'hui le code source est unique. Demain tu as 20 clients : certains ont payé
l'offre Standard, d'autres le Pro, certains ont demandé une personnalisation.
Sans feature flags, tu as deux options, toutes mauvaises :

- **Tout donner à tout le monde** → tu perds l'argument de vente du Pro
- **Maintenir plusieurs versions** → cauchemar de maintenance, bugs dupliqués

Avec les feature flags, **un seul exécutable**, et c'est le plan de licence qui
détermine ce que chaque installation peut faire.

---

## Architecture

```
Serveur de licence (PythonAnywhere)
    └── retourne { plan, expire, features_extra, licence_key }
            │
            ▼
    modules/licence.py  ← stocke plan chiffré + date expiration + grace period
            │
            ▼
    modules/features.py ← source de vérité : peut(), plan_actuel(), limite_caissiers()
            │
            ▼
    UI : vérifie features.peut("nom_feature") avant chaque action sensible
```

Le plan est stocké localement en DB **chiffré** (pas en clair).
La vérification réseau n'est faite qu'au démarrage.
Offline → le plan local fait foi jusqu'à expiration + grace period.

---

## Les plans

### Standard — 40 000 F (perpétuel)

| Feature key | Description |
|---|---|
| `ventes` | Fenêtre de vente, panier, paiement |
| `stock` | Gestion des produits et du stock |
| `recus_pdf` | Génération et impression reçus PDF (IFU/RCCM inclus) |
| `impression_thermique` | Ticket ESC/POS 80mm |
| `rapports_base` | Rapport du jour, du mois, top produits |
| `prix_gros` | Prix dégressif par quantité |
| `remises` | Remises sur panier (% ou montant) |
| `scanner_camera` | Scan par webcam intégrée |
| `parametres` | Paramètres caisse + boutique (logo, IFU, cachets) |
| `import_csv` | Import produits en masse par fichier CSV |
| `fournisseurs` | Gestion des fournisseurs et contacts |

Limite : **1 compte caissier** (le patron + 1 caissier max). **1 terminal**.

### Pro — 85 000 F (perpétuel)

Tout Standard, plus :

| Feature key | Description |
|---|---|
| `multi_caissiers` | Comptes gestionnaire + caissier illimités |
| `reseau_local` | Multi-terminaux réseau local (jusqu'à 3 PCs) |
| `session_caisse` | Timeout de session configurable par rôle |
| `clients_fidelite` | Base clients, points de fidélité |
| `credit_client` | Ardoise client (vente à crédit) |
| `exports` | Export Excel/CSV des ventes et stocks |
| `scanner_mobile` | Scan via téléphone (HTTP réseau local) |
| `rapports_avances` | Rapports détaillés, marges, TVA, historique long |
| `sauvegarde_auto` | Sauvegarde automatique quotidienne |
| `fiscalite_tva` | Paramétrage TVA sur les reçus |
| `audit_logs` | Traçabilité caisse : connexions terminaux, actions |

Limite : **3 terminaux** réseau local.

### White Label — 200 000 F (perpétuel, sur devis)

Tout Pro, plus :

| Feature key | Description |
|---|---|
| `white_label` | Titre fenêtre = nom boutique, aucune mention HishamPOS |

Limite : terminaux **illimités**.

### Démo (aucune licence)

Standard uniquement + watermark "DÉMONSTRATION" sur PDF.
Limité à **50 ventes** ET **14 jours** depuis l'installation.
Après : Standard sans ventes (lecture seule, invitation à activer).

> ⚠️ Le démo n'est PAS tout Pro. Donner Pro en démo = donner le produit gratuitement.

---

## Sécurité — ce qui est stocké en DB

### Problème à résoudre

Sans chiffrement, n'importe qui avec DB Browser peut :
- Lire `licence_plan = standard` et le changer en `pro` → **upgrade gratuit**
- Lire `licence_features_extra = pharmacie_mode` et l'ajouter ailleurs

### Solution : chiffrement PBKDF2 + Fernet

Le plan et les features extra sont stockés **chiffrés** en DB.
La clé de déchiffrement est dérivée de la clé de licence elle-même
(que seul le serveur peut émettre).

Sans la clé de licence originale → impossible de lire ou modifier le plan.

```python
# Dérivation de clé robuste (PBKDF2, pas un simple .ljust())
import hashlib, base64
from cryptography.fernet import Fernet

def _deriver_cle(licence_key: str) -> bytes:
    """Dérive une clé Fernet 32 bytes depuis la clé de licence."""
    dk = hashlib.pbkdf2_hmac(
        'sha256',
        licence_key.encode(),
        b'hishipos_salt_v1',  # sel fixe connu de l'app
        iterations=100_000
    )
    return base64.urlsafe_b64encode(dk)

def chiffrer(texte: str, licence_key: str) -> str:
    f = Fernet(_deriver_cle(licence_key))
    return f.encrypt(texte.encode()).decode()

def dechiffrer(chiffre: str, licence_key: str) -> str:
    f = Fernet(_deriver_cle(licence_key))
    return f.decrypt(chiffre.encode()).decode()
```

> Note : la clé de licence brute n'est jamais stockée en DB.
> Seul le hash (SHA256) est gardé pour dériver la clé Fernet.

### Ce qui est stocké en DB (après activation)

| Clé DB | Valeur | Format |
|---|---|---|
| `licence_plan_enc` | plan chiffré | Fernet token |
| `licence_expire` | date expiration | `2027-01-15` (en clair, pas sensible) |
| `licence_features_enc` | features extra chiffrées | Fernet token ou vide |
| `licence_key_hash` | SHA256 de la clé licence | hex (pour dériver Fernet) |
| `licence_demo_install` | timestamp installation démo | entier Unix |
| `licence_demo_ventes` | nb ventes en démo | entier |

---

## Grace period — expiration douce

### Comportement

| Situation | Comportement |
|---|---|
| Licence valide | Tout fonctionne normalement |
| Expirée depuis 1–7 jours | Bandeau orange en haut, tout fonctionne |
| Expirée depuis 8+ jours | Ventes bloquées, lecture seule |
| Jamais activé (démo) | Standard + watermark + limite 50 ventes / 14j |

### Pourquoi 7 jours et pas 3 ou 30

- **3 jours** : trop court, client peut être en déplacement
- **7 jours** : une semaine, le temps de le contacter, payer, recevoir la clé
- **30 jours** : trop long, perd l'urgence du renouvellement

### Implémentation

```python
# modules/licence.py
from datetime import date

def statut_expiration() -> str:
    """Retourne 'ok', 'grace' (1-7j), ou 'expire' (8j+)."""
    expire_str = db.get_parametre('licence_expire', '')
    if not expire_str:
        return 'ok'  # Démo, géré séparément
    try:
        expire = date.fromisoformat(expire_str)
        jours = (date.today() - expire).days
        if jours <= 0:
            return 'ok'
        if jours <= 7:
            return 'grace'
        return 'expire'
    except Exception:
        return 'ok'
```

---

## Limite dure sur les caissiers (Standard)

La vérification UI seule n'est pas suffisante (bug possible, manipulation DB).
La règle est aussi vérifiée dans le module utilisateurs.

```python
# modules/features.py
def limite_caissiers() -> int:
    """Nombre max de caissiers selon le plan."""
    plan = plan_actuel()
    if plan == 'standard':
        return 1
    return 999  # illimité en pratique

# modules/utilisateurs.py — vérification dure avant création
def creer_utilisateur(..., role='caissier'):
    from modules.features import limite_caissiers
    if role == 'caissier':
        nb = db.fetch_one(
            "SELECT COUNT(*) as n FROM utilisateurs WHERE role='caissier'"
        )['n']
        if nb >= limite_caissiers():
            return False, "Limite caissiers atteinte pour ce plan"
    # ... suite de la création
```

---

## Identifiant matériel (anti-réinstallation démo)

Le compteur de ventes démo peut être remis à zéro en réinstallant.
Pour limiter ça sans serveur :

```python
import uuid, hashlib

def _hardware_id() -> str:
    """Identifiant stable basé sur l'adresse MAC."""
    mac = uuid.getnode()
    return hashlib.sha256(str(mac).encode()).hexdigest()[:16]
```

Au premier lancement démo, `hardware_id` est stocké en DB avec la date
d'installation. Si `hardware_id` change → réinstallation détectée → on
reset le compteur mais on conserve la limite de 14 jours côté serveur
(prochaine amélioration : envoyer le `hardware_id` au serveur à l'activation).

> Limite : ça ne bloque pas quelqu'un qui change sa carte réseau.
> La vraie protection complète = vérification serveur. Pour l'instant,
> c'est suffisant pour le marché cible.

---

## White Label

```python
# modules/features.py
def peut(feature: str) -> bool: ...

# ui/windows/principale.py
from modules.features import peut
from database import db

if peut('white_label'):
    self.setWindowTitle(db.get_parametre('boutique_nom', 'Ma Boutique'))
else:
    self.setWindowTitle("HishiPOS — Gestion Boutique")
```

Le client white label voit son propre nom partout. Aucune mention HishiPOS.
Cette feature est vendue en supplément (90 000 F/an tout compris).

---

## Scénarios concrets

### Scénario A — Petite épicerie, Standard

Mme Adjobi achète Standard 35 000 F + installation 15 000 F.
Active la clé → plan `standard` stocké chiffré en DB.

Elle voit : ventes, stock, reçus, ticket, rapports de base.
Elle ne voit pas : Clients, Exports (boutons grisés avec tooltip "Offre Pro").

Elle essaie d'ouvrir `boutique.db` avec DB Browser :
- Elle voit `licence_plan_enc = gAAAAABh...` (chiffré, illisible)
- Impossible de changer le plan sans la clé de licence

Six mois plus tard elle veut la fidélité clients → upgrade Pro 25 000 F.
Nouvelle clé → tout se débloque sans réinstaller.

---

### Scénario B — Superette avec 2 caisses, Pro

M. Sossou prend Pro d'emblée. Il veut un caissier par poste.
Feature `multi_caissiers` → il peut créer autant de caissiers que voulu.
Côté code : `limite_caissiers()` retourne 999.

---

### Scénario C — Client veut son logo uniquement (Standard)

Mme Dossou veut son logo sur les reçus. C'est déjà dans les paramètres
(Standard inclut `parametres`). Elle le fait elle-même en 2 minutes.
Pas de facturation supplémentaire.

---

### Scénario D — Pharmacie sur mesure

Pharmacie Béhanzin veut affichage du dosage sur 2 lignes.
C'est du développement sur mesure : devis 75 000 F.

Leur clé de licence retourne :
```json
{ "plan": "pro", "features_extra": "pharmacie_mode" }
```

`features_extra` est chiffré en DB. Impossible pour un concurrent de copier.
Dans le code : `if features.peut('pharmacie_mode'): ...`

---

### Scénario E — Licence expirée le 15 janvier

**16 janvier au matin** : vérification réseau → `expired`.
Statut = `grace` (jour 1 sur 7).
→ Bandeau orange : "Votre licence a expiré. Renouvelez avant le 22 janvier."
→ Tout fonctionne normalement.

**22 janvier** : statut = `expire` (jour 8).
→ Ventes bloquées. Message : "Contactez votre revendeur pour renouveler."
→ Lecture seule : il peut consulter ses ventes passées et son stock.
→ Il ne perd aucune donnée.

---

### Scénario F — Client essaie de rester en démo à vie

Installation → 50 ventes en 2 jours → bloqué.
Réinstallation → `hardware_id` identique → compteur reparti de 0 mais
la date d'install originale est retrouvée → 14 jours toujours comptés.
Après 14 jours : Standard sans ventes.

Pour débloquer : il doit activer une vraie licence. Pas d'autre chemin.

---

## Migration des clients existants

Les clients qui ont déjà l'app installée n'ont pas `licence_plan_enc` en DB.

```python
# Au démarrage (main.py), avant tout :
def migrer_plan_si_absent():
    if not db.get_parametre('licence_plan_enc'):
        # Client existant sans plan → Standard par défaut
        # (il a forcément une licence valide puisqu'il utilisait déjà l'app)
        # Le plan sera mis à jour au prochain check de licence en ligne
        db.set_parametre('licence_plan_enc', '__migrated__')
        db.set_parametre('licence_expire', '2025-12-31')  # grace period
```

Au prochain démarrage avec internet → la licence est re-vérifiée → plan correct stocké.

---

## Ordre d'implémentation (5h)

| Étape | Fichier(s) | Durée |
|---|---|---|
| 1 | `modules/features.py` — PLANS, `peut()`, `limite_caissiers()` | 45 min |
| 2 | Chiffrement PBKDF2+Fernet dans `modules/licence.py` | 45 min |
| 3 | Grace period + statut expiration dans `modules/licence.py` | 30 min |
| 4 | Migration DB + `hardware_id` démo | 30 min |
| 5 | UI : griser/masquer features selon plan (3 fenêtres) | 1h |
| 6 | Watermark DEMO sur PDF + titre white label | 30 min |
| 7 | Limite dure caissiers dans `modules/utilisateurs.py` | 20 min |
| 8 | Serveur : ajouter `plan` + `features_extra` dans réponse JSON | 20 min |
| **Total** | | **~5h** |

---

## Ce qu'on NE fait PAS

- Pas d'obfuscation du binaire (inutile, protection = licence serveur)
- Pas de vérification réseau à chaque vente (lent, bloque si offline)
- Pas de version Standard et Pro séparées (un seul `.exe`)
- Pas de blocage brutal sans grace period (mauvaise réputation garantie)
