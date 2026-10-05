@echo off
setlocal
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo Python no se encontro en PATH.
  pause
  exit /b 1
)
python -m pip show pyinstaller >nul 2>nul
if errorlevel 1 (
  echo Instalando PyInstaller...
  python -m pip install pyinstaller
  if errorlevel 1 pause & exit /b 1
)
echo.
echo Creando ejecutable distribuible...
python -m PyInstaller --noconfirm --clean --windowed --name "Sistema Gestion Microeconomica" --add-data "assets;assets" --add-data "database\migrations;database\migrations" main.py
if errorlevel 1 (
  echo.
  echo Ocurrio un error al crear el ejecutable.
  pause
  exit /b 1
)
echo.
echo LISTO.
echo La carpeta para compartir esta en:
echo dist\Sistema Gestion Microeconomica
echo.
echo IMPORTANTE: comparte TODA esa carpeta, preferiblemente comprimida en ZIP.
pause
