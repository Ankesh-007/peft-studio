#!/bin/bash

# Verify Branch Protection Script for PEFT Studio
# This script checks if branch protection rules are properly configured

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Repository details
REPO_OWNER="${GITHUB_REPOSITORY_OWNER:-Ankesh-007}"
REPO_NAME="peft-studio"
REPO_FULL="${REPO_OWNER}/${REPO_NAME}"
BRANCH="main"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Branch Protection Verification${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if gh is installed
if ! command -v gh &> /dev/null; then
    echo -e "${RED}Error: GitHub CLI (gh) is not installed${NC}"
    echo "Please install it from: https://cli.github.com/"
    exit 1
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo -e "${RED}Error: Not authenticated with GitHub CLI${NC}"
    echo "Please run: gh auth login"
    exit 1
fi

echo -e "${GREEN}✓ GitHub CLI is installed and authenticated${NC}"
echo ""

# Check if repository exists
echo -e "${YELLOW}Checking repository: ${REPO_FULL}${NC}"
if ! gh repo view "${REPO_FULL}" &> /dev/null; then
    echo -e "${RED}✗ Repository not found: ${REPO_FULL}${NC}"
    echo "Please update REPO_OWNER in this script or set GITHUB_REPOSITORY_OWNER environment variable"
    exit 1
fi
echo -e "${GREEN}✓ Repository exists${NC}"
echo ""

# Check branch protection
echo -e "${YELLOW}Checking branch protection for '${BRANCH}'...${NC}"

# Use GitHub API to check branch protection
PROTECTION_CHECK=$(gh api "repos/${REPO_FULL}/branches/${BRANCH}/protection" 2>&1 || echo "NOT_PROTECTED")

if [[ "$PROTECTION_CHECK" == *"NOT_PROTECTED"* ]] || [[ "$PROTECTION_CHECK" == *"404"* ]]; then
    echo -e "${RED}✗ Branch protection is NOT configured for '${BRANCH}'${NC}"
    echo ""
    echo -e "${YELLOW}To configure branch protection:${NC}"
    echo "1. Go to: https://github.com/${REPO_FULL}/settings/branches"
    echo "2. Click 'Add branch protection rule'"
    echo "3. Branch name pattern: ${BRANCH}"
    echo "4. Enable the following:"
    echo "   - Require a pull request before merging"
    echo "   - Require approvals (at least 1)"
    echo "   - Require status checks to pass before merging"
    echo "   - Require branches to be up to date before merging"
    echo "   - Require conversation resolution before merging"
    echo "   - Include administrators"
    echo ""
    echo "See .github/REPOSITORY_CONFIGURATION_GUIDE.md for detailed instructions"
    exit 1
else
    echo -e "${GREEN}✓ Branch protection is configured${NC}"
    echo ""
    
    # Parse and display protection details
    echo -e "${BLUE}Protection Details:${NC}"
    
    # Check for required pull request reviews
    if echo "$PROTECTION_CHECK" | grep -q "required_pull_request_reviews"; then
        echo -e "${GREEN}✓ Required pull request reviews enabled${NC}"
        
        # Extract required approving review count
        APPROVALS=$(echo "$PROTECTION_CHECK" | grep -o '"required_approving_review_count":[0-9]*' | grep -o '[0-9]*' || echo "0")
        echo "  - Required approvals: ${APPROVALS}"
        
        # Check dismiss stale reviews
        if echo "$PROTECTION_CHECK" | grep -q '"dismiss_stale_reviews":true'; then
            echo -e "  - ${GREEN}✓ Dismiss stale reviews enabled${NC}"
        else
            echo -e "  - ${YELLOW}⚠ Dismiss stale reviews not enabled${NC}"
        fi
    else
        echo -e "${YELLOW}⚠ Required pull request reviews not configured${NC}"
    fi
    
    # Check for required status checks
    if echo "$PROTECTION_CHECK" | grep -q "required_status_checks"; then
        echo -e "${GREEN}✓ Required status checks enabled${NC}"
        
        # Check strict mode
        if echo "$PROTECTION_CHECK" | grep -q '"strict":true'; then
            echo -e "  - ${GREEN}✓ Require branches to be up to date${NC}"
        else
            echo -e "  - ${YELLOW}⚠ Branches not required to be up to date${NC}"
        fi
        
        # Extract contexts (required checks)
        CONTEXTS=$(echo "$PROTECTION_CHECK" | grep -o '"contexts":\[[^]]*\]' || echo "")
        if [ -n "$CONTEXTS" ]; then
            echo "  - Required checks: ${CONTEXTS}"
        fi
    else
        echo -e "${YELLOW}⚠ Required status checks not configured${NC}"
    fi
    
    # Check enforce admins
    if echo "$PROTECTION_CHECK" | grep -q '"enforce_admins"'; then
        if echo "$PROTECTION_CHECK" | grep -q '"enabled":true'; then
            echo -e "${GREEN}✓ Enforce admins enabled${NC}"
        else
            echo -e "${YELLOW}⚠ Enforce admins not enabled${NC}"
        fi
    else
        echo -e "${YELLOW}⚠ Enforce admins not configured${NC}"
    fi
    
    # Check required conversation resolution
    if echo "$PROTECTION_CHECK" | grep -q '"required_conversation_resolution"'; then
        if echo "$PROTECTION_CHECK" | grep -q '"enabled":true'; then
            echo -e "${GREEN}✓ Required conversation resolution enabled${NC}"
        else
            echo -e "${YELLOW}⚠ Required conversation resolution not enabled${NC}"
        fi
    else
        echo -e "${YELLOW}⚠ Required conversation resolution not configured${NC}"
    fi
fi

echo ""

# Check for required workflows
echo -e "${YELLOW}Checking required workflow files...${NC}"

REQUIRED_WORKFLOWS=(
    ".github/workflows/ci.yml"
    ".github/workflows/test.yml"
    ".github/workflows/build.yml"
    ".github/workflows/code-quality.yml"
)

MISSING_WORKFLOWS=0
for workflow in "${REQUIRED_WORKFLOWS[@]}"; do
    if [ -f "$workflow" ]; then
        echo -e "${GREEN}✓ Found: $workflow${NC}"
    else
        echo -e "${RED}✗ Missing: $workflow${NC}"
        MISSING_WORKFLOWS=$((MISSING_WORKFLOWS + 1))
    fi
done

if [ $MISSING_WORKFLOWS -gt 0 ]; then
    echo ""
    echo -e "${YELLOW}⚠ $MISSING_WORKFLOWS required workflow(s) missing${NC}"
    echo "These workflows should be present and added as required status checks"
fi

echo ""

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Verification Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

if [[ "$PROTECTION_CHECK" != *"NOT_PROTECTED"* ]] && [[ "$PROTECTION_CHECK" != *"404"* ]] && [ $MISSING_WORKFLOWS -eq 0 ]; then
    echo -e "${GREEN}✓ Branch protection is properly configured${NC}"
    echo -e "${GREEN}✓ All required workflows are present${NC}"
    echo ""
    echo "Repository: https://github.com/${REPO_FULL}"
    echo "Branch protection: https://github.com/${REPO_FULL}/settings/branch_protection_rules"
    echo ""
    echo -e "${GREEN}Branch protection verification passed!${NC}"
else
    echo -e "${YELLOW}⚠ Some configuration issues detected${NC}"
    echo ""
    echo "Please review the details above and:"
    echo "1. Configure missing branch protection rules"
    echo "2. Add missing workflow files"
    echo "3. Re-run this script to verify"
    echo ""
    echo "See .github/REPOSITORY_CONFIGURATION_GUIDE.md for detailed instructions"
fi

echo ""
