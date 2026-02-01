## RÈGLES DE RÉPONSE (Mode Éco)
- Be concise. Code only. No chatty explanations.
- When editing, use search/replace blocks. DO NOT output full files.
- No obvious comments.
- Focus on low token usage.

---
## INFOS DU PROJET

# GestionBoutique v2

## Qu'est-ce que c'est
Logiciel de gestion de boutique / point de vente (POS) pour commerces. Gestion des ventes, produits, clients, stock, recus, imprimante thermique. Deploye au Benin (devise FCFA, TVA 18%).

## Migration en cours : Tkinter → PySide6
**Lire `MIGRATION_PYSIDE6.md` pour le plan complet.**

### Etat d'avancement
- [x] Phase 0 : Fondation (ui/, theme, composants, config multiplateforme)
- [x] Phase 1 : Authentification (licence, premier lancement, login)
- [x] Phase 2 : Dashboard principal
- [x] Phase 3 : Ventes (critique)
- [x] Phase 4 : Gestion (produits, clients, utilisateurs)
- [x] Phase 5 : Rapports et outils
- [x] Phase 6 : Nettoyage final

## Migration terminée ! ✅

### Structure finale
- `main.py` → PySide6 (point d'entree)
- `main_tkinter_backup.py` → Backup Tkinter (ancien)
- `ui/` → Fenetres PySide6
- `modules/` → Logique metier (independant du framework UI)
- `database.py` → Couche SQLite

## Architecture

```
main.py / main_qt.py          # Points d'entree
config.py                      # Configuration, couleurs, chemins (multiplateforme)
database.py                    # SQLite singleton (db.execute_query, db.get_parametre)
modules/                       # Logique metier (18 modules, aucun import UI)
  produits.py, ventes.py, clients.py, utilisateurs.py,
  paiements.py, rapports.py, recus.py, imprimante.py,
  licence.py, synchronisation.py, sauvegarde.py,
  codebarres.py, fiscalite.py, scanner_camera.py,
  theme.py, logger.py, whatsapp.py, export.py
interface/                     # UI Tkinter (ancien)
ui/                            # UI PySide6 (nouveau)
  components/                  # Composants reutilisables (table, dialogs, toolbar, scanner)
  windows/                     # Fenetres de l'application
  theme.py                     # Systeme de theme QSS
  platform.py                  # Detection OS, chemins
tests/
```

## Flux critique : Vente
```
Scanner/saisie → Panier (memoire) → Paiement (modal) → Transaction DB atomique
→ MAJ stock → Recu PDF → Confirmation → Callback refresh dashboard
```

## Base de donnees
SQLite : `{BASE_DIR}/data/boutique.db`
Tables principales : produits, ventes, details_ventes, clients, paiements, utilisateurs, parametres (key-value), historique_stock, logs_actions, taux_tva, devises, sync_queue

## Conventions
- Langue de l'interface : francais
- Noms de classes/fichiers Tkinter : `FenetreXxx` / `fenetre_xxx.py`
- Noms de classes/fichiers Qt : `XxxWindow` / `xxx.py` (dans ui/windows/)
- Signaux/slots Qt (pas de callbacks bruts dans le nouveau code)
- Les modules metier ne doivent JAMAIS importer tkinter ou PySide6

## Commandes utiles
```bash
python main.py                    # Lancer application (PySide6)
python main_tkinter_backup.py    # Lancer backup Tkinter (si necessaire)
python -m pytest tests/           # Tests
pyinstaller GestionBoutique.spec  # Build executable
```

## Dependances
Voir `requirements.txt`. Migration ajoute : `PySide6>=6.6.0`, `platformdirs>=4.0.0`

## Environnement de dev
- Python Windows : `/mnt/c/Users/hp/AppData/Local/Programs/Python/Python311/python.exe`
- Depuis WSL, lancer avec ce chemin pour les tests GUI
- Tests : ce meme Python + pytest

## Multiplateforme
L'application doit fonctionner sur Windows, Linux et macOS.
- Chemins : `ui/platform.py` gere la detection OS (get_base_dir, get_serial_ports, etc.)
- Config : `config.py` utilise `_get_base_dir()` multiplateforme (Windows/Linux/macOS)
- Ports serie imprimante : detecter selon OS
- Packaging : PyInstaller sur chaque OS cible
