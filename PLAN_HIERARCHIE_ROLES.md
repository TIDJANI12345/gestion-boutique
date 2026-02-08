# Plan de Travail - Hiérarchie des Rôles

## 🎯 Objectif

Implémenter un système de rôles hiérarchisé avec 3 niveaux d'accès distincts :

1. **Super-Admin (Patron)** - 1 seul compte, accès total
2. **Gestionnaire** - Gestion des stocks et produits
3. **Caissier** - Ventes uniquement

---

## 📋 Structure des Rôles

### 🔴 Super-Admin (Patron)

**Permissions :**
- ✅ Toutes les fonctionnalités
- ✅ Gérer les utilisateurs (créer, modifier, supprimer, réinitialiser MDP)
- ✅ Voir toutes les ventes (tous vendeurs)
- ✅ Accès aux rapports globaux
- ✅ Paramètres système (TVA, devises, licence)
- ✅ Gestion produits et stocks
- ✅ Effectuer des ventes
- ✅ Sauvegarde/restauration

**Dashboard :**
- Vue d'ensemble globale (CA total, toutes ventes, tous vendeurs)
- Statistiques détaillées par vendeur
- Accès menu complet

**Contrainte :**
- ⚠️ **UN SEUL compte super-admin** autorisé
- Lors de l'installation : premier utilisateur créé = super-admin

---

### 🟡 Gestionnaire

**Permissions :**
- ✅ Gestion produits (ajouter, modifier, supprimer)
- ✅ Gestion stocks (ajuster, historique)
- ✅ Gestion clients (ajouter, modifier)
- ✅ Voir ses propres ventes
- ✅ Effectuer des ventes (optionnel selon config)
- ❌ PAS d'accès utilisateurs
- ❌ PAS de paramètres système
- ❌ PAS de vue globale des ventes

**Dashboard :**
- Stats personnelles (si autorisé à vendre)
- Vue produits et stocks
- Alertes stock faible

---

### 🟢 Caissier

**Permissions :**
- ✅ Effectuer des ventes uniquement
- ✅ Voir ses propres ventes
- ✅ Scanner produits (caméra/manuel)
- ✅ Imprimer reçus
- ❌ PAS de gestion produits
- ❌ PAS de gestion stocks
- ❌ PAS de gestion clients (peut chercher clients existants)
- ❌ PAS d'accès paramètres

**Dashboard :**
- Dashboard simplifié actuel (déjà implémenté)
- Stats personnelles uniquement
- Bouton vente en gros

---

## 🛠️ Tâches d'Implémentation

### Phase 1 : Mise à jour Base de Données

**Fichier :** `database.py`

**Actions :**

1. **Ajouter colonne `super_admin` à table `utilisateurs`**
   ```sql
   ALTER TABLE utilisateurs ADD COLUMN super_admin BOOLEAN DEFAULT 0;
   ```

2. **Migration automatique**
   ```python
   # Dans create_tables(), après création table utilisateurs
   try:
       cursor.execute("SELECT super_admin FROM utilisateurs LIMIT 1")
   except sqlite3.OperationalError:
       logger.info("Migration: Ajout colonne super_admin")
       cursor.execute("ALTER TABLE utilisateurs ADD COLUMN super_admin BOOLEAN DEFAULT 0")
       conn.commit()
   ```

3. **Marquer premier utilisateur comme super-admin**
   ```python
   # Si aucun super-admin n'existe, marquer le premier
   result = db.fetch_one("SELECT COUNT(*) FROM utilisateurs WHERE super_admin = 1")
   if result[0] == 0:
       # Marquer premier utilisateur actif comme super-admin
       db.execute_query("""
           UPDATE utilisateurs
           SET super_admin = 1, role = 'patron'
           WHERE id = (SELECT id FROM utilisateurs ORDER BY id LIMIT 1)
       """)
   ```

---

### Phase 2 : Mise à jour Module Utilisateurs

**Fichier :** `modules/utilisateurs.py`

**Actions :**

1. **Ajouter méthode `est_super_admin()`**
   ```python
   @staticmethod
   def est_super_admin(user_id):
       """Vérifier si un utilisateur est super-admin"""
       result = db.fetch_one(
           "SELECT super_admin FROM utilisateurs WHERE id = ?",
           (user_id,)
       )
       return result and result[0] == 1
   ```

2. **Modifier `creer_utilisateur()` pour empêcher création multiple super-admin**
   ```python
   # Dans creer_utilisateur(), avant INSERT
   if nouveau_role == 'patron':
       # Vérifier qu'il n'existe pas déjà un super-admin
       count = db.fetch_one("SELECT COUNT(*) FROM utilisateurs WHERE super_admin = 1")
       if count and count[0] > 0:
           return False, "Un super-admin existe déjà. Utilisez le rôle 'gestionnaire'."
       super_admin_flag = 1
   else:
       super_admin_flag = 0

   # Modifier INSERT pour inclure super_admin
   query = """
       INSERT INTO utilisateurs (nom, prenom, email, mot_de_passe, role, super_admin)
       VALUES (?, ?, ?, ?, ?, ?)
   """
   ```

