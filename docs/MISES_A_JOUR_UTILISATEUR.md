# 🔄 Guide des Mises à Jour - Pour Utilisateurs

Guide simple pour comprendre et utiliser le système de mises à jour automatique de Gestion Boutique.

---

## 🎯 Comment Ça Marche ?

### Vérification Automatique

**Au démarrage de l'application :**
1. L'application vérifie automatiquement s'il existe une nouvelle version
2. Si une mise à jour est disponible, une notification s'affiche
3. Vous choisissez quoi faire (télécharger, plus tard, ou ignorer)

**⏱️ Moment de la vérification :**
- 3 secondes après l'ouverture du dashboard
- Très rapide (quelques KB seulement)
- Ne ralentit pas l'application

---

## 📱 Notification de Mise à Jour

### À Quoi Ça Ressemble ?

```
┌──────────────────────────────────────────┐
│  🎉 Nouvelle version disponible !        │
├──────────────────────────────────────────┤
│  Nouvelle version : 2.1.0                │
│  Date de sortie : 08/02/2026             │
│  Taille du téléchargement : ~105 MB      │
│  Version actuelle : 2.0.0                │
├──────────────────────────────────────────┤
│  Nouvelle version avec système d'audit   │
│  trail complet et corrections de bugs    │
├──────────────────────────────────────────┤
│  [📥 Télécharger] [📄 Voir changements]  │
│  [⏰ Plus tard] [🚫 Ignorer cette version]│
└──────────────────────────────────────────┘
```

---

## 🔽 Comment Installer une Mise à Jour ?

### Étape 1 : Télécharger

1. **Cliquer sur "📥 Télécharger"**
   - Votre navigateur s'ouvre automatiquement
   - Le fichier commence à télécharger

2. **Attendre la fin du téléchargement**
   - Selon votre connexion : 2-10 minutes
   - Fichier : `GestionBoutique.exe` (~100-150 MB)

### Étape 2 : Sauvegarder Vos Données

**⚠️ TRÈS IMPORTANT - NE JAMAIS SAUTER CETTE ÉTAPE !**

1. **Ouvrir l'application (si fermée)**
2. **Menu Fichier → Sauvegarde**
3. **Attendre confirmation "Sauvegarde créée"**
4. **Noter l'emplacement du fichier de sauvegarde**

```
Exemple d'emplacement :
C:\Users\VotreNom\AppData\Roaming\GestionBoutique\sauvegardes\
boutique_backup_20260208_143022.db
```

### Étape 3 : Fermer l'Application

1. **Fermer complètement** Gestion Boutique
2. **Vérifier** qu'elle n'apparaît plus dans la barre des tâches

### Étape 4 : Remplacer le Fichier

