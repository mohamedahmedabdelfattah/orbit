@echo off
python "%~dp0..\core\tools\docs.py" %*
exit /b %errorlevel%
