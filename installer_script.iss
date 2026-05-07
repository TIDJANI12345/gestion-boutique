[Setup]
AppId={{B3F7A2E1-5C4D-4E8F-9A1B-2D3E4F5A6B7C}
AppName=HishamPOS
AppVersion=2.5.0
AppVerName=HishamPOS 2.5.0
AppPublisher=TIDJANI
AppPublisherURL=https://github.com/TIDJANI12345/gestion-boutique
DefaultDirName={autopf}\HishamPOS
DefaultGroupName=HishamPOS
OutputDir=output
OutputBaseFilename=HishamPOS_Setup_v2.5.0
Compression=lzma
SolidCompression=yes
WizardStyle=modern
SetupIconFile=logo.ico
UninstallDisplayIcon={app}\logo.ico
PrivilegesRequired=lowest

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "Créer un raccourci sur le bureau"; GroupDescription: "Raccourcis:"; Flags: unchecked

[Dirs]
; L'application cree ces dossiers automatiquement dans %APPDATA%
; Pas besoin de les creer ici

[Files]
; Fichier exécutable principal et dépendances
Source: "dist\HishamPOS\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; NE PAS copier data/ - l'application cree la base de donnees au premier lancement
; NE PAS copier recus/ exports/ - crees automatiquement dans %APPDATA%

; Images produits optionnelles (si elles existent)
Source: "images\*"; DestDir: "{app}\images"; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist

[Icons]
Name: "{group}\HishamPOS"; Filename: "{app}\HishamPOS.exe"; IconFilename: "{app}\logo.ico"
Name: "{autodesktop}\HishamPOS"; Filename: "{app}\HishamPOS.exe"; Tasks: desktopicon; IconFilename: "{app}\logo.ico"
Name: "{group}\Désinstaller HishamPOS"; Filename: "{uninstallexe}"; IconFilename: "{app}\logo.ico"

[Run]
Filename: "{app}\HishamPOS.exe"; Description: "Lancer HishamPOS"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\data"
Type: filesandordirs; Name: "{app}\recus"
Type: filesandordirs; Name: "{app}\exports"
Type: filesandordirs; Name: "{app}\images"
