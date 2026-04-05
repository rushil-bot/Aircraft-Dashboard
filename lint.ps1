# lint.ps1
# Runs code formatting and linting for the Aircraft Dashboard Python backend

Write-Host "Ensuring linters are installed..." -ForegroundColor DarkGray
python -m pip install -q black pylint

Write-Host "`n-- Formatting code with Black --" -ForegroundColor Cyan
python -m black gateway agents data

Write-Host "`n-- Analyzing code with Pylint --" -ForegroundColor Cyan
$env:PYTHONPATH = ".;" + $env:PYTHONPATH
# We specifically target our python directories
python -m pylint gateway agents data

$exitCode = $LASTEXITCODE

if ($exitCode -eq 0) {
    Write-Host "`n[PASS] Linting passed! Your code is pristine." -ForegroundColor Green
} else {
    Write-Host "`n[FAIL] Pylint found some issues. Review the warnings above." -ForegroundColor Yellow
}

# Preserve the exit code so CI or other wrappers know if it failed
exit $exitCode
