@echo off
echo ========================================
echo MCP Federation v3.0.0 Test Script
echo ========================================
echo.
echo This will test the new automated installer
echo.

REM Check Python
python --version 2>NUL
if %ERRORLEVEL% NEQ 0 (
    echo Python NOT FOUND - Installer should offer to install it
) else (
    echo Python FOUND
)

echo.

REM Check Node.js
node --version 2>NUL
if %ERRORLEVEL% NEQ 0 (
    echo Node.js NOT FOUND - Installer should offer to install it
) else (
    echo Node.js FOUND
)

echo.

REM Check npm
npm --version 2>NUL
if %ERRORLEVEL% NEQ 0 (
    echo npm NOT FOUND - Installer should fix PATH or install Node.js
) else (
    echo npm FOUND
)

echo.

REM Check Git
git --version 2>NUL
if %ERRORLEVEL% NEQ 0 (
    echo Git NOT FOUND - Installer should offer to install it
) else (
    echo Git FOUND
)

echo.
echo ========================================
echo Now running the installer...
echo ========================================
echo.

python install.py

pause