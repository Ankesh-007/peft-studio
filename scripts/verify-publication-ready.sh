#!/bin/bash
# PEFT Studio - Publication Readiness Verification Script
# This script verifies that the repository is ready for public release

set -e

echo "========================================"
echo "PEFT Studio Publication Readiness Check"
echo "========================================"
echo ""

all_passed=true

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to check if a file exists
check_file() {
    local path=$1
    local description=$2
    
    if [ -f "$path" ]; then
        echo -e "${GREEN}✓${NC} $description"
        return 0
    else
        echo -e "${RED}✗${NC} $description - MISSING"
        all_passed=false
        return 1
    fi
}

echo -e "${YELLOW}1. Checking Required Documentation Files...${NC}"
echo ""

check_file "README.md" "README.md exists"
check_file "CONTRIBUTING.md" "CONTRIBUTING.md exists"
check_file "CODE_OF_CONDUCT.md" "CODE_OF_CONDUCT.md exists"
check_file "SECURITY.md" "SECURITY.md exists"
check_file "LICENSE" "LICENSE exists"
check_file "CHANGELOG.md" "CHANGELOG.md exists"

echo ""
echo -e "${YELLOW}2. Checking GitHub Templates...${NC}"
echo ""

check_file ".github/ISSUE_TEMPLATE/bug_report.md" "Bug report template exists"
check_file ".github/ISSUE_TEMPLATE/feature_request.md" "Feature request template exists"
check_file ".github/ISSUE_TEMPLATE/question.md" "Question template exists"
check_file ".github/pull_request_template.md" "Pull request template exists"

echo ""
echo -e "${YELLOW}3. Checking CI/CD Workflows...${NC}"
echo ""

check_file ".github/workflows/ci.yml" "CI workflow exists"
check_file ".github/workflows/security.yml" "Security workflow exists"

echo ""
echo -e "${YELLOW}4. Checking Git Configuration...${NC}"
echo ""

# Check if git remote is configured
remote_url=$(git remote get-url origin 2>&1 || echo "")
if [[ "$remote_url" == *"github.com/Ankesh-007/peft-studio"* ]]; then
    echo -e "${GREEN}✓${NC} Git remote configured correctly"
else
    echo -e "${RED}✗${NC} Git remote not configured correctly"
    all_passed=false
fi

# Check if v1.0.0 tag exists
if git tag -l "v1.0.0" | grep -q "v1.0.0"; then
    echo -e "${GREEN}✓${NC} Version tag v1.0.0 exists"
else
    echo -e "${RED}✗${NC} Version tag v1.0.0 missing"
    all_passed=false
fi

# Check if on main branch
current_branch=$(git branch --show-current 2>&1 || echo "")
if [ "$current_branch" = "main" ]; then
    echo -e "${GREEN}✓${NC} On main branch"
else
    echo -e "${YELLOW}⚠${NC} Not on main branch (current: $current_branch)"
fi

# Check if there are uncommitted changes
if [ -z "$(git status --porcelain)" ]; then
    echo -e "${GREEN}✓${NC} No uncommitted changes"
else
    echo -e "${YELLOW}⚠${NC} Uncommitted changes detected"
    echo "  Consider committing or stashing changes before publication"
fi

echo ""
echo -e "${YELLOW}5. Checking Package Configuration...${NC}"
echo ""

# Check package.json
if [ -f "package.json" ]; then
    if grep -q "github.com/Ankesh-007/peft-studio" package.json; then
        echo -e "${GREEN}✓${NC} package.json repository URL correct"
    else
        echo -e "${RED}✗${NC} package.json repository URL incorrect"
        all_passed=false
    fi
    
    if grep -q '"license": "MIT"' package.json; then
        echo -e "${GREEN}✓${NC} package.json license set to MIT"
    else
        echo -e "${RED}✗${NC} package.json license not set to MIT"
        all_passed=false
    fi
    
    if grep -q '"keywords"' package.json; then
        echo -e "${GREEN}✓${NC} package.json has keywords"
    else
        echo -e "${YELLOW}⚠${NC} package.json missing keywords"
    fi
fi

echo ""
echo -e "${YELLOW}6. Checking Security...${NC}"
echo ""

# Check for .env files
env_files=$(find . -name ".env*" -not -name ".env.example" -type f 2>/dev/null || true)
if [ -z "$env_files" ]; then
    echo -e "${GREEN}✓${NC} No .env files found"
else
    echo -e "${RED}✗${NC} .env files found - REMOVE BEFORE PUBLICATION"
    echo "$env_files" | while read -r file; do
        echo -e "  ${RED}- $file${NC}"
    done
    all_passed=false
fi

# Check for database files
db_files=$(find . \( -name "*.db" -o -name "*.sqlite*" \) -type f 2>/dev/null || true)
if [ -z "$db_files" ]; then
    echo -e "${GREEN}✓${NC} No database files found"
else
    echo -e "${RED}✗${NC} Database files found - REMOVE BEFORE PUBLICATION"
    echo "$db_files" | while read -r file; do
        echo -e "  ${RED}- $file${NC}"
    done
    all_passed=false
fi

echo ""
echo -e "${YELLOW}7. Checking Build System...${NC}"
echo ""

# Check if node_modules exists
if [ -d "node_modules" ]; then
    echo -e "${GREEN}✓${NC} node_modules directory exists"
else
    echo -e "${YELLOW}⚠${NC} node_modules not found - run 'npm install'"
fi

# Check if backend dependencies are installed
if [ -d "backend/venv" ] || [ -d "backend/.venv" ]; then
    echo -e "${GREEN}✓${NC} Python virtual environment exists"
else
    echo -e "${YELLOW}⚠${NC} Python virtual environment not found"
fi

echo ""
echo "========================================"

if [ "$all_passed" = true ]; then
    echo -e "${GREEN}✓ ALL CHECKS PASSED - READY FOR PUBLICATION${NC}"
    echo ""
    echo -e "${CYAN}Next steps:${NC}"
    echo "1. Review PUBLICATION_GUIDE.md for detailed instructions"
    echo "2. Make repository public on GitHub"
    echo "3. Create release v1.0.0"
    echo "4. Verify public access"
    echo "5. Monitor initial feedback"
    exit 0
else
    echo -e "${RED}✗ SOME CHECKS FAILED - FIX ISSUES BEFORE PUBLICATION${NC}"
    echo ""
    echo -e "${YELLOW}Please address the issues above before making the repository public.${NC}"
    exit 1
fi
