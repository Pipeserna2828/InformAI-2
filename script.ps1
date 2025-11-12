# Script para instalar Poetry en Windows

Write-Host "Instalando Poetry..." -ForegroundColor Green

# Instalar Poetry
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -

# Añadir Poetry al PATH de la sesión actual
$env:Path += ";$env:APPDATA\Python\Scripts"

Write-Host "`nPoetry instalado. Inicializando el proyecto..." -ForegroundColor Green

# Inicializar dependencias del proyecto
poetry install

# Instalar el plugin shell para poder usar el comando 'poetry shell'
Write-Host "`nInstalando plugin shell para Poetry..." -ForegroundColor Green
poetry plugin add poetry-plugin-shell

# Activar el entorno virtual y ejecutar la aplicación
Write-Host "`nPara activar el entorno virtual y ejecutar la aplicación, ejecuta estos comandos:" -ForegroundColor Cyan
Write-Host "1. poetry env use python3.11 (o la versión de Python que tengas instalada compatible con <3.12)" -ForegroundColor Cyan
Write-Host "2. poetry shell" -ForegroundColor Cyan
Write-Host "3. python -m uvicorn src.main:app --reload" -ForegroundColor Cyan

Write-Host "`nTambién puedes ejecutar la aplicación directamente con:" -ForegroundColor Cyan
Write-Host "poetry run python -m uvicorn src.main:app --reload" -ForegroundColor Cyan

Write-Host "`nRecuerda añadir la siguiente ruta a tu PATH permanente si no lo has hecho ya:" -ForegroundColor Yellow
Write-Host "$env:APPDATA\Python\Scripts" -ForegroundColor Yellow