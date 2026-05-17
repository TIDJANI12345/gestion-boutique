# Plan — Mode Réseau Local Multi-Terminaux

## Réponse à la question SQLite

SQLite **seul sur le réseau** = ❌ (un fichier partagé sur WiFi provoque des corruptions)

SQLite **via une API locale** = ✅ Parfaitement capable pour 2–5 terminaux

La solution : le PC Serveur fait tourner une **API Flask locale** qui est le seul à
toucher SQLite. Les autres PC envoient des requêtes HTTP à cette API.
C'est exactement la même architecture que PythonAnywhere, mais en local.

Pour les supermarchés avec 10+ caisses très actives → migration vers MySQL possible
plus tard, sans changer l'architecture (juste changer le moteur de DB).

---

## Architecture cible

```
                    ┌─────────────────────────────────┐
                    │         PC SERVEUR               │
                    │  ┌─────────────┐  ┌──────────┐  │
                    │  │  Flask API  │  │  SQLite  │  │
                    │  │  port 5050  │←→│  boutique│  │
                    │  └─────────────┘  └──────────┘  │
                    │  + Caisse normale (optionnel)    │
                    └────────────┬────────────────────┘
                                 │ WiFi local
              ┌──────────────────┼──────────────────┐
              ↓                  ↓                  ↓
        PC Caisse 1        PC Caisse 2        PC Caisse 3
        (client)           (client)           (client)
        pas de DB          pas de DB          pas de DB
        locale             locale             locale
```

```
Internet (uniquement au démarrage)
    ↓
PythonAnywhere — validation licence uniquement
```

---

## Plans et limites

| Plan     | Terminaux max | Réseau local |
|----------|--------------|--------------|
| Standard | 1 PC         | ❌           |
| Pro      | 3 PC         | ✅           |
| White Label | Illimité  | ✅           |

---

## Ce qu'on supprime

- [ ] `modules/synchronisation.py` — sync cloud des données (produits/ventes)
- [ ] Endpoints PA : `/api/sync/push`, `/api/sync/pull`, `/api/sync/ping`
- [ ] Table `sync_queue` dans la DB locale
- [ ] `serveur_sync/` dans PythonAnywhere (si séparé)
- [ ] Bouton "Synchroniser" dans l'UI (ou le transformer en "Statut réseau")

**PythonAnywhere conserve uniquement :**
- `/api/activer` — activation licence
- `/api/verifier` — vérification licence
- `/admin/generer` — dashboard admin licences

---

## Ce qu'on crée

### 1. `serveur_local/api_locale.py`
API Flask qui tourne sur le PC Serveur (port 5050, réseau local uniquement).

**Endpoints à créer :**
```
GET  /ping                     → health check + info serveur
GET  /produits                 → liste produits
POST /produits                 → créer/modifier produit
GET  /ventes                   → liste ventes (avec filtres date)
POST /ventes                   → enregistrer une vente
GET  /stats/dashboard          → totaux pour le dashboard
GET  /utilisateurs             → liste utilisateurs
POST /utilisateurs             → créer/modifier utilisateur
GET  /stock/alertes            → produits en rupture/alerte
```

**Authentification locale :** token simple partagé sur le réseau local
(pas besoin de sécurité forte — réseau WiFi privé de la boutique)

### 2. `modules/client_reseau.py`
Remplace l'accès direct à SQLite pour les PC clients.
Même interface que `database.py` → zéro changement dans le reste du code.

```python
# Avant (PC standalone)
from database import db
produits = db.fetch_all("SELECT * FROM produits")

# Après (PC client) — même interface !
from modules.client_reseau import db
produits = db.fetch_all("SELECT * FROM produits")
```

### 3. `config.py` — nouveaux paramètres
```python
MODE_RESEAU = 'standalone' | 'serveur' | 'client'
SERVEUR_LOCAL_URL = 'http://192.168.x.x:5050'  # configuré par l'admin
SERVEUR_LOCAL_TOKEN = 'xxxx'  # token partagé
```

### 4. UI — `ui/windows/config_reseau.py`
Fenêtre de configuration réseau (accessible depuis le menu admin) :
- Choisir le mode : Standalone / Serveur / Client
- Si Client : saisir l'IP du serveur (ou découverte automatique)
- Tester la connexion
- Voir les terminaux connectés (côté serveur)

### 5. `main.py` — détection au démarrage
```
Démarrage
  → Lire MODE_RESEAU depuis config
  → Si 'standalone' : utiliser database.py (actuel, rien ne change)
  → Si 'serveur'    : démarrer api_locale.py en thread + utiliser database.py
  → Si 'client'     : utiliser client_reseau.py (parle à l'API du serveur)
```

---

## Ordre d'implémentation

### Étape 1 — Nettoyage (supprimer la vieille sync)
- Supprimer `modules/synchronisation.py`
- Nettoyer `main.py` (retirer le démarrage de la sync auto)
- Retirer les endpoints sync de `api_pythonanywhere.py`
- Supprimer `sync_queue` de la DB schema

### Étape 2 — API locale (serveur_local/api_locale.py)
- Créer le serveur Flask avec tous les endpoints
- Tester en standalone sur un seul PC
- Authentification par token simple

### Étape 3 — Client réseau (modules/client_reseau.py)
- Créer le client qui reproduit l'interface de `database.py`
- Tester : PC client → PC serveur → SQLite

### Étape 4 — Intégration main.py
- Détection du mode au démarrage
- Démarrage conditionnel de l'API si mode serveur

### Étape 5 — UI configuration réseau
- Fenêtre de config (IP serveur, mode, test connexion)
- Accessible uniquement pour le patron

### Étape 6 — Découverte automatique (optionnel)
- Le serveur diffuse sa présence sur le réseau local (UDP broadcast)
- Les clients le trouvent automatiquement sans saisir l'IP

### Étape 7 — Vérification licences multi-terminaux
- Valider que le plan autorise le nombre de terminaux connectés
- Bloquer la connexion si quota dépassé

---

## Points d'attention

1. **Hors-ligne** : si le serveur PC s'éteint, les caisses clientes ne peuvent
   plus vendre. Solution : afficher un message clair + possibilité de basculer
   temporairement en mode standalone avec sync différée.

2. **IDs des ventes** : les PC clients ne doivent pas générer les IDs — c'est
   le serveur qui les génère (évite les doublons).

3. **Impression** : chaque PC imprime sur son imprimante locale — l'API
   renvoie les données du reçu, le PC client gère l'impression.

4. **Migration** : les boutiques existantes (standalone) ne changent rien.
   Le mode réseau est opt-in, configuré manuellement par le patron.

---

## Estimation

| Étape | Complexité |
|-------|-----------|
| 1. Nettoyage sync | Facile |
| 2. API locale | Moyen |
| 3. Client réseau | Moyen |
| 4. Intégration main.py | Facile |
| 5. UI config réseau | Moyen |
| 6. Découverte auto | Difficile (optionnel) |
| 7. Vérif licences | Facile |
