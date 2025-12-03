#!/bin/bash

# Verify GitHub Actions Workflows Script for PEFT Studio
# This script validates that all required workflow files exist and are properly configured

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}GitHub Actions Workflow Verification${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Required workflow files
REQUIRED_WORKFLOWS=(
    ".github/workflows/ci.yml"
    ".github/workflows/test.yml"
    ".github/workflows/build.yml"
    ".github/workflows/code-quality.yml"
    ".github/workflows/deploy.yml"
    ".github/workflows/release.yml"
    ".github/workflows/build-installers.yml"
    ".github/workflows/nightly.yml"
)

# Optional but recommended workflows
OPTIONAL_WORKFLOWS=(
    ".github/workflows/verify-branch-protection.yml"
)

# Check for required workflows
echo -e "${YELLOW}Checking required workflow files...${NC}"
MISSING_REQUIRED=0
for workflow in "${REQUIRED_WORKFLOWS[@]}"; do
    if [ -f "$workflow" ]; then
        echo -e "${GREEN}✓ Found: $workflow${NC}"
    else
        echo -e "${RED}✗ Missing: $workflow${NC}"
        MISSING_REQUIRED=$((MISSING_REQUIRED + 1))
    fi
done

echo ""

# Check for optional workflows
echo -e "${YELLOW}Checking optional workflow files...${NC}"
for workflow in "${OPTIONAL_WORKFLOWS[@]}"; do
    if [ -f "$workflow" ]; then
        echo -e "${GREEN}✓ Found: $workflow${NC}"
    else
        echo -e "${YELLOW}ℹ Optional: $workflow (not present)${NC}"
    fi
done

echo ""

# Validate YAML syntax if yamllint is available
if command -v yamllint &> /dev/null; then
    echo -e "${YELLOW}Validating YAML syntax...${NC}"
    YAML_ERRORS=0
    for workflow in "${REQUIRED_WORKFLOWS[@]}"; do
        if [ -f "$workflow" ]; then
            if yamllint "$workflow" &> /dev/null; then
                echo -e "${GREEN}✓ Valid YAML: $workflow${NC}"
            else
                echo -e "${RED}✗ Invalid YAML: $workflow${NC}"
                YAML_ERRORS=$((YAML_ERRORS + 1))
            fi
        fi
    done
    echo ""
else
    echo -e "${YELLOW}ℹ yamllint not installed, skipping YAML validation${NC}"
    echo "  Install with: pip install yamllint"
    echo ""
fi

# Check workflow triggers
echo -e "${YELLOW}Checking workflow triggers...${NC}"
for workflow in "${REQUIRED_WORKFLOWS[@]}"; do
    if [ -f "$workflow" ]; then
        filename=$(basename "$workflow")
        
        # Check for push trigger
        if grep -q "push:" "$workflow"; then
            echo -e "${GREEN}✓ $filename has push trigger${NC}"
        else
            echo -e "${YELLOW}⚠ $filename missing push trigger${NC}"
        fi
        
        # Check for pull_request trigger
        if grep -q "pull_request:" "$workflow"; then
            echo -e "${GREEN}✓ $filename has pull_request trigger${NC}"
        else
            echo -e "${YELLOW}⚠ $filename missing pull_request trigger${NC}"
        fi
    fi
done

echo ""

# Check for workflow_dispatch (manual trigger)
echo -e "${YELLOW}Checking for manual trigger support...${NC}"
for workflow in "${REQUIRED_WORKFLOWS[@]}"; do
    if [ -f "$workflow" ]; then
        filename=$(basename "$workflow")
        if grep -q "workflow_dispatch:" "$workflow"; then
            echo -e "${GREEN}✓ $filename supports manual trigger${NC}"
        else
            echo -e "${YELLOW}ℹ $filename does not support manual trigger${NC}"
        fi
    fi
done

echo ""

# Check for required jobs in CI workflow
if [ -f ".github/workflows/ci.yml" ]; then
    echo -e "${YELLOW}Checking CI workflow jobs...${NC}"
    
    REQUIRED_JOBS=("lint" "test" "build")
    for job in "${REQUIRED_JOBS[@]}"; do
        if grep -q "  $job:" ".github/workflows/ci.yml"; then
            echo -e "${GREEN}✓ CI workflow has '$job' job${NC}"
        else
            echo -e "${RED}✗ CI workflow missing '$job' job${NC}"
        fi
    done
    echo ""
fi

# Check for GitHub Actions directory structure
echo -e "${YELLOW}Checking GitHub Actions directory structure...${NC}"

if [ -d ".github" ]; then
    echo -e "${GREEN}✓ .github directory exists${NC}"
else
    echo -e "${RED}✗ .github directory missing${NC}"
fi

if [ -d ".github/workflows" ]; then
    echo -e "${GREEN}✓ .github/workflows directory exists${NC}"
else
    echo -e "${RED}✗ .github/workflows directory missing${NC}"
fi

if [ -d ".github/ISSUE_TEMPLATE" ]; then
    echo -e "${GREEN}✓ .github/ISSUE_TEMPLATE directory exists${NC}"
else
    echo -e "${YELLOW}⚠ .github/ISSUE_TEMPLATE directory missing${NC}"
fi

if [ -f ".github/pull_request_template.md" ]; then
    echo -e "${GREEN}✓ Pull request template exists${NC}"
else
    echo -e "${YELLOW}⚠ Pull request template missing${NC}"
fi

echo ""

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Verification Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

if [ $MISSING_REQUIRED -eq 0 ]; then
    echo -e "${GREEN}✓ All required workflow files are present${NC}"
else
    echo -e "${RED}✗ $MISSING_REQUIRED required workflow file(s) missing${NC}"
fi

if [ -n "$YAML_ERRORS" ] && [ $YAML_ERRORS -gt 0 ]; then
    echo -e "${RED}✗ $YAML_ERRORS workflow file(s) have YAML syntax errors${NC}"
fi

echo ""

if [ $MISSING_REQUIRED -eq 0 ] && ([ -z "$YAML_ERRORS" ] || [ $YAML_ERRORS -eq 0 ]); then
    echo -e "${GREEN}Workflow verification passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Push changes to trigger workflows"
    echo "2. Monitor workflow runs in GitHub Actions tab"
    echo "3. Add successful workflows as required status checks in branch protection"
    exit 0
else
    echo -e "${RED}Workflow verification failed!${NC}"
    echo ""
    echo "Please:"
    echo "1. Add missing workflow files"
    echo "2. Fix YAML syntax errors"
    echo "3. Re-run this script to verify"
    exit 1
fi
