# Run from the project root with the venv active:
#   powershell -ExecutionPolicy Bypass -File deploy\make_space.ps1 -SpaceUrl https://huggingface.co/spaces/USERNAME/vidseek
param([Parameter(Mandatory=$true)][string]$SpaceUrl)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$out  = Join-Path $root "space_build"
if (Test-Path $out) { Remove-Item $out -Recurse -Force }
New-Item -ItemType Directory $out | Out-Null
Copy-Item "$root\api","$root\vidseek","$root\chroma_db" -Destination $out -Recurse
Copy-Item "$root\main.py" $out
Copy-Item "$PSScriptRoot\Dockerfile" $out
Copy-Item "$PSScriptRoot\requirements.txt" $out
Copy-Item "$PSScriptRoot\README_space.md" "$out\README.md"
Get-ChildItem $out -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force
# pin chromadb to your local version so the stored index stays readable
$ver = ((pip show chromadb | Select-String "^Version:").ToString() -split "\s+")[1]
(Get-Content "$out\requirements.txt") -replace "^chromadb$", "chromadb==$ver" | Set-Content "$out\requirements.txt"
Set-Location $out
git init -q
git lfs install
git lfs track "*.sqlite3" "*.bin" "*.parquet" "*.pickle"
git add .
git commit -q -m "Deploy VidSeek (read-only demo)"
git branch -M main
git remote add origin $SpaceUrl
git push -u origin main --force
Write-Host "Done. Space is building: $SpaceUrl"
