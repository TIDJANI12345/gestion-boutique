@echo off
echo ================================================
echo   BUILD GESTION BOUTIQUE v2.0
echo ================================================
echo.

REM Nettoyer anciens builds
echo [1/4] Nettoyage...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist __pycache__ rmdir /s /q __pycache__

REM Installer dependencies
echo [2/4] Installation dependances...
pip install -r requirements.txt --quiet

REM Build avec PyInstaller
echo [3/4] Compilation avec PyInstaller...
pyinstaller --clean --noconfirm GestionBoutique.spec

REM Copier fichiers necessaires
echo [4/4] Copie fichiers...
if exist dist\GestionBoutique (
    copy logo.ico dist\GestionBoutique\ >nul 2>&1
    copy logo.png dist\GestionBoutique\ >nul 2>&1
    REM Ne PAS copier data/ - l'app cree la DB au premier lancement
    REM Copier seulement les images produits (optionnel)
    if exist images (
        xcopy /E /I /Y images dist\GestionBoutique\images >nul 2>&1
    )
)

echo.
echo ================================================
echo   BUILD TERMINE TRES CHER HISHAM !
echo   Executable: dist\GestionBoutique\GestionBoutique.exe
echo ================================================
pause