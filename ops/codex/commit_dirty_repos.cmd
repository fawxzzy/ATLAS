@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0commit_dirty_repos.ps1" %*
exit /b %ERRORLEVEL%
