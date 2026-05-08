param(
  [int]$BackendPort = 8001,
  [int]$FrontendPort = 3000,
  [string]$BackendHost = "127.0.0.1"
)

$ErrorActionPreference = "Stop"

function Ensure-Command($name) {
  if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
    throw "Missing required command: $name"
  }
}

function Ensure-BackendEnv {
  $backendDir = Join-Path $PSScriptRoot "backend"
  $envExample = Join-Path $backendDir ".env.example"
  $envFile = Join-Path $backendDir ".env"
  if (-not (Test-Path $envFile)) {
    if (Test-Path $envExample) {
      Copy-Item $envExample $envFile -Force | Out-Null
      Write-Host "Created backend\.env from .env.example"
    } else {
      throw "backend\.env.example not found"
    }
  }
}

function Ensure-FrontendEnv {
  $frontendDir = Join-Path $PSScriptRoot "frontend"
  $envLocal = Join-Path $frontendDir ".env.local"
  $backendUrl = "http://localhost:$BackendPort"
  $line = "NEXT_PUBLIC_BACKEND_BASE_URL=$backendUrl"

  if (-not (Test-Path $envLocal)) {
    $line | Out-File -Encoding utf8 $envLocal
    Write-Host "Created frontend\.env.local => $backendUrl"
    return
  }

  $content = Get-Content $envLocal -ErrorAction SilentlyContinue
  if ($content -notmatch "^NEXT_PUBLIC_BACKEND_BASE_URL=") {
    Add-Content -Path $envLocal -Value $line
    Write-Host "Updated frontend\.env.local => $backendUrl"
    return
  }

  $updated = $content | ForEach-Object {
    if ($_ -match "^NEXT_PUBLIC_BACKEND_BASE_URL=") { $line } else { $_ }
  }
  Set-Content -Path $envLocal -Value $updated -Encoding utf8
  Write-Host "Updated frontend\.env.local => $backendUrl"
}

function Ensure-BackendVenvAndDeps {
  $backendDir = Join-Path $PSScriptRoot "backend"
  $venvPy = Join-Path $backendDir ".venv\Scripts\python.exe"
  if (-not (Test-Path $venvPy)) {
    Write-Host "Creating backend venv..."
    python -m venv (Join-Path $backendDir ".venv")
  }

  $req = Join-Path $backendDir "requirements.txt"
  if (-not (Test-Path $req)) {
    throw "backend\requirements.txt not found"
  }

  Write-Host "Installing backend deps..."
  & $venvPy -m pip install -r $req | Out-Null
}

function Ensure-FrontendDeps {
  $frontendDir = Join-Path $PSScriptRoot "frontend"
  $nodeModules = Join-Path $frontendDir "node_modules"
  if (-not (Test-Path $nodeModules)) {
    Write-Host "Installing frontend deps..."
    Push-Location $frontendDir
    try {
      npm install | Out-Null
    } finally {
      Pop-Location
    }
  }
}

Ensure-Command python
Ensure-Command npm

Ensure-BackendEnv
Ensure-FrontendEnv
Ensure-BackendVenvAndDeps
Ensure-FrontendDeps

$backendDir = Join-Path $PSScriptRoot "backend"
$frontendDir = Join-Path $PSScriptRoot "frontend"
$venvUvicorn = Join-Path $backendDir ".venv\Scripts\uvicorn.exe"

Write-Host ""
Write-Host "Starting backend on http://$BackendHost`:$BackendPort ..."
Start-Process -WorkingDirectory $backendDir -FilePath $venvUvicorn -ArgumentList @(
  "app.main:app",
  "--reload",
  "--host", $BackendHost,
  "--port", "$BackendPort"
) | Out-Null

Write-Host "Starting frontend on http://localhost:$FrontendPort ..."
# Start-Process -FilePath "npm" fails on Windows (npm is npm.cmd, not npm.exe).
# Use cmd so the dev server actually starts; /k keeps the window open if npm errors immediately.
Start-Process -WorkingDirectory $frontendDir -FilePath "cmd.exe" -ArgumentList @(
  "/k", "npm run dev -- --port $FrontendPort"
) | Out-Null

Write-Host ""
Write-Host "Open:"
Write-Host "  Frontend: http://localhost:$FrontendPort"
Write-Host "  Backend Swagger: http://localhost:$BackendPort/docs"
Write-Host "  Backend OpenAPI: http://localhost:$BackendPort/openapi.json"
Write-Host ""
Write-Host "Note: Set backend/.env LLM keys before using /api/v1/chat."

