@echo off
python "%~dp0..\core\tools\watch.py" %*
exit /b %errorlevel%
