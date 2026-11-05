@echo off
python "%~dp0..\core\tools\skill.py" %*
exit /b %errorlevel%
