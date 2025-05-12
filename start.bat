CALL .\venv\Scripts\activate
python .\main.py
IF %ERRORLEVEL% NEQ 0 (
    echo Python script encountered an error.
    pause
)