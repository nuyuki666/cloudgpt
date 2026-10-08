@echo off
title Deploy CloudGPT to Vercel
cd /d "%~dp0"
python deploy_to_vercel.py %*
pause
