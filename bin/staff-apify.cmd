@echo off
python "%~dp0..\core\tools\apify.py" %*
exit /b %errorlevel%
