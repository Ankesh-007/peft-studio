#!/bin/bash
# Security Scanning Script for Unix (Bash)
# Scans the repository for sensitive data, credentials, and security issues

set -e

VERBOSE=false
ISSUES_FOUND=0
WARNINGS_FOUND=0

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--verbose)
            VERBOSE=true
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
}

print_error() {
    echo -e "\033[0;31m✗ $1\033[0m"
    ((ISSUES_FOUND++))
}

print_warning() {
    echo -e "\033[0;33m⚠ $1\033[0m"
    ((WARNINGS_FOUND++))
}

print_info() {
    echo -e "\033[0;36mℹ $1\033[0m"
}

print_section() {
    echo -e "\n\033[0;35m========================================"
    echo -e " $1"
    echo -e "========================================\033[0m\n"
}

# Patterns to search for (using grep -E extended regex)
declare -A SENSITIVE_PATTERNS=(
    ["API Keys"]="api[_-]?key\s*[:=]\s*['\"\`][a-zA-Z0-9_\-]{20,}['\"\`]|apikey\s*[:=]\s*['\"\`][a-zA-Z0-9_\-]{20,}['\"\`]"
    ["AWS Credentials"]="AKIA[0-9A-Z]{16}|aws[_-]?secret[_-]?access[_-]?key|aws[_-]?access[_-]?key[_-]?id"
    ["Private Keys"]="-----BEGIN (RSA |DSA |EC )?PRIVATE KEY-----|-----BEGIN OPENSSH PRIVATE KEY-----"
    ["Tokens"]="token\s*[:=]\s*['\"\`][a-zA-Z0-9_\-\.]{20,}['\"\`]|bearer\s+[a-zA-Z0-9_\-\.]{20,}|github[_-]?token|gh[ps]_[a-zA-Z0-9]{36,}"
    ["Passwords"]="password\s*[:=]\s*['\"\`][^'\"\`]{8,}['\"\`]|passwd\s*[:=]\s*['\"\`][^'\"\`]{8,}['\"\`]|pwd\s*[:=]\s*['\"\`][^'\"\`]{8,}['\"\`]"
    ["Database URLs"]="mongodb(\+srv)?://[^\s]+|postgres(ql)?://[^\s]+|mysql://[^\s]+"
    ["Email Addresses"]="[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    ["IP Addresses"]="\\b([0-9]{1,3}\\.){3}[0-9]{1,3}\\b"
)

# Files and directories to exclude
EXCLUDE_PATTERNS=(
    "node_modules"
    ".git"
    "dist"
    "build"
    ".hypothesis"
    "__pycache__"
    "*.min.js"
    "*.map"
    "package-lock.json"
    "*.log"
    ".pytest_cache"
    "artifacts"
    "checkpoints"
)

# Build find exclude arguments
FIND_EXCLUDE_ARGS=""
for pattern in "${EXCLUDE_PATTERNS[@]}"; do
    FIND_EXCLUDE_ARGS="$FIND_EXCLUDE_ARGS -not -path '*/$pattern/*' -not -name '$pattern'"
done

print_section "PEFT Studio Security Scanner"
print_info "Starting security scan of repository..."
print_info "Scan started at: $(date '+%Y-%m-%d %H:%M:%S')"

# Check 1: Scan for sensitive patterns in files
print_section "1. Scanning for Sensitive Data Patterns"

# Get list of files to scan
FILES_TO_SCAN=$(eval "find . -type f $FIND_EXCLUDE_ARGS" 2>/dev/null || true)
TOTAL_FILES=$(echo "$FILES_TO_SCAN" | wc -l)
print_info "Scanning $TOTAL_FILES files..."

for category in "${!SENSITIVE_PATTERNS[@]}"; do
    echo -e "\nChecking for: $category"
    pattern="${SENSITIVE_PATTERNS[$category]}"
    found_issues=false
    
    while IFS= read -r file; do
        if [ -f "$file" ] && [ -r "$file" ]; then
            # Skip binary files
            if file "$file" | grep -q "text"; then
                if grep -iE "$pattern" "$file" > /dev/null 2>&1; then
                    if [ "$found_issues" = false ]; then
                        found_issues=true
                    fi
                    print_error "Found in: $file"
                    if [ "$VERBOSE" = true ]; then
                        grep -iE "$pattern" "$file" | sed 's/^/  Match: /'
                    fi
                fi
            fi
        fi
    done <<< "$FILES_TO_SCAN"
    
    if [ "$found_issues" = false ]; then
        print_success "No $category found"
    fi
done

# Check 2: Verify .gitignore coverage
print_section "2. Verifying .gitignore Coverage"

REQUIRED_GITIGNORE_PATTERNS=(
    "*.env"
    ".env"
    ".env.local"
    "*.db"
    "*.sqlite"
    "*.sqlite3"
    "node_modules/"
    "__pycache__/"
    "*.pyc"
    ".pytest_cache/"
    "dist/"
    "build/"
    "*.log"
)

