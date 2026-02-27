@echo off
rem setup_and_run.bat
rem Prompts for MIRO_BOARD_ID and WATCH_FOLDER, updates .env, activates venv and runs the uploader.
setlocal enabledelayedexpansion

echo This script will update the `.env` file with MIRO_BOARD_ID and WATCH_FOLDER, then run the uploader.

set /p MIRO_BOARD_ID=Enter MIRO_BOARD_ID: 
if "%MIRO_BOARD_ID%"=="" (
  echo No MIRO_BOARD_ID provided. Exiting.
  goto :EOF
)

set /p WATCH_FOLDER=Enter WATCH_FOLDER (use forward slashes, e.g. C:/path/to/folder): 
if "%WATCH_FOLDER%"=="" (
  echo No WATCH_FOLDER provided. Exiting.
  goto :EOF
)

rem Check if folder exists (use PowerShell which understands both slash styles)
powershell -NoProfile -Command "if (-not (Test-Path -Path '%WATCH_FOLDER%')) { exit 2 } else { exit 0 }"
if errorlevel 2 (
  echo Folder '%WATCH_FOLDER%' does not exist.
  set /p createFolder=Do you want to create it? [Y/N]: 
  if /I "%createFolder%"=="Y" (
    powershell -NoProfile -Command "New-Item -ItemType Directory -Path '%WATCH_FOLDER%' | Out-Null"
    if errorlevel 1 (
      echo Failed to create folder '%WATCH_FOLDER%'. Exiting.
      goto :EOF
    )
  ) else (
    echo Exiting.
    goto :EOF
  )
)

rem Resolve path to .env in the script folder
set "SCRIPT_DIR=%~dp0"
set "ENV_FILE=%SCRIPT_DIR%.env"
if not exist "%ENV_FILE%" (
  echo .env file not found at "%ENV_FILE%". Exiting.
  goto :EOF
)

rem Use PowerShell to safely replace the MIRO_BOARD_ID and WATCH_FOLDER lines (preserve other content)
powershell -NoProfile -Command ^
  "$envPath = Resolve-Path -LiteralPath '%ENV_FILE%';" ^
  "$content = Get-Content -Raw -LiteralPath $envPath;" ^
  "$content = $content -replace 'MIRO_BOARD_ID=".*?"','MIRO_BOARD_ID="%MIRO_BOARD_ID%"';" ^
  "$content = $content -replace 'WATCH_FOLDER=".*?"','WATCH_FOLDER="%WATCH_FOLDER%"';" ^
  "Set-Content -LiteralPath $envPath -Value $content -Encoding UTF8;"
if errorlevel 1 (
  echo Failed to update %ENV_FILE%. Exiting.
  goto :EOF
)

echo Updated %ENV_FILE% with:
echo   MIRO_BOARD_ID="%MIRO_BOARD_ID%"
echo   WATCH_FOLDER="%WATCH_FOLDER%"

rem Activate the virtual environment if present, else continue with system Python
if exist "%SCRIPT_DIR%miro-sync-env\Scripts\activate.bat" (
  echo Activating virtual environment...
  call "%SCRIPT_DIR%miro-sync-env\Scripts\activate.bat"
  if errorlevel 1 echo Warning: activation returned non-zero code; continuing.
) else (
  echo Virtual environment not found at "%SCRIPT_DIR%miro-sync-env\Scripts\activate.bat". Using system Python.
)

echo Running the uploader (logs printed to console)...
python "%SCRIPT_DIR%miro_image_uploader.py" %*

endlocal

:EOF
exit /b 0
