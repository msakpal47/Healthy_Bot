Param()
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = "E:\Healthy"
$aws = Join-Path $root "healthy_aws"
$local = Join-Path $root "healthy_local"

if (Test-Path $aws) { Remove-Item $aws -Recurse -Force }
if (Test-Path $local) { Remove-Item $local -Recurse -Force }
New-Item -ItemType Directory -Path $aws | Out-Null
New-Item -ItemType Directory -Path $local | Out-Null

# Copy full project to healthy_local (excluding the target output folders themselves)
Get-ChildItem -Path $root -Force | Where-Object { $_.Name -notin @("healthy_aws","healthy_local") } | ForEach-Object {
  Copy-Item -Path $_.FullName -Destination $local -Recurse -Force
}

# Build minimal deployable healthy_aws
$awsSrcWeb = Join-Path $aws "src\web"
$awsSimple = Join-Path $aws "simple"
$awsData = Join-Path $aws "Data"
$awsStorage = Join-Path $aws "storage"

New-Item -ItemType Directory -Path (Join-Path $awsSrcWeb "templates") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $awsSrcWeb "static") -Force | Out-Null
New-Item -ItemType Directory -Path $awsSimple -Force | Out-Null
New-Item -ItemType Directory -Path $awsData -Force | Out-Null
New-Item -ItemType Directory -Path $awsStorage -Force | Out-Null

Copy-Item -Path (Join-Path $root "requirements.txt") -Destination $aws -Force
if (Test-Path (Join-Path $root "Dockerfile")) {
  Copy-Item -Path (Join-Path $root "Dockerfile") -Destination $aws -Force
}
Copy-Item -Path (Join-Path $root "src\web\app.py") -Destination (Join-Path $awsSrcWeb "app.py") -Force
Copy-Item -Path (Join-Path $root "src\web\templates\*") -Destination (Join-Path $awsSrcWeb "templates") -Recurse -Force
Copy-Item -Path (Join-Path $root "src\web\static\*") -Destination (Join-Path $awsSrcWeb "static") -Recurse -Force
Copy-Item -Path (Join-Path $root "simple\consult.py") -Destination (Join-Path $awsSimple "consult.py") -Force
Copy-Item -Path (Join-Path $root "simple\gen_ai.py") -Destination (Join-Path $awsSimple "gen_ai.py") -Force
Copy-Item -Path (Join-Path $root "simple\__init__.py") -Destination (Join-Path $awsSimple "__init__.py") -Force
Copy-Item -Path (Join-Path $root "src\config.py") -Destination (Join-Path $aws "src\config.py") -Force
Copy-Item -Path (Join-Path $root "Data\100_unique_diseases.csv") -Destination (Join-Path $awsData "100_unique_diseases.csv") -Force

# Create run.sh for AWS
$runSh = @"
#!/usr/bin/env bash
set -e
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
export DATA_PATH=\$(pwd)/Data
gunicorn -b 0.0.0.0:8000 'src.web.app:app'
"@
Set-Content -Path (Join-Path $aws "run.sh") -Value $runSh -Encoding ascii

Write-Host "Packed healthy_local and healthy_aws"
