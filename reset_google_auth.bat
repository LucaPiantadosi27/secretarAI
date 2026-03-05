@echo off
echo =========================================
echo SECRETARAI - GOOGLE OAUTH RESET
echo =========================================
echo.
echo Arresto del bot in corso (se in esecuzione in background)...
taskkill /F /IM python.exe /T >nul 2>&1
echo.

if exist "token.json" (
    echo Eliminazione del vecchio token.json...
    del token.json
    echo OK.
) else (
    echo Nessun token.json trovato, perfetto.
)

echo.
echo Cerca il tuo nuovo file scaricato dalla Google Cloud Console...
echo Rinomina il file scaricato in "credentials.json" e mettilo qui:
echo %CD%
echo.
echo Una volta fatto, premi un tasto qualsiasi per avviare il bot
echo e completare il nuovo login sul browser.
pause

echo Avvio di SecretarAI...
py scripts\run_bot.py
