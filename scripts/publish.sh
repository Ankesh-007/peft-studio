#!/bin/bash
# Publish Verification Script for Unix (Bash)
# Runs all pre-publication checks and generates a verification report

set -e

VERBOSE=false
SKIP_TESTS=false
SKIP_BUILD=false
CHECKS_PASSED=0
CHECKS_FAILED=0
CHECKS_WARNING=0
START_TIME=$(date +%s)

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        *)
            shift
            ;;
    esac
done

# Color output functions
print_success() {
    echo -e "\033[0;32m✓ $1\033[0m"
    ((CHECKS_PASSED++))
}

print_failure() {
    echo -e "\033[0;31m✗ $1\033[0m"
    ((CHECKS_FAILED++))
}

print_warning() {
    echo -e "\033[0;33m⚠ $1\033[0m"
    ((CHECKS_WARNING++))
}

print_info() {
    echo -e "\033[0;36mℹ $1\033[0m"
}

print_section() {
    echo -e "\n\033[0;35m========================================"
    echo -e " $1"
    echo -e "========================================\033[0m\n"
}

run_check() {
    local name="$1"
    local command="$2"
    
    echo -e "\nRunning: $name"
    if eval "$command" > /dev/null 2>&1; then
        print_success "$name"
        return 0
    else
        print_failure "$name"
        return 1
    fi
}

print_section "PEFT Studio Publish Verification"
print_info "Starting comprehensive pre-publication checks..."
print_info "Started at: $(date '+%Y-%m-%d %H:%M:%S')"

# Check 1: Security Scan
print_section "1. Security Verification"

if [ -f "scripts/security-scan.sh" ]; then
    if bash scripts/security-scan.sh $([ "$VERBOSE" = true ] && echo "-v"); then
        print_success "Security Scan"
    else
        print_failure "Security Scan"
    fi
else
    print_warning "Security scan script not found"
fi

# Check 2: Required Files
print_section "2. Required Files Check"

