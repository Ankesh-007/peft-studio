#!/bin/bash
# Security Scan Script for PEFT Studio
# This script scans for potential security issues before public release

echo "🔒 PEFT Studio Security Scan"
echo "================================"
echo ""

issues=0

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to search and report
search_pattern() {
    local pattern=$1
    local description=$2
    shift 2
    local exclude_args=("$@")
    
    echo -e "${YELLOW}Checking for $description...${NC}"
    
    local results
    results=$(git grep -i "$pattern" "${exclude_args[@]}" 2>/dev/null)
    
    if [ -n "$results" ]; then
        echo -e "  ${RED}⚠️  Found potential issues:${NC}"
        echo "$results" | while read -r line; do
            echo -e "    ${RED}$line${NC}"
        done
        return 1
    else
        echo -e "  ${GREEN}✅ No issues found${NC}"
        return 0
    fi
}

# Scan for API keys
search_pattern "api[_-]key" "API keys" -- ':!node_modules' ':!*.md' ':!.git'
issues=$((issues + $?))

# Scan for tokens
search_pattern 'token\s*=\s*['\''"]' "hardcoded tokens" -- ':!node_modules' ':!*.md' ':!.git'
issues=$((issues + $?))

# Scan for passwords
search_pattern 'password\s*=\s*['\''"]' "hardcoded passwords" -- ':!node_modules' ':!*.md' ':!.git'
issues=$((issues + $?))

# Scan for secrets
search_pattern 'secret\s*=\s*['\''"]' "hardcoded secrets" -- ':!node_modules' ':!*.md' ':!.git'
issues=$((issues + $?))

# Scan for AWS keys
search_pattern "AKIA[0-9A-Z]{16}" "AWS access keys" -- ':!node_modules' ':!.git'
issues=$((issues + $?))

# Scan for private keys
search_pattern "BEGIN.*PRIVATE KEY" "private keys" -- ':!node_modules' ':!.git'
issues=$((issues + $?))

# Scan for email addresses (excluding documentation)
echo -e "${YELLOW}Checking for email addresses...${NC}"
emails=$(git grep -E "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}" -- ':!*.md' ':!LICENSE' ':!node_modules' 2>/dev/null)
if [ -n "$emails" ]; then
    echo -e "  ${YELLOW}⚠️  Found email addresses (review if they should be public):${NC}"
    echo "$emails" | while read -r line; do
        echo -e "    ${YELLOW}$line${NC}"
    done
fi

# Check .env files
echo -e "${YELLOW}Checking .env files...${NC}"
env_files=$(find . -name ".env*" -not -name ".env.example" -not -path "*/node_modules/*" -not -path "*/.git/*" 2>/dev/null)
if [ -n "$env_files" ]; then
    echo -e "  ${YELLOW}⚠️  Found .env files (ensure they're in .gitignore):${NC}"
    echo "$env_files" | while read -r line; do
        echo -e "    ${YELLOW}$line${NC}"
    done
    issues=$((issues + 1))
else
    echo -e "  ${GREEN}✅ No .env files found${NC}"
fi

# Check for database files
echo -e "${YELLOW}Checking for database files...${NC}"
db_files=$(find . \( -name "*.db" -o -name "*.sqlite" -o -name "*.sqlite3" \) -not -path "*/node_modules/*" -not -path "*/.git/*" 2>/dev/null)
if [ -n "$db_files" ]; then
    echo -e "  ${YELLOW}⚠️  Found database files (ensure they're in .gitignore):${NC}"
    echo "$db_files" | while read -r line; do
        echo -e "    ${YELLOW}$line${NC}"
    done
    issues=$((issues + 1))
else
    echo -e "  ${GREEN}✅ No database files found${NC}"
fi

# Check for large files
echo -e "${YELLOW}Checking for large files (>10MB)...${NC}"
large_files=$(find . -type f -size +10M -not -path "*/node_modules/*" -not -path "*/.git/*" 2>/dev/null)
if [ -n "$large_files" ]; then
    echo -e "  ${YELLOW}⚠️  Found large files:${NC}"
    echo "$large_files" | while read -r file; do
        size=$(du -h "$file" | cut -f1)
        echo -e "    ${YELLOW}$file ($size)${NC}"
    done
fi

# Check .gitignore
echo -e "${YELLOW}Checking .gitignore...${NC}"
if [ -f ".gitignore" ]; then
    required_patterns=(".env" "*.db" "*.sqlite" "node_modules" "__pycache__")
    missing=()
    
    for pattern in "${required_patterns[@]}"; do
        if ! grep -q "$pattern" .gitignore; then
            missing+=("$pattern")
        fi
    done
    
    if [ ${#missing[@]} -gt 0 ]; then
        echo -e "  ${YELLOW}⚠️  Missing patterns in .gitignore:${NC}"
        for pattern in "${missing[@]}"; do
            echo -e "    ${YELLOW}$pattern${NC}"
        done
    else
        echo -e "  ${GREEN}✅ .gitignore looks good${NC}"
    fi
else
    echo -e "  ${RED}❌ .gitignore not found!${NC}"
    issues=$((issues + 1))
fi

# Summary
echo ""
echo "================================"
if [ $issues -eq 0 ]; then
    echo -e "${GREEN}✅ Security scan complete - No critical issues found!${NC}"
    echo -e "${YELLOW}Review any warnings above before publishing.${NC}"
else
    echo -e "${RED}⚠️  Security scan found $issues potential issue(s)${NC}"
    echo -e "${RED}Please review and fix before publishing!${NC}"
    exit 1
fi

echo ""
echo -e "${CYAN}Next steps:${NC}"
echo "1. Review any warnings above"
echo "2. Run: npm test && cd backend && pytest"
echo "3. Run: npm run lint"
echo "4. Review PUBLIC_RELEASE_CHECKLIST.md"
echo "5. Test fresh clone and build"
