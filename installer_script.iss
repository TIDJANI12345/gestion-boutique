[Setup]
AppName=Gestion Boutique
AppVersion=2.0.0
AppPublisher=Votre Entreprise
AppPublisherURL=https://www.votresite.bj
DefaultDirName={autopf}\GestionBoutique
DefaultGroupName=Gestion Boutique
OutputDir=output
OutputBaseFilename=GestionBoutique_Setup_v2.0.0
Compression=lzma
SolidCompression=yes
WizardStyle=modern
SetupIconFile=logo.ico
UninstallDisplayIcon={app}\logo.ico
PrivilegesRequired=admin

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
Source: "dist\GestionBoutique.exe"; DestDir: "{app}"; Flags: ignoreversion

; Fichiers de base
Source: "logo.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "logo.png"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.txt"; DestDir: "{app}"; Flags: ignoreversion isreadme

; Gestion des données (Base de données et licence)
Source: "data\*"; DestDir: "{app}\data"; Flags: ignoreversion recursesubdirs createallsubdirs

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