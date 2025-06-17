@echo off
echo ========================================
echo     Restarting MongoDB Service
echo ========================================

echo Stopping MongoDB Service...
net stop MongoDB 

echo Waiting for 5 seconds...
timeout /t 5 /nobreak > NUL

echo Starting MongoDB Service...
net start MongoDB 

echo ----------------------------------------
echo MongoDB Service has been restarted.
echo ----------------------------------------
