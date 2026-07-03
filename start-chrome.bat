@echo off
echo Closing all Chrome instances...
taskkill /f /im chrome.exe
timeout /t 2 /nobreak
echo Starting Chrome with remote debugging and custom profile...
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\Users\USER\.gemini\antigravity\scratch\chrome-debug-profile"
echo Done! Please log in to your site in the opened browser, and then return here and say "ok".
pause
