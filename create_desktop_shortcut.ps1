<#
create_desktop_shortcut.ps1

Usage: Run this script from the repository folder (where `setup_and_run.bat` lives).
It will create a shortcut on the current user's Desktop named "Run Miro Uploader.lnk"
that launches `setup_and_run.bat` (works whether the venv is activated or not).

Run in PowerShell (if execution policy prevents running, run as Administrator or use
`Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned -Force` once).
#>

try {
    $psScriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
} catch {
    # fallback to current directory
    $psScriptPath = (Get-Location).Path
}

$targetBat = Join-Path -Path $psScriptPath -ChildPath 'setup_and_run.bat'
if (-not (Test-Path -LiteralPath $targetBat)) {
    Write-Error "setup_and_run.bat not found at $targetBat. Run this script from the repository folder."
    exit 1
}

$desktop = [Environment]::GetFolderPath('Desktop')
$lnkPath = Join-Path -Path $desktop -ChildPath 'Run Miro Uploader.lnk'

$wsh = New-Object -ComObject WScript.Shell
$shortcut = $wsh.CreateShortcut($lnkPath)

# Use cmd.exe to run the batch file so the .bat runs in a console window.
$shortcut.TargetPath = "$env:windir\System32\cmd.exe"
$shortcut.Arguments = "/c `"$targetBat`""
$shortcut.WorkingDirectory = $psScriptPath
# Optional: set an icon if desired (use the batch file as icon placeholder)
$shortcut.IconLocation = "$targetBat,0"
$shortcut.Description = 'Shortcut to run the Miro image uploader setup script'
$shortcut.Save()

Write-Host "Shortcut created at: $lnkPath"
exit 0
