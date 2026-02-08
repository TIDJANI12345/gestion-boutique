# Guide : Scanner avec la Caméra du Téléphone

## Vue d'ensemble

GestionBoutique vous permet d'utiliser la caméra de votre téléphone (Android/iOS) comme scanner de codes-barres. Cette fonctionnalité est utile si :
- Vous n'avez pas de webcam sur votre PC
- La caméra de votre téléphone est de meilleure qualité
- Vous voulez plus de flexibilité pour scanner des produits

---

## Méthode 1 : DroidCam (Recommandé) 📱

### Avantages
- ✅ Gratuit
- ✅ Compatible Android + iOS
- ✅ Simple à configurer
- ✅ Bonne qualité vidéo

### Installation

#### Sur le téléphone
1. **Android** : Téléchargez [DroidCam](https://play.google.com/store/apps/details?id=com.dev47apps.droidcam) depuis Google Play
2. **iOS** : Téléchargez [DroidCam](https://apps.apple.com/app/droidcam-webcam-obs-camera/id1510258102) depuis App Store
3. Lancez l'application
4. **Notez l'adresse IP et le port affichés** (ex: `192.168.1.100:4747`)

#### Sur le PC (optionnel mais recommandé)
1. Téléchargez le client DroidCam depuis [www.dev47apps.com](https://www.dev47apps.com/)
2. Installez-le (Windows/Linux)
3. Cela installe aussi un driver qui permet d'utiliser DroidCam comme webcam virtuelle

http://192.168.137.27:4747/video

### Configuration dans GestionBoutique

1. Ouvrez **GestionBoutique**
2. Allez dans **Menu > Paramètres > Paramètres Caisse**
3. Dans la section **"Caméra de scan"**, trouvez **"Source caméra"**
4. Entrez l'URL complète : `http://192.168.1.100:4747/video`
   - Remplacez `192.168.1.100` par l'IP affichée dans l'app mobile
   - Remplacez `4747` par le port affiché
5. Cliquez sur **"Tester"** pour vérifier la connexion
6. Si le test réussit, cliquez sur **"Enregistrer"**

### Utilisation

1. **Sur le téléphone** : Lancez DroidCam et placez-le face aux produits
2. **Dans GestionBoutique** : Ouvrez la fenêtre **Ventes**
3. Cliquez sur **"Scanner"** ou **"Afficher caméra"**
4. La caméra du téléphone s'affiche et scanne automatiquement

---

## Méthode 2 : IP Webcam (Android uniquement) 📹

### Avantages
- ✅ Plus de contrôles (résolution, FPS, zoom)
- ✅ Gratuit et open source
- ✅ Stable et performant

### Installation

1. Téléchargez [IP Webcam](https://play.google.com/store/apps/details?id=com.pas.webcam) depuis Google Play
2. Lancez l'application
3. Scrollez vers le bas et appuyez sur **"Démarrer le serveur"**
4. **Notez l'adresse IP affichée** (ex: `http://192.168.1.100:8080`)

http://192.168.137.27:8080/video

### Configuration dans GestionBoutique

1. Ouvrez **GestionBoutique**
2. Allez dans **Menu > Paramètres > Paramètres Caisse**
3. Dans **"Source caméra"**, entrez : `http://192.168.1.100:8080/video`
   - Remplacez par votre IP
4. Cliquez sur **"Tester"**
5. **"Enregistrer"**

### Options Avancées IP Webcam

Dans l'app mobile, vous pouvez configurer :
- **Résolution** : Recommandé 640x480 ou 800x600 (meilleur compromis qualité/latence)
- **Qualité** : 70-80% (économie bande passante)
- **FPS** : 15-30 (30 pour scan fluide)
- **Focus** : Auto ou Manual
- **Zoom** : Utile pour scanner des petits codes

---

## Méthode 3 : Webcam USB Externe

Si vous avez une deuxième webcam USB branchée sur le PC :

1. Dans **"Source caméra"**, entrez : `1`
   - `0` = webcam par défaut
   - `1` = 2ème webcam
   - `2` = 3ème webcam, etc.
2. Cliquez sur **"Tester"**
3. **"Enregistrer"**

---

## Dépannage 🔧

### Erreur : "Impossible de se connecter à la caméra"

#### Vérifiez le réseau
- ✅ Le PC et le téléphone sont sur le **même réseau WiFi**
- ✅ L'app mobile est **lancée et active**
- ✅ L'adresse IP est **correcte** (elle peut changer après redémarrage WiFi)

#### Vérifiez l'URL
- Format correct : `http://IP:PORT/video`
- Exemples valides :
  - `http://192.168.1.100:4747/video` (DroidCam)
  - `http://192.168.1.100:8080/video` (IP Webcam)
- ⚠️ Ne pas oublier `/video` à la fin !

#### Testez dans un navigateur
- Ouvrez un navigateur sur le PC
- Allez sur `http://IP:PORT` (sans `/video`)
- Si vous voyez l'interface de l'app, le serveur fonctionne
- Si vous ne voyez rien, problème réseau/firewall

### Erreur : "Caméra trouvée mais impossible de lire les images"

- La caméra est utilisée par une autre application
- Fermez les autres apps qui utilisent la caméra :
  - Zoom, Teams, Skype
  - Autres instances de GestionBoutique
  - OBS Studio, etc.

### La vidéo est lente/saccadée

- **Réduisez la résolution** dans l'app mobile (recommandé : 640x480)
- **Réduisez le FPS** (15-20 suffit pour scanner)
- Vérifiez la qualité du WiFi (signal fort)
- Rapprochez le téléphone du routeur WiFi

### L'IP change souvent

**Solution** : Configurer une IP statique pour le téléphone dans le routeur WiFi
1. Accédez à l'interface du routeur (ex: `192.168.1.1`)
2. Cherchez "DHCP" ou "Adresses statiques"
3. Assignez une IP fixe au téléphone (ex: `192.168.1.150`)

---

## Conseils d'Utilisation 💡

### Positionnement du Téléphone
- Utilisez un **support** ou un **trépied** pour stabiliser le téléphone
- Positionnez à environ **20-30cm** des codes-barres
- Éclairage : Évitez les reflets et ombres

### Économie de Batterie
- Branchez le téléphone sur secteur pendant l'utilisation
- DroidCam/IP Webcam consomment beaucoup de batterie

### Sécurité Réseau
- Ces apps créent un serveur HTTP **non sécurisé** (pas HTTPS)
- ⚠️ **Utilisez UNIQUEMENT sur réseau local privé**
- Ne jamais exposer à Internet (pas de port forwarding)

---

## Comparaison des Solutions

| Critère | DroidCam | IP Webcam | Webcam USB |
|---------|----------|-----------|------------|
| **OS** | Android + iOS | Android | Windows/Linux |
| **Prix** | Gratuit | Gratuit | 15-50€ |
| **Qualité** | Excellente | Excellente | Variable |
| **Latence** | Faible | Très faible | Aucune |
| **Configuration** | Simple | Simple | Plug & Play |
| **Mobilité** | Haute | Haute | Limitée (câble) |

---

## Exemple de Configuration Complète

### Scénario : Boutique avec 2 caisses

**Caisse 1** : PC avec webcam intégrée
- Source caméra : `0`

**Caisse 2** : PC portable sans webcam
- Téléphone Android avec IP Webcam
- IP fixe assignée : `192.168.1.150`
- Source caméra : `http://192.168.1.150:8080/video`
- Téléphone monté sur support ajustable

---

## Support Technique

Si vous rencontrez des problèmes :
1. Vérifiez ce guide de dépannage
2. Testez avec le bouton **"Tester"** dans les préférences
3. Vérifiez les logs de l'application

---

## Notes Techniques

### URLs Supportées par OpenCV

GestionBoutique utilise OpenCV pour lire les flux vidéo. Formats supportés :
- `0`, `1`, `2` : Webcams USB (index)
- `http://IP:PORT/video` : MJPEG stream
- `rtsp://IP:PORT/stream` : RTSP stream (certaines caméras IP)

### Codecs Vidéo
- DroidCam : MJPEG (Motion JPEG)
- IP Webcam : MJPEG, H.264 (utiliser MJPEG pour GestionBoutique)

### Bande Passante
- Résolution 640x480 @ 30 FPS ≈ 3-5 Mbps
- Résolution 800x600 @ 15 FPS ≈ 2-3 Mbps
- WiFi 2.4GHz suffit largement

---

**Dernière mise à jour** : 2026-02-08
