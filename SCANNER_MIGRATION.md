# Migration du Scanner Caméra

## Problème

`modules/scanner_camera.py` utilisait Tkinter → incompatible avec PySide6.

## Solution

Créé **`ui/components/scanner_camera.py`** (version PySide6)

### Changements

#### 1. Nouveau composant Qt
```python
# ui/components/scanner_camera.py
class ScannerCameraDialog(QDialog):
    - Utilise QLabel pour le feed vidéo
    - QTimer pour lire les frames
    - QImage/QPixmap pour convertir OpenCV → Qt
    - Dialog modal
```

#### 2. Mise à jour de ventes.py
```python
# Avant (Tkinter)
from modules.scanner_camera import ScannerCamera
ScannerCamera(self, callback)

# Après (PySide6)
from ui.components.scanner_camera import ScannerCameraDialog
dlg = ScannerCameraDialog(callback, parent=self)
dlg.exec()
```

#### 3. Ancien module conservé
`modules/scanner_camera.py` reste pour compatibilité avec `main_tkinter_backup.py`

## Fonctionnalités

✅ Détection code-barres en temps réel (OpenCV + pyzbar)
✅ Affichage vidéo 30 FPS
✅ Rectangle vert autour du code détecté
✅ Fermeture automatique après scan
✅ Callback avec le code scanné

## Dépendances

```bash
pip install opencv-python pyzbar
```

## Architecture

```
modules/scanner_camera.py     # Tkinter (ancien, backup)
ui/components/scanner_camera.py  # PySide6 (actif)
ui/windows/ventes.py          # Utilise la version Qt
```

## Test

```python
from ui.components.scanner_camera import ScannerCameraDialog

def on_scan(code):
    print(f"Code scanné: {code}")

dlg = ScannerCameraDialog(on_scan)
dlg.exec()
```

---

**Migration terminée** ✅ Le scanner fonctionne maintenant avec PySide6 !
