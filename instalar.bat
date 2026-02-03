@echo off
echo ======================================================
echo    INSTALADOR AUTOMATICO - MONITOR LABIND
echo ======================================================
echo.

:: 1. Criando o ambiente virtual
echo [1/3] Criando ambiente virtual (venv)...
python -m venv venv

:: 2. Ativando o ambiente e atualizando o PIP
echo [2/3] Atualizando o instalador (pip)...
call .\venv\Scripts\activate
python -m pip install --upgrade pip

:: 3. Instalando requisitos do arquivo
echo [3/3] Instalando dependencias do requirements.txt...
pip install -r requirements.txt

echo.
echo ======================================================
echo    INSTALACAO CONCLUIDA COM SUCESSO!
echo    Para iniciar, use o arquivo iniciar_monitor.bat
echo ======================================================
pause