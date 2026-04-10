@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0commit_stack_repos.ps1" %*
exit /b %ERRORLEVEL%
