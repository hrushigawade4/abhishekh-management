#define AppName "Abhishek Manager"
#define AppExe  "AbhishekManager.exe"
#define AppVer  "1.0.0"

[Setup]
AppId={{17adab5b-8a1a-4fc1-86f1-40a8870e8896}}
AppName={#AppName}
AppVersion={#AppVer}
DefaultDirName={pf}\AbhishekManager
DefaultGroupName=Abhishek Manager
OutputBaseFilename=AbhishekManagerSetup_{#AppVer}
OutputDir=.
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
DisableDirPage=no
DisableProgramGroupPage=no
SetupIconFile=icon.ico

[Files]
Source: "dist\{#AppExe}"; DestDir: "{app}"; Flags: ignoreversion
; Removed database file, only EXE is included

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"; WorkingDir:"{app}"
Name: "{commondesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon; WorkingDir:"{app}"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"; Flags: unchecked

[Run]
Filename: "{app}\{#AppExe}"; Description:"Launch {#AppName}"; Flags: nowait postinstall skipifsilent