3. **Modifier `modifier_role()` pour protéger super-admin**
   ```python
   @staticmethod
   def modifier_role(user_id, nouveau_role):
       # Vérifier si l'utilisateur est super-admin
       if Utilisateur.est_super_admin(user_id):
           return False  # Impossible de changer rôle du super-admin

       # Empêcher promotion vers patron si un existe déjà
       if nouveau_role == 'patron':
           count = db.fetch_one("SELECT COUNT(*) FROM utilisateurs WHERE super_admin = 1")
           if count and count[0] > 0:
               return False

       # Procéder...
   ```

4. **Ajouter rôles disponibles**
   ```python
   ROLES_DISPONIBLES = {
       'patron': 'Super-Admin (Patron)',
       'gestionnaire': 'Gestionnaire (Stocks)',
       'caissier': 'Caissier (Ventes)'
   }
   ```

---

### Phase 3 : Mise à jour Interface Utilisateurs

**Fichier :** `ui/windows/utilisateurs.py`

**Actions :**

1. **Modifier combo rôle pour afficher nouveaux rôles**
   ```python
   # Remplacer
   self._combo_role.addItems(["caissier", "patron"])

   # Par
   self._combo_role.addItems(["caissier", "gestionnaire"])
   # Note: "patron" n'est plus dans la liste (créé automatiquement à l'installation)
   ```

2. **Ajouter indicateur visuel super-admin dans tableau**
   ```python
   # Dans _charger_utilisateurs()
   for u in utilisateurs:
       statut = "Actif" if u[6] else "Inactif"
       role_display = u[5] or ""

       # Si super-admin, ajouter badge
       if len(u) > 7 and u[7] == 1:  # super_admin column
           role_display = f"⭐ {role_display}"

       lignes.append([...])
   ```

3. **Désactiver boutons pour super-admin**
   ```python
   # Dans _selectionner_utilisateur()
   def _selectionner_utilisateur(self, row: int):
       ligne = self._table_model.obtenir_ligne(row)
       if not ligne:
           return
       self._user_selectionne_id = ligne[0]

       # Vérifier si super-admin
       from modules.utilisateurs import Utilisateur
       is_super = Utilisateur.est_super_admin(self._user_selectionne_id)

       # Désactiver boutons si super-admin sélectionné
       # (empêcher modification/suppression du super-admin)
       # TODO: implémenter logique de désactivation boutons
   ```

---

### Phase 4 : Dashboards Spécifiques par Rôle

**Fichiers à créer/modifier :**

1. **Dashboard Gestionnaire** (nouveau)
   - Créer `ui/windows/principale_gestionnaire.py`
   - S'inspirer de `principale_caissier.py`
   - Menu : Produits, Stocks, Clients, Mes Ventes (si autorisé)
   - Pas de menu Utilisateurs, Paramètres

2. **Routage selon rôle** dans `main.py`
   ```python
   # Dans fonction après login
   role = utilisateur['role']

   if role == 'patron' or utilisateur.get('super_admin') == 1:
       from ui.windows.principale import PrincipaleWindow
       window = PrincipaleWindow(utilisateur)
   elif role == 'gestionnaire':
       from ui.windows.principale_gestionnaire import PrincipaleGestionnaireWindow
       window = PrincipaleGestionnaireWindow(utilisateur)
   elif role == 'caissier':
       from ui.windows.principale_caissier import PrincipaleCaissierWindow
       window = PrincipaleCaissierWindow(utilisateur)
   else:
       # Rôle inconnu
       erreur("Rôle non reconnu")
       return
   ```

---

### Phase 5 : Contrôles d'Accès (Permissions)

**Fichiers à modifier :** Toutes les fenêtres sensibles

**Actions :**

1. **Créer module de permissions** `modules/permissions.py`
   ```python
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
           role = utilisateur.get('role')
           return permission in Permissions.PERMISSIONS.get(role, [])
   ```

2. **Appliquer contrôles dans fenêtres**
   ```python
   # Exemple dans principale.py
   def ouvrir_utilisateurs(self):
       from modules.permissions import Permissions
       if not Permissions.peut(self.utilisateur, 'gerer_utilisateurs'):
           erreur(self, "Accès refusé", "Vous n'avez pas la permission.")
           return

       # Ouvrir fenêtre...
   ```

3. **Masquer menus selon permissions**
   ```python
   # Dans _setup_menubar() de principale.py
   if Permissions.peut(self.utilisateur, 'gerer_utilisateurs'):
       menu.addAction("Utilisateurs", self.ouvrir_utilisateurs)

   if Permissions.peut(self.utilisateur, 'parametres_systeme'):
       menu.addAction("Paramètres fiscaux", self.ouvrir_parametres_fiscaux)
   ```

