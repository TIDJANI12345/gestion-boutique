# Plan Scanner Mobile - Caméra Téléphone

## Vue d'ensemble
Permettre l'utilisation de la caméra du téléphone pour scanner des codes-barres dans GestionBoutique.
Deux solutions complémentaires : **A) Multi-source caméra** (immédiat) et **B) Web App mobile** (pro).

---

## PHASE A : Configuration Multi-Source Caméra ⚡ (PRIORITÉ)

### Objectif
Permettre de configurer la source vidéo OpenCV pour utiliser :
- Webcam PC (par défaut) : `0`
- DroidCam/IP Webcam : `http://192.168.1.X:8080/video`
- Autre webcam USB : `1`, `2`, etc.

### Fichiers à Modifier

#### 1. `database.py` - Nouveau paramètre
Ajouter paramètre par défaut : `camera_source` = `"0"`

#### 2. `ui/windows/preferences_caisse.py` - UI Config
Ajouter section "Scanner Caméra" :
- Label : "Source caméra"
- QLineEdit pour entrer : `0`, `1`, ou `http://IP:PORT/video`
- Bouton "Tester" pour vérifier la connexion
- Info bulle explicative

#### 3. `ui/components/camera_widget.py` - Lecture paramètre
```python
# Ligne 90 : Remplacer
self.cap = cv2.VideoCapture(0)

# Par
source = self._get_camera_source()
self.cap = cv2.VideoCapture(source)
```

Ajouter méthode `_get_camera_source()` :
- Lire `db.get_parametre('camera_source', '0')`
- Convertir en int si numérique, sinon retourner string (URL)

#### 4. `ui/components/scanner_camera.py` - Idem
Même modification ligne 91

#### 5. Documentation utilisateur
Créer `SCANNER_MOBILE_GUIDE.md` :
- Installation DroidCam (Android/iOS)
- Installation IP Webcam (Android)
- Configuration dans GestionBoutique
- Dépannage (firewall, WiFi)

### Tests
- [ ] Webcam PC (source = `0`)
- [ ] DroidCam sur réseau local
- [ ] IP Webcam sur réseau local
- [ ] Erreur si source invalide (message clair)
- [ ] Sauvegarde/restauration config

### Durée Estimée
30 minutes

---

## PHASE B : Web App Mobile + WebSocket 🚀 (APRÈS PHASE A)

### Objectif
Application web progressive (PWA) qui scanne depuis le mobile et envoie via WebSocket.
Pas d'installation d'app nécessaire, fonctionne iOS + Android.

### Architecture
```
┌─────────────────┐         WebSocket          ┌──────────────────┐
│  Mobile Browser │ ────────────────────────► │  GestionBoutique │
│   (ZXing JS)    │   ws://192.168.1.X:8765    │   (serveur WS)   │
└─────────────────┘                            └──────────────────┘
         │                                              │
         │ Scanne QR/Barcode                            │ Émet signal Qt
         └─────────────────────────────────────────────┘
                    Injecte code dans fenêtre vente
```

### Fichiers à Créer

#### 1. `modules/scanner_mobile_server.py`
**Serveur WebSocket intégré**
```python
class ScannerMobileServer(QThread):
    code_recu = Signal(str)

    def __init__(self):
        # Serveur WebSocket asyncio dans thread
        # Port : 8765 (configurable)
        # Protocole : {"type": "scan", "code": "1234567890"}

    def run(self):
        # asyncio.run(websocket.serve(...))

    def arreter(self):
        # Cleanup
```

Dépendance : `websockets` (ajouter à requirements.txt)

#### 2. `ui/resources/scanner_mobile.html`
**Page web mobile**
```html
<!DOCTYPE html>
<html>
<head>
    <title>Scanner Mobile - GestionBoutique</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://unpkg.com/@zxing/library@latest"></script>
</head>
<body>
    <div id="scanner-container">
        <video id="video"></video>
        <div id="status">Connexion...</div>
    </div>
    <script>
        // ZXing scanner
        // WebSocket vers ws://HOST:8765
        // Envoie JSON : {"type": "scan", "code": "..."}
    </script>
</body>
</html>
```

#### 3. `modules/scanner_mobile_http.py`
**Mini serveur HTTP pour servir la page**
```python
class ScannerMobileHTTP(QThread):
    def __init__(self, port=8080):
        # Serveur HTTP simple (http.server)
        # Sert scanner_mobile.html sur http://IP:8080
```

#### 4. `ui/windows/scanner_mobile_setup.py`
**Dialog de configuration**
- QR code pour connexion mobile (génère URL + encode en QR)
- Affiche : `http://192.168.1.X:8080`
- Liste des téléphones connectés (WebSocket clients)
- Bouton Start/Stop serveur
- LED de statut (vert = actif, rouge = arrêté)

