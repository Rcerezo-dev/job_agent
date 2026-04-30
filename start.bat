@echo off
echo Starting Job Agent dashboard...

:: Start the API server in a new window (keeps running in background)
start "Job Agent API" cmd /k "python -m uvicorn job_agent.api:app --reload"

:: Give the server a moment to start
timeout /t 2 /nobreak >nul

:: Open the dashboard in the default browser
start "" "%~dp0frontend\index.html"

echo Dashboard open. Close the "Job Agent API" window to stop the server.
