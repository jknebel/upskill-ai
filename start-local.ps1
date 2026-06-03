# Script de démarrage local pour Upskill AI
# Ce script lance le backend FastAPI et le frontend React en parallèle.

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "      DÉMARRAGE DE UPSKILL AI POC        " -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# 1. Démarrer le Backend FastAPI
Write-Host "[1/2] Démarrage du backend FastAPI sur http://localhost:8000..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; .\venv\Scripts\activate; uvicorn main:app --reload --port 8000"

# 2. Démarrer le Frontend React
Write-Host "[2/2] Démarrage du frontend React sur http://localhost:5173..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"

Write-Host "-----------------------------------------" -ForegroundColor Green
Write-Host "Les deux serveurs sont en cours de lancement." -ForegroundColor Green
Write-Host "Le backend tourne sur : http://localhost:8000" -ForegroundColor Green
Write-Host "Le frontend tourne sur : http://localhost:5173" -ForegroundColor Green
Write-Host "Veuillez garder les fenêtres PowerShell ouvertes." -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
