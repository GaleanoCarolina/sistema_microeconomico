@echo off
chcp 65001 >nul
setlocal

where python >nul 2>&1
if %errorlevel%==0 (
    python main.py
    set EXITCODE=%errorlevel%
) else (
    where py >nul 2>&1
    if %errorlevel%==0 (
        py main.py
        set EXITCODE=%errorlevel%
    ) else (
        echo No se encontro Python. Instala Python 3 y vuelve a intentarlo.
        set EXITCODE=1
    )
)

if not %EXITCODE%==0 (
    echo.
    echo La aplicacion se cerro por un error. Copia el mensaje mostrado arriba si necesitas ayuda.
    pause
)
exit /b %EXITCODE%
