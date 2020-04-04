@echo off

rem set PYTHON_CMD="C:\Python\python.exe"  <-- Comment ;)
set PYTHON_CMD="python.exe"

set BASEDIR=%~dp0
cd %BASEDIR%
%PYTHON_CMD% engine.py
