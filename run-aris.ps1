# Inicia o ARIS (backend + frontend) e abre numa JANELA PEQUENA, sem cara de
# navegador (modo --app do Edge). Usa o Edge/Chrome real, então o reconhecimento
# de voz (Web Speech API) continua funcionando.
#
# Uso:  botão direito > "Executar com PowerShell"  (ou:  .\run-aris.ps1)
# Pré-requisitos (uma vez):  cd backend; uv sync     e     cd frontend; npm install

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

Write-Host "Iniciando o nucleo (backend) do ARIS..." -ForegroundColor Cyan
Start-Process -WindowStyle Minimized -WorkingDirectory "$root\backend" `
  -FilePath "$root\backend\.venv\Scripts\uvicorn.exe" `
  -ArgumentList "aris.api.gateway:app", "--port", "8000"

Write-Host "Iniciando a interface (frontend)..." -ForegroundColor Cyan
Start-Process -WindowStyle Minimized -WorkingDirectory "$root\frontend" `
  -FilePath "npm.cmd" -ArgumentList "run", "dev"

Write-Host "Aguardando a interface subir..." -ForegroundColor Cyan
$pronto = $false
for ($i = 0; $i -lt 60; $i++) {
  try {
    Invoke-WebRequest "http://localhost:5173" -UseBasicParsing -TimeoutSec 1 | Out-Null
    $pronto = $true; break
  } catch { Start-Sleep -Milliseconds 500 }
}
if (-not $pronto) { Write-Host "A interface demorou a responder; abrindo mesmo assim." -ForegroundColor Yellow }

Write-Host "Abrindo o ARIS em janela pequena..." -ForegroundColor Green
$args = @("--app=http://localhost:5173", "--window-size=420,660", "--window-position=120,80")
try { Start-Process "msedge" -ArgumentList $args }
catch {
  try { Start-Process "chrome" -ArgumentList $args }
  catch { Write-Host "Edge/Chrome nao encontrados. Abra http://localhost:5173 no Edge/Chrome." -ForegroundColor Red }
}

Write-Host ""
Write-Host "ARIS no ar. Para parar: feche a janela e encerre as 2 janelas minimizadas (backend/frontend)." -ForegroundColor DarkGray
