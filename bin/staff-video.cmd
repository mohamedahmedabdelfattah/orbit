@echo off
python "%~dp0..\core\tools\video.py" %*
exit /b %errorlevel%
