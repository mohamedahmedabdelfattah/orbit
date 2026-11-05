@echo off
python "%~dp0..\core\tools\remind.py" %*
exit /b %errorlevel%
