@echo off
python "%~dp0..\core\tools\browse.py" %*
exit /b %errorlevel%
