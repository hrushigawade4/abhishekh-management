#define AppName "Abhishek Manager"
#define AppExe  "AbhishekManager.exe"
#define AppVer  "1.0.0"

[Setup]
AppId={{17adab5b-8a1a-4fc1-86f1-40a8870e8896}}   ; generate your own GUID and keep stable for updates
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
; Single EXE from PyInstaller
Source: "dist\{#AppExe}"; DestDir: "{app}"; Flags: ignoreversion

; (Optional) If you used --onedir and want to ship the whole folder:
; Source: "dist\AbhishekManager\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Optional: include VC++ Redistributable and run silently on install (uncomment if you add the file)
; Source: "vc_redist.x64.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"; WorkingDir:"{app}"
Name: "{commondesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon; WorkingDir:"{app}"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"; Flags: unchecked

[Run]
; If including VC++ redistributable, install it first (example)
; Filename: "{tmp}\vc_redist.x64.exe"; Parameters: "/install /passive /norestart"; StatusMsg: "Installing Visual C++ Redistributable..."
Filename: "{app}\{#AppExe}"; Description:"Launch {#AppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Keep %APPDATA% DB untouched; do NOT delete DB in AppData
