@echo off
title Inventory System Server

echo Starting Inventory Server...
echo DO NOT CLOSE THIS WINDOW
echo.

cd /d "%~dp0"

echo Current folder:
cd

echo.
echo Running Python...
"C:\Users\hets8\AppData\Local\Python\pythoncore-3.14-64\python.exe" app.py

echo.
echo ERRORLEVEL: %ERRORLEVEL%
echo.
echo If you see this, Python exited immediately.
pause
