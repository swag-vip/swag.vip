@echo off
echo ============================================
echo    Discord Bot - Full Stack
echo ============================================
echo.

REM Generer une cle API
for /f "delims=" %%i in ('powershell -Command "[System.Guid]::NewGuid().ToString('N')"') do set API_KEY=%%i
echo Cle API generee: %API_KEY%
echo.

REM Installer les dependances
echo Installation des dependances...
pip install -r requirements-full.txt
echo.

REM Lancer le backend
echo Demarrage du backend sur http://localhost:5000
echo Dashboard: ouvrir dashboard/index.html dans le navigateur
echo.
echo CLE API (a sauvegarder): %API_KEY%
echo.
set API_KEY=%API_KEY%
python backend.py
pause
