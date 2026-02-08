@echo off
REM SecretarAI Bot Launcher for Windows

cd /d "%~dp0.."
set PYTHONPATH=%CD%
py scripts\run_bot.py
