@echo off
echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Building EXE...
flet pack main.py --name HyperField-Lite --project "HyperField Lite"
echo.
echo Done! Check the dist folder for the EXE.
pause
