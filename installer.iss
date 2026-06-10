#define VersionFileHandle FileOpen("version.txt")
#define MyAppVersion Trim(FileRead(VersionFileHandle))
#expr FileClose(VersionFileHandle)

[Setup]
AppId={{8E7A5D1D-7D5A-4E1E-9B7D-3C2F6E1A9B11}
AppName=SortMyPhotos

AppVersion={#MyAppVersion}
AppVerName=SortMyPhotos {#MyAppVersion}
DefaultDirName={autopf}\SortMyPhotos
DefaultGroupName=SortMyPhotos
DisableProgramGroupPage=yes
OutputDir=installer_output
OutputBaseFilename=SortMyPhotos_{#MyAppVersion}_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
UninstallDisplayName=SortMyPhotos
UninstallDisplayIcon={app}\SortMyPhotos.exe

[Files]
Source: "D:\SortMyPhotos\dist\SortMyPhotos.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\SortMyPhotos"; Filename: "{app}\SortMyPhotos.exe"; WorkingDir: "{app}"
Name: "{autodesktop}\SortMyPhotos"; Filename: "{app}\SortMyPhotos.exe"; Tasks: desktopicon; WorkingDir: "{app}"

[Tasks]
Name: "desktopicon"; Description: "Vytvořit ikonu na ploše"; GroupDescription: "Další možnosti:"

[Run]
Filename: "{app}\SortMyPhotos.exe"; Description: "Spustit SortMyPhotos"; Flags: nowait postinstall skipifsilent