REQUIRED_FILES=(
    "README.md"
    "LICENSE"
    "CONTRIBUTING.md"
    "CODE_OF_CONDUCT.md"
    "SECURITY.md"
    "CHANGELOG.md"
    ".gitignore"
    "package.json"
    "package-lock.json"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        print_success "Found: $file"
    else
        print_failure "Missing: $file"
    fi
done

# Check 3: GitHub Templates
print_section "3. GitHub Templates Check"

GITHUB_TEMPLATES=(
    ".github/ISSUE_TEMPLATE/bug_report.md"
    ".github/ISSUE_TEMPLATE/feature_request.md"
    ".github/ISSUE_TEMPLATE/question.md"
    ".github/pull_request_template.md"
    ".github/workflows/ci.yml"
    ".github/workflows/security.yml"
)

for template in "${GITHUB_TEMPLATES[@]}"; do
    if [ -f "$template" ]; then
        print_success "Found: $template"
    else
        print_failure "Missing: $template"
    fi
done

# Check 4: Package.json Metadata
print_section "4. Package.json Metadata Check"

if [ -f "package.json" ]; then
    # Check required fields using jq if available, otherwise use grep
    if command -v jq > /dev/null 2>&1; then
        name=$(jq -r '.name' package.json)
        version=$(jq -r '.version' package.json)
        description=$(jq -r '.description' package.json)
        author=$(jq -r '.author' package.json)
        license=$(jq -r '.license' package.json)
        repository=$(jq -r '.repository.url' package.json)
        homepage=$(jq -r '.homepage' package.json)
        bugs=$(jq -r '.bugs.url' package.json)
        keywords=$(jq -r '.keywords | length' package.json)
        
        [ "$name" != "null" ] && [ -n "$name" ] && print_success "package.json has valid 'name': $name" || print_failure "package.json missing or invalid 'name'"
        [ "$version" != "null" ] && [ -n "$version" ] && print_success "package.json has valid 'version': $version" || print_failure "package.json missing or invalid 'version'"
        [ "$description" != "null" ] && [ -n "$description" ] && print_success "package.json has valid 'description'" || print_failure "package.json missing or invalid 'description'"
        [ "$author" != "null" ] && [ -n "$author" ] && print_success "package.json has valid 'author'" || print_failure "package.json missing or invalid 'author'"
        [ "$license" != "null" ] && [ -n "$license" ] && print_success "package.json has valid 'license': $license" || print_failure "package.json missing or invalid 'license'"
        [ "$repository" != "null" ] && [ -n "$repository" ] && ! echo "$repository" | grep -q "placeholder" && print_success "package.json has valid 'repository'" || print_failure "package.json missing or invalid 'repository'"
        [ "$homepage" != "null" ] && [ -n "$homepage" ] && ! echo "$homepage" | grep -q "placeholder" && print_success "package.json has valid 'homepage'" || print_failure "package.json missing or invalid 'homepage'"
        [ "$bugs" != "null" ] && [ -n "$bugs" ] && ! echo "$bugs" | grep -q "placeholder" && print_success "package.json has valid 'bugs'" || print_failure "package.json missing or invalid 'bugs'"
        
        if [ "$keywords" != "null" ] && [ "$keywords" -gt 0 ]; then
            print_success "package.json has $keywords keywords"
        else
            print_warning "package.json has no keywords (affects discoverability)"
        fi
    else
        print_warning "jq not installed, skipping detailed package.json validation"
    fi
else
    print_failure "package.json not found"
fi

# Check 5: Dependencies Security
print_section "5. Dependencies Security Check"

print_info "Running npm audit..."
if npm audit --json > /tmp/audit.json 2>&1; then
    if command -v jq > /dev/null 2>&1; then
        total=$(jq -r '.metadata.vulnerabilities.total' /tmp/audit.json 2>/dev/null || echo "0")
        critical=$(jq -r '.metadata.vulnerabilities.critical' /tmp/audit.json 2>/dev/null || echo "0")
        high=$(jq -r '.metadata.vulnerabilities.high' /tmp/audit.json 2>/dev/null || echo "0")
        moderate=$(jq -r '.metadata.vulnerabilities.moderate' /tmp/audit.json 2>/dev/null || echo "0")
        low=$(jq -r '.metadata.vulnerabilities.low' /tmp/audit.json 2>/dev/null || echo "0")
        
        if [ "$total" -eq 0 ]; then
            print_success "No npm vulnerabilities found"
        elif [ "$critical" -gt 0 ] || [ "$high" -gt 0 ]; then
            print_failure "Found $critical critical and $high high severity vulnerabilities"
        elif [ "$moderate" -gt 0 ]; then
            print_warning "Found $moderate moderate severity vulnerabilities"
        else
            print_success "Only $low low severity vulnerabilities found"
        fi
    else
        print_warning "jq not installed, cannot parse audit results"
    fi
    rm -f /tmp/audit.json
else
    print_warning "npm audit check completed with warnings"
fi

# Check 6: Linting
print_section "6. Code Quality Check"

if [ "$SKIP_TESTS" = false ]; then
    print_info "Running linting..."
    if npm run lint > /dev/null 2>&1; then
        print_success "Linting passed"
    else
        print_failure "Linting failed"
    fi
else
    print_info "Skipping linting (--skip-tests flag)"
fi

# Check 7: Tests
print_section "7. Test Suite Check"

if [ "$SKIP_TESTS" = false ]; then
    print_info "Running frontend tests..."
    if npm test -- --run > /dev/null 2>&1; then
        print_success "Frontend tests passed"
    else
        print_failure "Frontend tests failed"
    fi
    
    print_info "Running backend tests..."
    if [ -f "backend/requirements.txt" ]; then
        if (cd backend && pytest > /dev/null 2>&1); then
            print_success "Backend tests passed"
        else
            print_failure "Backend tests failed"
        fi
    else
        print_info "No backend tests found"
    fi
else
    print_info "Skipping tests (--skip-tests flag)"
fi

# Check 8: Build
print_section "8. Build Verification"

if [ "$SKIP_BUILD" = false ]; then
    print_info "Running build..."
    if npm run build > /dev/null 2>&1 && [ -d "dist" ]; then
        print_success "Build completed successfully"
    else
        print_failure "Build failed or dist directory not created"
    fi
else
    print_info "Skipping build (--skip-build flag)"
fi

# Check 9: Git Status
print_section "9. Git Repository Check"

git_status=$(git status --porcelain)
if [ -z "$git_status" ]; then
    print_success "Working directory is clean"
else
    print_warning "Working directory has uncommitted changes"
    if [ "$VERBOSE" = true ]; then
        echo "$git_status"
    fi
fi

# Check for version tag
if [ -f "package.json" ]; then
    if command -v jq > /dev/null 2>&1; then
        current_version=$(jq -r '.version' package.json)
        if git tag -l "v$current_version" | grep -q "v$current_version"; then
            print_success "Version tag v$current_version exists"
        else
            print_warning "Version tag v$current_version does not exist"
        fi
    fi
fi

# Check 10: Documentation Links
print_section "10. Documentation Check"

print_info "Checking README.md links..."
if [ -f "README.md" ]; then
    # Check for placeholder URLs
    if grep -iE "placeholder|example\.com|your-username" README.md > /dev/null 2>&1; then
        print_failure "README.md contains placeholder URLs"
    else
        print_success "README.md has no obvious placeholder URLs"
    fi
    
    # Check for badges
    if grep -E "!\[.*\]\(https://img\.shields\.io" README.md > /dev/null 2>&1; then
        print_success "README.md contains badges"
    else
        print_warning "README.md has no badges"
    fi
else
    print_failure "README.md not found"
fi

# Generate Report
print_section "Verification Report"

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
TOTAL_CHECKS=$((CHECKS_PASSED + CHECKS_FAILED + CHECKS_WARNING))

echo -e "\033[0;36mVerification completed at: $(date '+%Y-%m-%d %H:%M:%S')\033[0m"
echo -e "\033[0;36mDuration: $DURATION seconds\033[0m"
echo ""
echo -e "\033[0;36mTotal checks: $TOTAL_CHECKS\033[0m"
echo -e "\033[0;32mPassed: $CHECKS_PASSED\033[0m"
echo -e "\033[0;31mFailed: $CHECKS_FAILED\033[0m"
echo -e "\033[0;33mWarnings: $CHECKS_WARNING\033[0m"
echo ""

# Save report to file
REPORT_PATH="publish-verification-report.txt"
cat > "$REPORT_PATH" << EOF
PEFT Studio Publish Verification Report
========================================
Generated: $(date '+%Y-%m-%d %H:%M:%S')
Duration: $DURATION seconds

Summary:
--------
Total checks: $TOTAL_CHECKS
Passed: $CHECKS_PASSED
Failed: $CHECKS_FAILED
Warnings: $CHECKS_WARNING

Status: $([ $CHECKS_FAILED -eq 0 ] && echo "READY FOR PUBLICATION" || echo "NOT READY - FIX ISSUES ABOVE")
EOF

print_info "Report saved to: $REPORT_PATH"

# Final verdict
echo ""
if [ $CHECKS_FAILED -eq 0 ]; then
    echo -e "\033[0;32m✓ Repository is READY for publication!\033[0m"
    echo -e "\033[0;32m✓ All critical checks passed\033[0m"
    if [ $CHECKS_WARNING -gt 0 ]; then
        echo -e "\033[0;33m⚠ Consider addressing $CHECKS_WARNING warning(s) before publishing\033[0m"
    fi
    exit 0
else
    echo -e "\033[0;31m✗ Repository is NOT READY for publication\033[0m"
    echo -e "\033[0;31m✗ Please fix $CHECKS_FAILED failed check(s)\033[0m"
    exit 1
fi
