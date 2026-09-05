@echo off
net session >nul 2>&1
if %errorlevel% neq 0 (
  powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b
)

echo Setting next boot to Safe Mode...
bcdedit /set {current} safeboot minimal
if %errorlevel% neq 0 (
  echo Failed to set Safe Mode boot.
  pause
  exit /b 1
)

echo.
echo Safe Mode boot is set.
echo Restart now, then run run-cleanup-360-as-admin.bat in Safe Mode.
echo.
choice /C YN /M "Restart now"
if errorlevel 2 exit /b 0
shutdown /r /t 5
