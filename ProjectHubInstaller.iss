[Setup]
AppName=ProjectHub
AppVersion=1.0.0
DefaultDirName={commonpf64}\ProjectHub
DefaultGroupName=ProjectHub
OutputBaseFilename=ProjectHubSetup
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin
SetupIconFile=computer.ico
UninstallDisplayIcon={app}\ProjectHub.exe

[Files]
Source: "dist\ProjectHub.exe"; DestDir: "{app}"
Source: "computer.ico"; DestDir: "{app}"

[Icons]
Name: "{commonprograms}\ProjectHub"; Filename: "{app}\ProjectHub.exe"; IconFilename: "{app}\computer.ico"
Name: "{userdesktop}\ProjectHub"; Filename: "{app}\ProjectHub.exe"; IconFilename: "{app}\computer.ico"

[Run]
Filename: "{app}\ProjectHub.exe"; Description: "Launch ProjectHub"; Flags: nowait postinstall skipifsilent
