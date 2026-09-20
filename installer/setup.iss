; Voice-to-Text Windows 11 — Inno Setup Script
; Generated automatically by build_installer.py

#define AppName "Voice-to-Text Windows"
#define AppVersion "2.1.0"
#define AppPublisher "Mostafa Afrouzi"
#define AppURL "https://github.com/mostafaafrouzi/Voice-to-Text-Windows"
#define AppExeName "VoiceToText.exe"
#define AppGUID "8E7F3A2C-4B6D-11ED-A82E-0050568E1C8E"

[Setup]
AppId={{{#AppGUID}}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} v{#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}/issues
AppUpdatesURL={#AppURL}/releases
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
AllowNoIcons=yes
LicenseFile=
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=..\dist
OutputBaseFilename=VoiceToText-Setup-v{#AppVersion}
SetupIconFile=..\assets\icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
WizardResizable=no
ShowLanguageDialog=no
LanguageDetectionMethod=none
DisableWelcomePage=no
DisableDirPage=no
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\{#AppExeName}
UninstallDisplayName={#AppName} v{#AppVersion}
MinVersion=10.0
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes
CloseApplicationsFilter=*{#AppExeName}
RestartApplications=no
ChangesEnvironment=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"
Name: "startupentry"; Description: "Start &automatically with Windows"; GroupDescription: "System integration:"

[Files]
Source: "..\dist\VoiceToText\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\{#AppExeName}"; Comment: "Voice-to-Text Windows 11"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon; IconFilename: "{app}\{#AppExeName}"; Comment: "Voice-to-Text Windows 11"

[Registry]
; Startup entry (if user selected it during install)
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "VoiceToTextWindows"; ValueData: """{app}\{#AppExeName}"""; Tasks: startupentry; Flags: uninsdeletevalue
Root: HKCU; Subkey: "Software\{#AppPublisher}\{#AppName}"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\{#AppPublisher}\{#AppName}"; ValueType: string; ValueName: "Version"; ValueData: "{#AppVersion}"

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent unchecked

[UninstallRun]
Filename: "{sys}\taskkill.exe"; Parameters: "/F /IM {#AppExeName}"; Flags: runhidden; RunOnceId: "KillVoiceToText"

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
end;
