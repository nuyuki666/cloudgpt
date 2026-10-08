@echo off
chcp 65001 >nul
title CloudGPT Public Hosting
echo ========================================================
echo   Запуск CloudGPT на глобальном хостинге (HTTPS)
echo ========================================================
python start_public_host.py
pause
