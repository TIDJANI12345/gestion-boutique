[Setup]
AppId={{B3F7A2E1-5C4D-4E8F-9A1B-2D3E4F5A6B7C}
AppName=Gestion Boutique
AppVersion=2.0.0
AppVerName=Gestion Boutique 2.0.0
AppPublisher=TIDJANI
AppPublisherURL=https://github.com/TIDJANI12345/gestion-boutique
DefaultDirName={autopf}\GestionBoutique
DefaultGroupName=Gestion Boutique
OutputDir=output
OutputBaseFilename=GestionBoutique_Setup_v2.0.0
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
; On s'assure que les dossiers existent, même s'ils sont vides
Name: "{app}\images"
Name: "{app}\exports"
Name: "{app}\recus"
Name: "{app}\data"

[Files]
; Fichier exécutable principal
Source: "dist\gestionboutique.exe"; DestDir: "{app}"; DestName: "GestionBoutique.exe"; Flags: ignoreversion

; Fichiers de base
Source: "logo.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "logo.png"; DestDir: "{app}"; Flags: ignoreversion

; Gestion des données (Base de données et licence)
Source: "data\*"; DestDir: "{app}\data"; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist

; Utilisation du flag 'skipifsourcedoesntexist' pour éviter les erreurs de compilation si vide
Source: "images\*"; DestDir: "{app}\images"; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist
Source: "exports\*"; DestDir: "{app}\exports"; Flags: ignoreversion recursesubdirs createallsubdirs onlyifdoesntexist skipifsourcedoesntexist
Source: "recus\*"; DestDir: "{app}\recus"; Flags: ignoreversion recursesubdirs createallsubdirs onlyifdoesntexist skipifsourcedoesntexist

[Icons]
Name: "{group}\Gestion Boutique"; Filename: "{app}\GestionBoutique.exe"; IconFilename: "{app}\logo.ico"
Name: "{autodesktop}\Gestion Boutique"; Filename: "{app}\GestionBoutique.exe"; Tasks: desktopicon; IconFilename: "{app}\logo.ico"
Name: "{group}\Désinstaller Gestion Boutique"; Filename: "{uninstallexe}"; IconFilename: "{app}\logo.ico"

[Run]
Filename: "{app}\GestionBoutique.exe"; Description: "Lancer Gestion Boutique"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\data"
Type: filesandordirs; Name: "{app}\recus"
Type: filesandordirs; Name: "{app}\exports"
Type: filesandordirs; Name: "{app}\images"