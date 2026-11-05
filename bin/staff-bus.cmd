@echo off
python "%~dp0..\core\tools\bus.py" %*
exit /b %errorlevel%
