# Generate .env for Docker from backend/.env and frontend/.env.local

Write-Host "Generating .env for Docker..." -ForegroundColor Cyan

# Check backend env
if (-not (Test-Path "backend/.env")) {
    Write-Host "❌ backend/.env not found" -ForegroundColor Red
    exit 1
}

# Start header
@"
# Docker Environment Configuration
# Auto-generated from backend/.env
# DO NOT EDIT MANUALLY - regenerate with create-docker-env.ps1

"@ | Out-File -FilePath ".env" -Encoding utf8

# Add backend configuration
"# ========================================" | Out-File -FilePath ".env" -Append -Encoding utf8
"# Backend Configuration (from backend/.env)" | Out-File -FilePath ".env" -Append -Encoding utf8
"# ========================================" | Out-File -FilePath ".env" -Append -Encoding utf8

Get-Content "backend/.env" | Where-Object { $_ -notmatch '^#' -and $_ -notmatch '^$' } | Out-File -FilePath ".env" -Append -Encoding utf8

Write-Host "✓ .env file created successfully" -ForegroundColor Green
Write-Host ""
Write-Host "Review the generated .env file before running Docker:"
Write-Host "  Get-Content .env" -ForegroundColor Gray
