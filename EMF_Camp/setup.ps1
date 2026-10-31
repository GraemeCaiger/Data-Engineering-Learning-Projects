# Locate project directory
$ProjectFolder = $PSScriptRoot

Write-Host "`n---------------- Installing Python dependencies ----------------`n"

# Install requirements
python -m pip install -r "$ProjectFolder\requirements.txt"

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Dependency installation failed."
    exit 1
}

Write-Host "`n---------------- Environment built ----------------`n"
Write-Host "Setup complete!"