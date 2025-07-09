#!/bin/bash
set -eu

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Components to validate
COMPONENTS=(
    "ai-shared"
    "ai-db"
    "ai-frontend"
    "git-layer"
    "console"
    "mcp"
    "ai-hub"
)

# Track failures
declare -A FAILURES

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    
    if [ "$status" = "SUCCESS" ]; then
        echo -e "${GREEN}✓${NC} $message"
    elif [ "$status" = "FAIL" ]; then
        echo -e "${RED}✗${NC} $message"
    elif [ "$status" = "INFO" ]; then
        echo -e "${BLUE}→${NC} $message"
    elif [ "$status" = "WARN" ]; then
        echo -e "${YELLOW}!${NC} $message"
    fi
}

# Function to run a command and check result
run_check() {
    local component=$1
    local check_name=$2
    local command=$3
    
    if eval "$command" > /dev/null 2>&1; then
        print_status "SUCCESS" "$component: $check_name"
        return 0
    else
        print_status "FAIL" "$component: $check_name"
        FAILURES["$component:$check_name"]=1
        return 1
    fi
}

# Function to validate a single component
validate_component() {
    local component=$1
    
    echo
    echo -e "${BLUE}=== Validating $component ===${NC}"
    
    cd "$component"
    
    # Install dependencies
    print_status "INFO" "Installing dependencies..."
    if ! poetry install --quiet 2>/dev/null; then
        # Try again without quiet to see if it's a false positive
        if ! poetry install > /dev/null 2>&1; then
            print_status "FAIL" "$component: poetry install"
            FAILURES["$component:install"]=1
            cd ..
            return 1
        fi
    fi
    
    # Run checks (continue on failure)
    set +e
    
    # Type checking
    run_check "$component" "mypy" "poetry run mypy ."
    
    # Linting
    run_check "$component" "ruff" "poetry run ruff check ."
    
    # Format checking
    run_check "$component" "black" "poetry run black --check ."
    
    # Tests - run all tests but exclude integration tests
    if [ -d "tests" ]; then
        run_check "$component" "pytest" "poetry run pytest -m 'not integration' -v"
    else
        print_status "WARN" "$component: No tests directory found"
    fi
    
    # Build package
    run_check "$component" "build" "poetry build --quiet"
    
    set -e
    cd ..
}

# Function to run integration tests
run_integration_tests() {
    echo
    echo -e "${BLUE}=== Integration Tests ===${NC}"
    
    local has_integration=false
    
    for component in "${COMPONENTS[@]}"; do
        if [ -d "$component/tests" ]; then
            cd "$component"
            # Check if component has integration tests
            if poetry run pytest -m integration --co -q > /dev/null 2>&1; then
                has_integration=true
                print_status "INFO" "Running $component integration tests..."
                if run_check "$component" "integration tests" "poetry run pytest -m integration -v"; then
                    :
                fi
            fi
            cd ..
        fi
    done
    
    if [ "$has_integration" = false ]; then
        print_status "INFO" "No integration tests found"
    fi
}

# Main execution
main() {
    echo -e "${BLUE}AI-DB System Validation${NC}"
    echo "========================"
    
    # Check if we're in the workspace root
    if [ ! -f "pyproject.toml" ] || [ ! -d "ai-shared" ]; then
        print_status "FAIL" "Must run from workspace root directory"
        exit 1
    fi
    
    # Validate each component
    for component in "${COMPONENTS[@]}"; do
        validate_component "$component"
    done
    
    # Run integration tests if requested
    if [ "${1:-}" = "--with-integration" ]; then
        run_integration_tests
    else
        echo
        echo -e "${BLUE}=== Integration Tests ===${NC}"
        print_status "INFO" "Integration tests skipped (use --with-integration to run)"
    fi
    
    # Summary
    echo
    echo -e "${BLUE}=== Summary ===${NC}"
    
    if [ "${#FAILURES[@]}" -eq 0 ]; then
        print_status "SUCCESS" "All checks passed! 🎉"
        exit 0
    else
        print_status "FAIL" "Failed checks:"
        for failure in "${!FAILURES[@]}"; do
            echo "  - $failure"
        done
        exit 1
    fi
}

# Handle script arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [OPTIONS]"
        echo
        echo "Validates all components in the AI-DB monorepo"
        echo
        echo "Options:"
        echo "  --with-integration    Also run integration tests"
        echo "  --help               Show this help message"
        exit 0
        ;;
esac

# Run validation
main "$@"