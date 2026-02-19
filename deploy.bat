@echo off
setlocal

:: ==============================================
:: Deployment script for Raspberry Pi (Windows)
:: ==============================================

:: Configuration - modify these values
set PI_USER=kelly
set PI_HOST=raspberrypi.local
set PI_DEST=/home/kelly/development/home_assistant

:: Get script directory
set SCRIPT_DIR=%~dp0

echo Deploying src to %PI_USER%@%PI_HOST%:%PI_DEST%

:: Create destination directory on Pi
ssh %PI_USER%@%PI_HOST% "mkdir -p %PI_DEST%/src"

:: Copy src folder using scp
echo Copying src folder...
scp -r "%SCRIPT_DIR%src" %PI_USER%@%PI_HOST%:%PI_DEST%/

if %ERRORLEVEL% EQU 0 (
    echo [OK] src folder copied successfully
) else (
    echo [ERROR] Failed to copy src folder
    exit /b 1
)

:: Copy requirements.txt
echo Copying requirements.txt...
scp "%SCRIPT_DIR%requirements.txt" %PI_USER%@%PI_HOST%:%PI_DEST%/

:: Copy .env
echo Copying .env...
scp "%SCRIPT_DIR%.env" %PI_USER%@%PI_HOST%:%PI_DEST%/ 2>nul

echo.
echo Done!
pause
