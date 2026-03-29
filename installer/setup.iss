; EcoNodeX — Inno Setup script
; Requires: PyInstaller dist/EcoNodeX/ folder already built

#define MyAppName "EcoNodeX"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "EcoNodeX Project"
#define MyAppExeName "EcoNodeX.exe"
#define MyAppDir "..\dist\EcoNodeX"

[Setup]
AppId={{8F3E2A4D-1B7C-4F9E-A234-5E6D7B8C9F0A}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=..\dist\installer
OutputBaseFilename=EcoNodeX_Setup_v{#MyAppVersion}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}
PrivilegesRequired=lowest

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear icono en el escritorio"; GroupDescription: "Iconos adicionales:"; Flags: unchecked

[Files]
Source: "{#MyAppDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}";      Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Desinstalar";       Filename: "{uninstallexe}"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Iniciar {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Leave user data intact; only remove app files
