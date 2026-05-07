# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[
        ('C:\\Users\\hp\\AppData\\Local\\Programs\\Python\\Python311\\Lib\\site-packages\\pyzbar\\libiconv.dll', 'pyzbar'),
        ('C:\\Users\\hp\\AppData\\Local\\Programs\\Python\\Python311\\Lib\\site-packages\\pyzbar\\libzbar-64.dll', 'pyzbar'),
    ],
    datas=[
        ('ui/resources', 'ui/resources'),
        ('images', 'images'),
    ],
    hiddenimports=[
        # Qt
        'PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets',
        'PySide6.QtMultimedia', 'PySide6.QtPrintSupport',
        # Barcode / camera
        'cv2', 'pyzbar', 'pyzbar.pyzbar',
        # Crypto (feature flags)
        'cryptography', 'cryptography.fernet',
        'cryptography.hazmat.primitives', 'cryptography.hazmat.backends',
        # Printer
        'escpos', 'usb', 'serial',
        # PDF
        'reportlab', 'reportlab.pdfgen', 'reportlab.lib',
        # Network (local API + client)
        'flask', 'requests',
        # Misc
        'bcrypt', 'platformdirs', 'asyncio',
        # Business modules
        'modules.ventes', 'modules.produits', 'modules.clients',
        'modules.utilisateurs', 'modules.permissions', 'modules.paiements',
        'modules.recus', 'modules.rapports', 'modules.fiscalite',
        'modules.imprimante', 'modules.sauvegarde', 'modules.licence',
        'modules.features', 'modules.sessions', 'modules.ardoise',
        'modules.import_csv', 'modules.logger',
        'modules.reseau', 'modules.client_reseau',
        'serveur_local.api_locale', 'serveur_local.discovery',
        # UI windows
        'ui.windows.ventes', 'ui.windows.paiement',
        'ui.windows.principale', 'ui.windows.principale_gestionnaire',
        'ui.windows.principale_caissier', 'ui.windows.produits',
        'ui.windows.ardoise', 'ui.windows.annulation_vente',
        'ui.windows.import_csv', 'ui.windows.sauvegarde',
        'ui.windows.confirmation_vente', 'ui.windows.config_reseau',
        # UI dialogs
        'ui.dialogs.ouverture_caisse', 'ui.dialogs.cloture_z',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter', 'ttkthemes', '_tkinter', 'Tkinter',
        'websockets',
        'modules.scanner_mobile_server', 'modules.scanner_mobile_http',
    ],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='HishamPOS',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='images/logo_boutique.png',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='HishamPOS',
)
