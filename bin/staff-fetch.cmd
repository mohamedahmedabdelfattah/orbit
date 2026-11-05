@echo off
python "%~dp0..\core\tools\fetch.py" %*
exit /b %errorlevel%
