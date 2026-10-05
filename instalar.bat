@echo off
chcp 65001 >nul
echo ================================================
echo  Instalacion del Sistema de Gestion V6
echo ================================================
echo.
python --version >nul 2>&1
if errorlevel 1 (
  echo No se encontro el comando python. Probando con py...
  py --version >nul 2>&1
  if errorlevel 1 (
    echo No se encontro Python 3. Instalalo y vuelve a ejecutar este archivo.
    pause
    exit /b 1
  )
  py -m pip install -r requirements.txt
) else (
  python -m pip install -r requirements.txt
)
echo.
echo Instalacion terminada. Ahora puedes abrir run_demo.bat o run.bat.
pause