---

### Phase 6 : Tests et Validation

**Tests à effectuer :**

1. **Test Super-Admin**
   - [ ] Un seul super-admin peut exister
   - [ ] Impossible de créer 2e patron
   - [ ] Super-admin voit toutes les ventes
   - [ ] Peut réinitialiser MDP de tous
   - [ ] Accès à tous les menus

2. **Test Gestionnaire**
   - [ ] Peut gérer produits
   - [ ] Peut gérer stocks
   - [ ] Peut gérer clients
   - [ ] Voit uniquement ses ventes (si autorisé à vendre)
   - [ ] Pas d'accès utilisateurs
   - [ ] Pas d'accès paramètres système

3. **Test Caissier**
   - [ ] Peut faire ventes
   - [ ] Voit uniquement ses ventes
   - [ ] Dashboard simplifié
   - [ ] Pas d'accès gestion produits/stocks
   - [ ] Pas d'accès utilisateurs

4. **Test Sécurité**
   - [ ] Impossible de modifier rôle du super-admin
   - [ ] Impossible de désactiver super-admin
   - [ ] Tentative d'accès non autorisé = erreur
   - [ ] Logs d'actions correctement enregistrés

---

## 📝 Notes Importantes

### Migration Utilisateurs Existants

Lors du déploiement, script de migration :

```python
# Script à exécuter UNE FOIS
def migrer_roles_existants():
    """Migrer les anciens rôles vers nouveau système"""

    # 1. Marquer premier utilisateur 'patron' comme super-admin
    db.execute_query("""
        UPDATE utilisateurs
        SET super_admin = 1
        WHERE role = 'patron'
        ORDER BY id
        LIMIT 1
    """)

    # 2. Les autres 'patron' deviennent 'gestionnaire'
    db.execute_query("""
        UPDATE utilisateurs
        SET role = 'gestionnaire'
        WHERE role = 'patron' AND super_admin = 0
    """)

    print("✅ Migration rôles terminée")
```

### Configuration Gestionnaire peut Vendre

Ajouter paramètre DB :

```python
# Permettre aux gestionnaires d'effectuer des ventes
db.set_parametre('gestionnaire_peut_vendre', '1')  # 1=oui, 0=non
```

Utiliser dans permissions :
```python
@staticmethod
def peut(utilisateur, permission):
    role = utilisateur.get('role')
    perms = Permissions.PERMISSIONS.get(role, []).copy()

    # Ajouter permission vente pour gestionnaire si configuré
    if role == 'gestionnaire' and permission == 'effectuer_ventes':
        if db.get_parametre('gestionnaire_peut_vendre', '1') == '1':
            return True

    return permission in perms
```

---

## 🎨 Interface Utilisateur

### Badges Visuels Rôles

Dans liste utilisateurs :
- ⭐ **Patron** (super-admin)
- 📦 **Gestionnaire**
- 💰 **Caissier**

### Couleurs selon Rôle

```python
ROLE_COLORS = {
    'patron': '#DC2626',      # Rouge (admin)
    'gestionnaire': '#F59E0B', # Orange (gestion)
    'caissier': '#10B981'      # Vert (ventes)
}
```

---

## ✅ Checklist Finale

### Base de Données
- [ ] Colonne `super_admin` ajoutée
- [ ] Migration automatique implémentée
- [ ] Premier utilisateur marqué super-admin

### Module Utilisateurs
- [ ] Méthode `est_super_admin()`
- [ ] Protection contre création multiple super-admin
- [ ] Protection modification rôle super-admin
- [ ] Rôles disponibles mis à jour

### Interface
- [ ] Combo rôle mis à jour (pas de "patron" sélectionnable)
- [ ] Badge ⭐ pour super-admin dans tableau
- [ ] Bouton réinitialiser MDP implémenté ✅
- [ ] Désactivation boutons pour super-admin

### Dashboards
- [ ] Dashboard gestionnaire créé
- [ ] Routage selon rôle implémenté
- [ ] Menus adaptés selon permissions

### Permissions
- [ ] Module `permissions.py` créé
- [ ] Contrôles d'accès appliqués
- [ ] Menus masqués selon rôle

### Tests
- [ ] Tests super-admin
- [ ] Tests gestionnaire
- [ ] Tests caissier
- [ ] Tests sécurité

---

## 🚀 Ordre d'Exécution Recommandé

1. **Phase 1** - Base de données (critique)
2. **Phase 2** - Module utilisateurs (dépend de Phase 1)
3. **Phase 5** - Permissions (framework général)
4. **Phase 3** - Interface utilisateurs (dépend de Phase 2)
5. **Phase 4** - Dashboards (dépend de Phase 5)
6. **Phase 6** - Tests (final)

---

## 📞 Support

Si blocage ou question :
- Relire section concernée
- Vérifier logs application (`data/logs/`)
- Tester avec utilisateurs de test

---

**Bonne chance ! 🎯**