if [ -f ".gitignore" ]; then
    for pattern in "${REQUIRED_GITIGNORE_PATTERNS[@]}"; do
        if grep -qF "$pattern" .gitignore; then
            print_success "Pattern '$pattern' is in .gitignore"
        else
            print_warning "Pattern '$pattern' is missing from .gitignore"
        fi
    done
else
    print_error ".gitignore file not found!"
fi

# Check 3: Verify no actual sensitive files exist
print_section "3. Checking for Sensitive Files"

SENSITIVE_FILES=(
    "*.env"
    ".env"
    ".env.local"
    ".env.production"
    "*.db"
    "*.sqlite"
    "*.sqlite3"
    "*.pem"
    "*.key"
    "id_rsa"
    "id_dsa"
)

found_sensitive_files=false
for pattern in "${SENSITIVE_FILES[@]}"; do
    files=$(eval "find . -type f -name '$pattern' $FIND_EXCLUDE_ARGS" 2>/dev/null || true)
    if [ -n "$files" ]; then
        while IFS= read -r file; do
            print_error "Found sensitive file: $file"
            found_sensitive_files=true
        done <<< "$files"
    fi
done

if [ "$found_sensitive_files" = false ]; then
    print_success "No sensitive files found in repository"
fi

# Check 4: Scan git history for sensitive data
print_section "4. Scanning Git History"

print_info "Checking for sensitive patterns in commit history..."

SENSITIVE_KEYWORDS=("password" "secret" "key" "token" "credential" "api_key")
history_issues=false

for keyword in "${SENSITIVE_KEYWORDS[@]}"; do
    result=$(git log --all --full-history --source -- "*$keyword*" 2>&1 || true)
    if [ -n "$result" ] && ! echo "$result" | grep -q "fatal"; then
        print_warning "Found commits referencing '$keyword' in file paths"
        history_issues=true
        if [ "$VERBOSE" = true ]; then
            echo "$result"
        fi
    fi
done

if [ "$history_issues" = false ]; then
    print_success "No obvious sensitive data patterns in git history"
fi

# Check 5: Check for large files
print_section "5. Checking for Large Files"

print_info "Scanning for files larger than 1MB..."

large_files=$(eval "find . -type f -size +1M $FIND_EXCLUDE_ARGS" 2>/dev/null || true)

if [ -n "$large_files" ]; then
    while IFS= read -r file; do
        size=$(du -h "$file" | cut -f1)
        print_warning "Large file found: $file ($size)"
    done <<< "$large_files"
else
    print_success "No files larger than 1MB found"
fi

# Check 6: Verify environment variable usage
print_section "6. Verifying Environment Variable Usage"

print_info "Checking for hardcoded configuration..."

config_files=$(eval "find . -type f \( -name '*.ts' -o -name '*.tsx' -o -name '*.js' -o -name '*.jsx' -o -name '*.py' \) $FIND_EXCLUDE_ARGS" 2>/dev/null || true)

hardcoded_config_found=false
while IFS= read -r file; do
    if [ -f "$file" ] && [ -r "$file" ]; then
        # Look for hardcoded URLs (excluding localhost/127.0.0.1)
        if grep -E 'https?://(?!localhost|127\.0\.0\.1)[a-zA-Z0-9.-]+' "$file" > /dev/null 2>&1; then
            # Exclude common safe patterns
            if ! grep -E 'github\.com|example\.com|huggingface\.co' "$file" > /dev/null 2>&1; then
                print_warning "Potential hardcoded URL in: $file"
                hardcoded_config_found=true
            fi
        fi
    fi
done <<< "$config_files"

if [ "$hardcoded_config_found" = false ]; then
    print_success "No obvious hardcoded configuration found"
fi

# Summary
print_section "Security Scan Summary"

echo -e "\033[0;36mScan completed at: $(date '+%Y-%m-%d %H:%M:%S')\033[0m"
echo -e "\033[0;36mFiles scanned: $TOTAL_FILES\033[0m"
echo ""

if [ $ISSUES_FOUND -eq 0 ] && [ $WARNINGS_FOUND -eq 0 ]; then
    echo -e "\033[0;32m✓ No security issues found!\033[0m"
    echo -e "\033[0;32m✓ Repository appears safe for public release\033[0m"
    exit 0
else
    if [ $ISSUES_FOUND -gt 0 ]; then
        echo -e "\033[0;31m✗ Found $ISSUES_FOUND security issue(s)\033[0m"
    fi
    if [ $WARNINGS_FOUND -gt 0 ]; then
        echo -e "\033[0;33m⚠ Found $WARNINGS_FOUND warning(s)\033[0m"
    fi
    echo ""
    echo -e "\033[0;33mPlease review and fix the issues above before publishing.\033[0m"
    
    if [ $ISSUES_FOUND -gt 0 ]; then
        exit 1
    else
        exit 0
    fi
fi
