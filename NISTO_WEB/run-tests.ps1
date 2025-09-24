# NISTO Web Application - Master Test Runner
# PowerShell script to run all tests (frontend and backend)

param(
    [string]$Target = "all",  # Options: "all", "frontend", "backend"
    [switch]$Watch = $false,  # Run tests in watch mode
    [switch]$Coverage = $false,  # Run with coverage
    [switch]$Verbose = $false   # Verbose output
)

# Colors for output
$Red = [System.ConsoleColor]::Red
$Green = [System.ConsoleColor]::Green
$Yellow = [System.ConsoleColor]::Yellow
$Blue = [System.ConsoleColor]::Blue
$White = [System.ConsoleColor]::White

function Write-ColorOutput($ForegroundColor, $Message) {
    $previousColor = $Host.UI.RawUI.ForegroundColor
    $Host.UI.RawUI.ForegroundColor = $ForegroundColor
    Write-Output $Message
    $Host.UI.RawUI.ForegroundColor = $previousColor
}

function Write-Header($Message) {
    Write-Output ""
    Write-ColorOutput $Blue "================================================================"
    Write-ColorOutput $Blue "  $Message"
    Write-ColorOutput $Blue "================================================================"
    Write-Output ""
}

function Write-Success($Message) {
    Write-ColorOutput $Green "[PASS] $Message"
}

function Write-Error($Message) {
    Write-ColorOutput $Red "[FAIL] $Message"
}

function Write-Warning($Message) {
    Write-ColorOutput $Yellow "[WARN] $Message"
}

function Write-Info($Message) {
    Write-ColorOutput $White "[INFO] $Message"
}

# Check if we're in the right directory
if (-not (Test-Path "frontend/package.json") -or -not (Test-Path "backend/requirements.txt")) {
    Write-Error "Please run this script from the NISTO_WEB directory"
    Write-Info "Expected structure:"
    Write-Info "  NISTO_WEB/"
    Write-Info "  ├── frontend/package.json"
    Write-Info "  ├── backend/requirements.txt"
    Write-Info "  └── run-tests.ps1"
    exit 1
}

# Track test results
$frontendPassed = $false
$backendPassed = $false
$totalTests = 0
$passedTests = 0
$failedTests = 0

Write-Header "NISTO Web Application Test Suite"
Write-Info "Target: $Target"
Write-Info "Watch mode: $Watch"
Write-Info "Coverage: $Coverage"
Write-Info "Verbose: $Verbose"

# Function to run frontend tests
function Run-FrontendTests {
    Write-Header "Running Frontend Tests (React + TypeScript)"
    
    if (-not (Test-Path "frontend/node_modules")) {
        Write-Warning "Frontend dependencies not found. Installing..."
        Set-Location frontend
        npm install
        Set-Location ..
    }
    
    Set-Location frontend
    
    try {
        $testCommand = "npm test"
        
        if ($Watch) {
            $testCommand += " -- --watch"
        } else {
            $testCommand += " -- --run"
        }
        
        if ($Coverage) {
            $testCommand += " --coverage"
        }
        
        if ($Verbose) {
            $testCommand += " --reporter=verbose"
        }
        
        Write-Info "Running: $testCommand"
        
        $result = Invoke-Expression $testCommand
        $exitCode = $LASTEXITCODE
        
        if ($exitCode -eq 0) {
            Write-Success "Frontend tests passed!"
            $script:frontendPassed = $true
        } else {
            Write-Error "Frontend tests failed!"
            $script:frontendPassed = $false
        }
        
        return $exitCode
    }
    catch {
        Write-Error "Error running frontend tests: $_"
        $script:frontendPassed = $false
        return 1
    }
    finally {
        Set-Location ..
    }
}

# Function to run backend tests
function Run-BackendTests {
    Write-Header "Running Backend Tests (FastAPI + Python)"
    
    # Check if virtual environment exists
    if (-not (Test-Path "backend/venv")) {
        Write-Warning "Python virtual environment not found. Creating..."
        Set-Location backend
        python -m venv venv
        Set-Location ..
    }
    
    Set-Location backend
    
    try {
        # Activate virtual environment
        if (Test-Path "venv/Scripts/Activate.ps1") {
            . .\venv\Scripts\Activate.ps1
        } elseif (Test-Path "venv/bin/activate") {
            . .\venv\bin\activate
        } else {
            Write-Error "Could not find virtual environment activation script"
            return 1
        }
        
        # Install dependencies if needed
        Write-Info "Ensuring Python dependencies are installed..."
        pip install -r requirements.txt | Out-Null
        
        $testCommand = "python -m pytest"
        
        if ($Verbose) {
            $testCommand += " -v"
        } else {
            $testCommand += " -q"
        }
        
        if ($Coverage) {
            $testCommand += " --cov=app --cov-report=term-missing"
        }
        
        if ($Watch) {
            Write-Warning "Watch mode not available for backend tests (pytest-watch not configured)"
        }
        
        Write-Info "Running: $testCommand"
        
        $result = Invoke-Expression $testCommand
        $exitCode = $LASTEXITCODE
        
        if ($exitCode -eq 0) {
            Write-Success "Backend tests passed!"
            $script:backendPassed = $true
        } else {
            Write-Error "Backend tests failed!"
            $script:backendPassed = $false
        }
        
        return $exitCode
    }
    catch {
        Write-Error "Error running backend tests: $_"
        $script:backendPassed = $false
        return 1
    }
    finally {
        # Deactivate virtual environment
        if (Get-Command deactivate -ErrorAction SilentlyContinue) {
            deactivate
        }
        Set-Location ..
    }
}

# Run tests based on target
$startTime = Get-Date

try {
    switch ($Target.ToLower()) {
        "frontend" {
            $exitCode = Run-FrontendTests
        }
        "backend" {
            $exitCode = Run-BackendTests
        }
        "all" {
            Write-Info "Running all tests..."
            
            $frontendExitCode = Run-FrontendTests
            $backendExitCode = Run-BackendTests
            
            # Overall exit code is 0 only if both pass
            $exitCode = [Math]::Max($frontendExitCode, $backendExitCode)
        }
        default {
            Write-Error "Invalid target: $Target"
            Write-Info "Valid targets: all, frontend, backend"
            exit 1
        }
    }
}
catch {
    Write-Error "Unexpected error: $_"
    $exitCode = 1
}

# Summary
$endTime = Get-Date
$duration = $endTime - $startTime

Write-Header "Test Summary"
Write-Info "Duration: $($duration.TotalSeconds.ToString('F2')) seconds"

if ($Target -eq "all" -or $Target -eq "frontend") {
    if ($frontendPassed) {
        Write-Success "Frontend: PASSED"
    } else {
        Write-Error "Frontend: FAILED"
    }
}

if ($Target -eq "all" -or $Target -eq "backend") {
    if ($backendPassed) {
        Write-Success "Backend: PASSED"
    } else {
        Write-Error "Backend: FAILED"
    }
}

if ($exitCode -eq 0) {
    Write-Success "All tests passed!"
} else {
    Write-Error "Some tests failed!"
}

Write-Header "Usage Examples"
Write-Info "Run all tests:           .\run-tests.ps1"
Write-Info "Run frontend only:       .\run-tests.ps1 -Target frontend"
Write-Info "Run backend only:        .\run-tests.ps1 -Target backend"
Write-Info "Run with coverage:       .\run-tests.ps1 -Coverage"
Write-Info "Run in watch mode:       .\run-tests.ps1 -Target frontend -Watch"
Write-Info "Verbose output:          .\run-tests.ps1 -Verbose"

exit $exitCode