#### 5. Intégration dans `ui/windows/ventes.py`
**Démarrage automatique du serveur**
```python
def __init__(self):
    # ...
    self.scanner_server = None
    if db.get_parametre('scanner_mobile_auto', '0') == '1':
        self._start_scanner_mobile()

def _start_scanner_mobile(self):
    self.scanner_server = ScannerMobileServer()
    self.scanner_server.code_recu.connect(self._traiter_code_barre)
    self.scanner_server.start()
```

#### 6. Menu dans `ui/windows/principale.py`
Ajouter menu "Outils" > "Scanner Mobile" :
- "Configurer Scanner Mobile..." → Ouvre dialog setup
- "Démarrer Serveur Scanner" → Start/Stop
- "QR Code de Connexion" → Affiche QR

### Nouvelles Dépendances
```txt
websockets>=12.0
qrcode>=7.4.2
```

### Sécurité
- WebSocket sans auth (réseau local uniquement)
- Vérifier IP client (bloquer si hors réseau local)
- Rate limiting (max 10 scans/seconde par client)
- CORS configuré pour localhost uniquement

### Fonctionnalités Avancées (v2)
- [ ] Multi-téléphones simultanés (plusieurs caissiers)
- [ ] Vibration mobile au scan réussi
- [ ] Son de confirmation
- [ ] Historique des scans (log)
- [ ] Auto-reconnexion si déconnexion
- [ ] PWA installable (manifest.json)
- [ ] Mode sombre/clair
- [ ] Affichage produit scanné sur mobile (feedback)

### Tests
- [ ] Connexion WebSocket depuis mobile
- [ ] Scan et réception côté PC
- [ ] Déconnexion/reconnexion
- [ ] Multi-clients
- [ ] Erreur réseau (WiFi coupé)
- [ ] QR code valide
- [ ] Serveur HTTP accessible
- [ ] Compatible iOS Safari + Android Chrome

### Durée Estimée
2 heures (base) + 1 heure (polish)

---

## PHASE C : Améliorations Futures (Optionnel)

### Serveur Cloud (pour accès externe)
- Tunnel ngrok/cloudflared pour scanner hors réseau local
- Authentification par token
- HTTPS obligatoire

### App Mobile Native (si nécessaire)
- React Native ou Flutter
- Scan optimisé (MLKit, ZXing native)
- Notifications push
- Mode offline + sync

### Dashboard de monitoring
- Statistiques de scan
- Performance par caissier
- Erreurs de scan (codes invalides)

---

## Prérequis Utilisateurs

### Pour Phase A (DroidCam)
1. Installer DroidCam sur Android/iOS
2. Connecter téléphone + PC au même WiFi
3. Noter l'IP affichée dans l'app
4. Configurer dans GestionBoutique : Préférences > Scanner Caméra

### Pour Phase B (Web App)
1. Démarrer serveur dans GestionBoutique
2. Scanner QR code affiché
3. Autoriser caméra dans le navigateur mobile
4. Commencer à scanner

---

## Notes Techniques

### OpenCV Sources Supportées
```python
cv2.VideoCapture(0)                          # Webcam par défaut
cv2.VideoCapture(1)                          # 2ème webcam
cv2.VideoCapture("http://IP:8080/video")     # MJPEG stream
cv2.VideoCapture("rtsp://IP:554/stream")     # RTSP stream
```

### Format WebSocket
```json
{
  "type": "scan",
  "code": "1234567890123",
  "format": "EAN13",
  "timestamp": 1677123456789
}
```

### QR Code de Connexion
Contenu : `http://192.168.1.X:8080?id=UNIQUE_ID`
- L'ID permet d'identifier le client
- Généré aléatoirement à chaque démarrage

---

## Checklist Finale

### Phase A
- [ ] Paramètre `camera_source` en DB
- [ ] UI config dans Préférences
- [ ] Lecture paramètre dans widgets
- [ ] Bouton "Tester caméra"
- [ ] Documentation utilisateur
- [ ] Tests avec DroidCam/IP Webcam

### Phase B
- [ ] Module `scanner_mobile_server.py`
- [ ] Page HTML + ZXing
- [ ] Serveur HTTP pour page
- [ ] Dialog de setup avec QR
- [ ] Intégration dans fenêtre ventes
- [ ] Menu dans dashboard
- [ ] Dépendances installées
- [ ] Tests multi-devices
- [ ] Documentation

---

**Statut :** Phase A en cours
**Début :** 2026-02-08
