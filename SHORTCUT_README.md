# Desktop Shortcut for Miro Uploader

This repository includes a helper PowerShell script `create_desktop_shortcut.ps1` that creates a Desktop shortcut named "Run Miro Uploader.lnk" which launches `setup_and_run.bat`.

How to use

1. Open PowerShell and change to the repository folder where `setup_and_run.bat` and `create_desktop_shortcut.ps1` live:

```powershell
cd 'C:\BT-DTC\CODE\MiroREST_API\Miro_REST_API_101'
.
```

2. Run the script (you may need to allow script execution once):

```powershell
.\create_desktop_shortcut.ps1
```

What it does

- Verifies `setup_and_run.bat` exists in the same folder.
- Creates a `.lnk` on your Desktop that runs `cmd.exe /c "<path>\setup_and_run.bat"` so the batch runs in a console window.

Notes

- The `setup_and_run.bat` already activates the repository virtualenv (`miro-sync-env`) if present. The shortcut simply runs the batch; the batch will handle active/inactive virtualenvs.
- If PowerShell's execution policy blocks running the script, run PowerShell as Administrator and run:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned -Force
```

- You can place the resulting shortcut in another location (e.g., the Startup folder) manually if you want it to run on boot.
