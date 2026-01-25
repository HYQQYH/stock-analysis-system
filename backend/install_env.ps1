# PowerShell script to activate virtual environment and install dependencies

Write-Host "========================================" -ForegroundColor Green
Write-Host "Stock Analysis System - Environment Setup" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Check if virtual environment exists
$venv_path = ".\aistock_env"
if (Test-Path $venv_path) {
    Write-Host "[✓] Virtual environment found at $venv_path" -ForegroundColor Green
} else {
    Write-Host "[✗] Virtual environment not found. Please create it first." -ForegroundColor Red
    exit 1
}

# Activate virtual environment
Write-Host ""
Write-Host "[→] Activating virtual environment..." -ForegroundColor Yellow
& .\aistock_env\Scripts\Activate.ps1
Write-Host "[✓] Virtual environment activated" -ForegroundColor Green

# Verify Python and pip
Write-Host ""
Write-Host "[→] Verifying Python and pip..." -ForegroundColor Yellow
python --version
pip --version

# Upgrade pip, setuptools, wheel
Write-Host ""
Write-Host "[→] Upgrading pip, setuptools, wheel..." -ForegroundColor Yellow
python -m pip install --upgrade pip setuptools wheel -i https://mirrors.aliyun.com/pypi/simple/ 2>&1 | Select-Object -Last 3

# Install requirements
Write-Host ""
Write-Host "[→] Installing project dependencies (this may take 3-5 minutes)..." -ForegroundColor Yellow
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

if ($LASTEXITCODE -eq 0) {
    Write-Host "[✓] Dependencies installed successfully" -ForegroundColor Green
} else {
    Write-Host "[✗] Failed to install dependencies" -ForegroundColor Red
    exit 1
}

# Verify key packages
Write-Host ""
Write-Host "[→] Verifying key packages..." -ForegroundColor Yellow
Write-Host ""

$packages = @("fastapi", "pandas", "sqlalchemy", "redis", "pydantic", "requests")
foreach ($pkg in $packages) {
    try {
        $version = python -c "import $pkg; print($pkg.__version__)" 2>&1
        if ($?) {
            Write-Host "[✓] $pkg : $version" -ForegroundColor Green
        } else {
            Write-Host "[?] $pkg : installed but version check failed" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "[✗] $pkg : NOT FOUND" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "[→] Listing all installed packages..." -ForegroundColor Yellow
pip list

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✓ Environment setup completed successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. The virtual environment is still active in this terminal" -ForegroundColor Cyan
Write-Host "2. Test FastAPI: python -m uvicorn app.main:app --reload" -ForegroundColor Cyan
Write-Host "3. Visit http://localhost:8000/docs for API documentation" -ForegroundColor Cyan
Write-Host ""
