@echo off
chcp 65001 >nul
title CloudGPT APK Builder
echo ========================================================
echo   Сборка нативного Android APK для CloudGPT Mobile
echo ========================================================
python build_apk.py
echo.
pause
