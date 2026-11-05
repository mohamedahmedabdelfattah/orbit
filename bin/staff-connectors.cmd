@echo off
python "%~dp0..\core\tools\connectors_cli.py" %*
exit /b %errorlevel%