1. **Aller dans le dossier** où se trouve l'ancien .exe
   - Exemple : `C:\Program Files\GestionBoutique\`
   - OU : Sur le Bureau

2. **Renommer l'ancien** (pour garder une copie)
   ```
   GestionBoutique.exe → GestionBoutique_old.exe
   ```

3. **Copier le nouveau** fichier téléchargé
   - Depuis : `C:\Users\VotreNom\Downloads\GestionBoutique.exe`
   - Vers : `C:\Program Files\GestionBoutique\` (ou votre dossier)

### Étape 5 : Relancer l'Application

1. **Double-cliquer** sur le nouveau `GestionBoutique.exe`
2. **Se connecter** normalement
3. **Vérifier la version** : Menu Aide → À propos

---

## ⏰ Options de Notification

### Bouton "Plus tard"

**Quand utiliser :**
- Vous êtes occupé
- Vous voulez terminer votre vente en cours
- Vous n'avez pas le temps maintenant

**Ce qui se passe :**
- La notification se ferme
- Au prochain démarrage, la notification réapparaîtra
- Vos données sont en sécurité

### Bouton "Ignorer cette version"

**Quand utiliser :**
- Vous ne voulez pas cette version spécifique
- Vous attendez une version ultérieure

**Ce qui se passe :**
- Vous ne verrez plus la notification pour cette version
- Vous serez notifié des versions suivantes (ex: 2.2.0)
- Vous pouvez toujours installer manuellement

**⚠️ Note :** Si la mise à jour est **critique** (badge rouge), il est fortement recommandé de l'installer.

---

## 🔍 Vérification Manuelle

### Comment Vérifier Manuellement ?

Si vous n'avez pas reçu de notification ou voulez vérifier :

1. **Ouvrir l'application**
2. **Menu Aide → 🔄 Vérifier les mises à jour**
3. **Attendre** (quelques secondes)
4. **Notification apparaît** si mise à jour disponible

---

## 🆘 Problèmes Fréquents

### "Aucune connexion internet"

**Solution :**
1. Vérifier votre connexion internet
2. Réessayer plus tard
3. Vérifier manuellement : Menu Aide → Vérifier les mises à jour

### "Téléchargement très lent"

**Solution :**
1. Normal avec connexion lente (fichier ~100 MB)
2. Laisser télécharger en arrière-plan
3. Peut prendre 10-30 minutes selon connexion
4. Ne pas fermer le navigateur

### "Fichier introuvable après téléchargement"

**Solution :**
1. Vérifier le dossier `Téléchargements`
2. Chercher "GestionBoutique.exe"
3. Si introuvable, re-télécharger

### "L'application ne démarre plus après MAJ"

**Solution - Restaurer l'ancienne version :**
1. Supprimer le nouveau .exe
2. Renommer `GestionBoutique_old.exe` → `GestionBoutique.exe`
3. Relancer
4. Contacter le support

**Solution - Restaurer les données :**
1. Menu Fichier → Restaurer
2. Sélectionner la sauvegarde récente
3. Attendre la restauration
4. Relancer

---

## ✅ Bonnes Pratiques

### Avant Chaque Mise à Jour

- ✅ **Toujours** faire une sauvegarde
- ✅ **Fermer** toutes les ventes en cours
- ✅ **Noter** l'emplacement de la sauvegarde
- ✅ **Garder** l'ancien .exe (renommer en _old)

### Après Chaque Mise à Jour

- ✅ **Vérifier** la version dans Menu Aide → À propos
- ✅ **Tester** une vente simple
- ✅ **Vérifier** que toutes les données sont là
- ✅ **Supprimer** l'ancien .exe après 1 semaine (si tout OK)

---

## 📞 Support

### En Cas de Problème

1. **Consulter** ce guide
2. **Vérifier** les sauvegardes dans `AppData\Roaming\GestionBoutique\sauvegardes\`
3. **Contacter** le support :
   - WhatsApp : [Votre numéro]
   - Email : [Votre email]

### Informations à Fournir

Quand vous contactez le support :
- Version actuelle (Menu Aide → À propos)
- Message d'erreur exact (si applicable)
- Étape où ça bloque
- Captures d'écran

---

## 🎓 Questions Fréquentes

### Q : Les mises à jour sont-elles obligatoires ?

**R :** Non, mais fortement recommandées.
- Les mises à jour corrigent des bugs
- Ajoutent de nouvelles fonctionnalités
- Améliorent la sécurité

**Exception :** Les mises à jour **critiques** (badge rouge) doivent être installées rapidement.

### Q : Mes données seront-elles perdues ?

**R :** Non, si vous suivez les étapes :
1. Toujours faire une sauvegarde avant MAJ
2. Ne jamais supprimer le dossier `AppData\Roaming\GestionBoutique\`
3. Les données sont dans la base, pas dans le .exe

### Q : Combien de temps prend une MAJ ?

**R :**
- Téléchargement : 5-30 minutes (selon connexion)
- Sauvegarde : 10 secondes
- Installation : 1 minute
- **Total : ~10-40 minutes**

### Q : Puis-je continuer à travailler pendant le téléchargement ?

**R :** Oui ! Le téléchargement se fait dans le navigateur.
- Vous pouvez continuer à utiliser l'application
- Installez la MAJ quand vous êtes prêt (fin de journée)

### Q : La vérification utilise-t-elle beaucoup de data internet ?

**R :** Non, très peu :
- Vérification : ~2-3 KB (négligeable)
- Se fait automatiquement 1 fois par démarrage
- Téléchargement : ~100-150 MB (seulement si vous cliquez "Télécharger")

### Q : Que faire si je n'ai pas de connexion internet ?

**R :**
- L'application fonctionne normalement (offline)
- Pas de notification (normal)
- Vérifier manuellement quand connexion rétablie
- Ou demander le .exe au support par clé USB

---

## 📝 Checklist Rapide

```
☐ Notification apparue
☐ Lire les changements
☐ Cliquer "Télécharger"
☐ Attendre téléchargement complet
☐ Menu Fichier → Sauvegarde
☐ Fermer l'application
☐ Renommer ancien .exe en _old
☐ Copier nouveau .exe
☐ Relancer application
☐ Vérifier version dans À propos
☐ Tester une vente
☐ Tout fonctionne ✅
```

---

**Version du guide :** 1.0
**Date :** 2026-02-08
**Pour :** Gestion Boutique v2.0+
