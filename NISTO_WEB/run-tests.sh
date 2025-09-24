#!/bin/bash

# NISTO Web Application - Master Test Runner
# Cross-platform shell script to run all tests (frontend and backend)

set -e  # Exit on any error

# Default values
TARGET="all"
WATCH=false
COVERAGE=false
VERBOSE=false

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo ""
    echo -e "${BLUE}================================================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}================================================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${WHITE}ℹ️  $1${NC}"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--target)
            TARGET="$2"
            shift 2
            ;;
        -w|--watch)
            WATCH=true
            shift
            ;;
        -c|--coverage)
            COVERAGE=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            echo "NISTO Web Application Test Runner"
            echo ""
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -t, --target TARGET     Run tests for specific target (all|frontend|backend)"
            echo "  -w, --watch            Run tests in watch mode (frontend only)"
            echo "  -c, --coverage         Run tests with coverage reporting"
            echo "  -v, --verbose          Enable verbose output"
            echo "  -h, --help             Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                     # Run all tests"
            echo "  $0 -t frontend         # Run frontend tests only"
            echo "  $0 -t backend -c       # Run backend tests with coverage"
            echo "  $0 -t frontend -w      # Run frontend tests in watch mode"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

# Check if we're in the right directory
if [[ ! -f "frontend/package.json" ]] || [[ ! -f "backend/requirements.txt" ]]; then
    print_error "Please run this script from the NISTO_WEB directory"
    print_info "Expected structure:"
    print_info "  NISTO_WEB/"
    print_info "  ├── frontend/package.json"
    print_info "  ├── backend/requirements.txt"
    print_info "  └── run-tests.sh"
    exit 1
fi

# Track test results
frontend_passed=false
backend_passed=false

print_header "NISTO Web Application Test Suite"
print_info "Target: $TARGET"
print_info "Watch mode: $WATCH"
print_info "Coverage: $COVERAGE"
print_info "Verbose: $VERBOSE"

# Function to run frontend tests
run_frontend_tests() {
    print_header "Running Frontend Tests (React + TypeScript)"
    
    if [[ ! -d "frontend/node_modules" ]]; then
        print_warning "Frontend dependencies not found. Installing..."
        cd frontend
        npm install
        cd ..
    fi
    
    cd frontend
    
    local test_command="npm test"
    
    if [[ "$WATCH" == true ]]; then
        test_command+=" -- --watch"
    else
        test_command+=" -- --run"
    fi
    
    if [[ "$COVERAGE" == true ]]; then
        test_command+=" --coverage"
    fi
    
    if [[ "$VERBOSE" == true ]]; then
        test_command+=" --reporter=verbose"
    fi
    
    print_info "Running: $test_command"
    
    if eval $test_command; then
        print_success "Frontend tests passed!"
        frontend_passed=true
        cd ..
        return 0
    else
        print_error "Frontend tests failed!"
        frontend_passed=false
        cd ..
        return 1
    fi
}

# Function to run backend tests
run_backend_tests() {
    print_header "Running Backend Tests (FastAPI + Python)"
    
    cd backend
    
    # Check if virtual environment exists
    if [[ ! -d "venv" ]]; then
        print_warning "Python virtual environment not found. Creating..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    if [[ -f "venv/bin/activate" ]]; then
        source venv/bin/activate
    elif [[ -f "venv/Scripts/activate" ]]; then
        source venv/Scripts/activate
    else
        print_error "Could not find virtual environment activation script"
        cd ..
        return 1
    fi
    
    # Install dependencies if needed
    print_info "Ensuring Python dependencies are installed..."
    pip install -r requirements.txt > /dev/null
    
    local test_command="python -m pytest"
    
    if [[ "$VERBOSE" == true ]]; then
        test_command+=" -v"
    else
        test_command+=" -q"
    fi
    
    if [[ "$COVERAGE" == true ]]; then
        test_command+=" --cov=app --cov-report=term-missing"
    fi
    
    if [[ "$WATCH" == true ]]; then
        print_warning "Watch mode not available for backend tests (pytest-watch not configured)"
    fi
    
    print_info "Running: $test_command"
    
    if eval $test_command; then
        print_success "Backend tests passed!"
        backend_passed=true
        deactivate 2>/dev/null || true
        cd ..
        return 0
    else
        print_error "Backend tests failed!"
        backend_passed=false
        deactivate 2>/dev/null || true
        cd ..
        return 1
    fi
}

# Record start time
start_time=$(date +%s)

# Run tests based on target
exit_code=0

case $TARGET in
    "frontend")
        run_frontend_tests || exit_code=$?
        ;;
    "backend")
        run_backend_tests || exit_code=$?
        ;;
    "all")
        print_info "Running all tests..."
        
        frontend_exit_code=0
        backend_exit_code=0
        
        run_frontend_tests || frontend_exit_code=$?
        run_backend_tests || backend_exit_code=$?
        
        # Overall exit code is 0 only if both pass
        exit_code=$((frontend_exit_code > backend_exit_code ? frontend_exit_code : backend_exit_code))
        ;;
    *)
        print_error "Invalid target: $TARGET"
        print_info "Valid targets: all, frontend, backend"
        exit 1
        ;;
esac

# Calculate duration
end_time=$(date +%s)
duration=$((end_time - start_time))

# Summary
print_header "Test Summary"
print_info "Duration: ${duration} seconds"

if [[ "$TARGET" == "all" ]] || [[ "$TARGET" == "frontend" ]]; then
    if [[ "$frontend_passed" == true ]]; then
        print_success "Frontend: PASSED"
    else
        print_error "Frontend: FAILED"
    fi
fi

if [[ "$TARGET" == "all" ]] || [[ "$TARGET" == "backend" ]]; then
    if [[ "$backend_passed" == true ]]; then
        print_success "Backend: PASSED"
    else
        print_error "Backend: FAILED"
    fi
fi

if [[ $exit_code -eq 0 ]]; then
    print_success "All tests passed! 🎉"
else
    print_error "Some tests failed! 💥"
fi

print_header "Usage Examples"
print_info "Run all tests:           ./run-tests.sh"
print_info "Run frontend only:       ./run-tests.sh -t frontend"
print_info "Run backend only:        ./run-tests.sh -t backend"
print_info "Run with coverage:       ./run-tests.sh -c"
print_info "Run in watch mode:       ./run-tests.sh -t frontend -w"
print_info "Verbose output:          ./run-tests.sh -v"

exit $exit_code
