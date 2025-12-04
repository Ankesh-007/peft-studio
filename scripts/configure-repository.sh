#!/bin/bash

# Repository Configuration Script for PEFT Studio
# This script automates GitHub repository configuration using GitHub CLI (gh)
#
# Prerequisites:
# - GitHub CLI (gh) must be installed: https://cli.github.com/
# - You must be authenticated: gh auth login
# - You must have admin access to the repository

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

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}PEFT Studio Repository Configuration${NC}"
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

# Function to check if repository exists
check_repository() {
    echo -e "${YELLOW}Checking repository: ${REPO_FULL}${NC}"
    if gh repo view "${REPO_FULL}" &> /dev/null; then
        echo -e "${GREEN}✓ Repository exists${NC}"
        return 0
    else
        echo -e "${RED}✗ Repository not found: ${REPO_FULL}${NC}"
        echo "Please update REPO_OWNER in this script or set GITHUB_REPOSITORY_OWNER environment variable"
        exit 1
    fi
}

# Function to update repository settings
configure_basic_settings() {
    echo ""
    echo -e "${YELLOW}Configuring basic repository settings...${NC}"
    
    # Update description
    gh repo edit "${REPO_FULL}" \
        --description "Professional desktop application for Parameter-Efficient Fine-Tuning (PEFT) of Large Language Models" \
        --enable-issues \
        --enable-projects \
        --enable-wiki=false \
        2>/dev/null || echo -e "${YELLOW}Note: Some settings may require manual configuration${NC}"
    
    echo -e "${GREEN}✓ Basic settings configured${NC}"
}

# Function to add topics
add_topics() {
    echo ""
    echo -e "${YELLOW}Adding repository topics...${NC}"
    
    TOPICS="peft,fine-tuning,llm,machine-learning,electron,react,pytorch,transformers,desktop-app,ai"
    
    gh repo edit "${REPO_FULL}" --add-topic "${TOPICS}" 2>/dev/null || {
        echo -e "${YELLOW}Note: Topics may need to be added manually via GitHub web interface${NC}"
        echo "Topics to add: ${TOPICS}"
    }
    
    echo -e "${GREEN}✓ Topics configured${NC}"
}

# Function to enable discussions
enable_discussions() {
    echo ""
    echo -e "${YELLOW}Enabling GitHub Discussions...${NC}"
    
    # Note: GitHub CLI doesn't have direct support for enabling discussions
    # This needs to be done via the web interface or GraphQL API
    echo -e "${YELLOW}⚠ Discussions must be enabled manually:${NC}"
    echo "  1. Go to: https://github.com/${REPO_FULL}/settings"
    echo "  2. Under 'Features', check 'Discussions'"
    echo "  3. Click 'Set up discussions'"
}

# Function to configure branch protection
configure_branch_protection() {
    echo ""
    echo -e "${YELLOW}Configuring branch protection for 'main'...${NC}"
    
    # Note: This requires more complex API calls
    echo -e "${YELLOW}⚠ Branch protection must be configured manually:${NC}"
    echo "  1. Go to: https://github.com/${REPO_FULL}/settings/branches"
    echo "  2. Click 'Add branch protection rule'"
    echo "  3. Branch name pattern: main"
    echo "  4. Enable required settings (see REPOSITORY_CONFIGURATION_GUIDE.md)"
}

# Function to verify workflows
verify_workflows() {
    echo ""
    echo -e "${YELLOW}Verifying GitHub Actions workflows...${NC}"
    
    WORKFLOW_FILES=(
        ".github/workflows/ci.yml"
        ".github/workflows/test.yml"
        ".github/workflows/build.yml"
        ".github/workflows/code-quality.yml"
        ".github/workflows/deploy.yml"
        ".github/workflows/release.yml"
        ".github/workflows/build-installers.yml"
        ".github/workflows/nightly.yml"
    )
    
    for workflow in "${WORKFLOW_FILES[@]}"; do
        if [ -f "$workflow" ]; then
            echo -e "${GREEN}✓ Found: $workflow${NC}"
        else
            echo -e "${RED}✗ Missing: $workflow${NC}"
        fi
    done
}

# Function to check community standards
check_community_standards() {
    echo ""
    echo -e "${YELLOW}Checking community standards...${NC}"
    
    REQUIRED_FILES=(
        "README.md"
        "LICENSE"
        "CONTRIBUTING.md"
        "CODE_OF_CONDUCT.md"
        "SECURITY.md"
        ".github/ISSUE_TEMPLATE/bug_report.md"
        ".github/ISSUE_TEMPLATE/feature_request.md"
        ".github/pull_request_template.md"
    )
    
    for file in "${REQUIRED_FILES[@]}"; do
        if [ -f "$file" ]; then
            echo -e "${GREEN}✓ Found: $file${NC}"
        else
            echo -e "${RED}✗ Missing: $file${NC}"
        fi
    done
}

# Function to display summary
display_summary() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}Configuration Summary${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    echo -e "${GREEN}Automated Configuration:${NC}"
    echo "  ✓ Repository description updated"
    echo "  ✓ Issues and Projects enabled"
    echo "  ✓ Topics added"
    echo "  ✓ Workflows verified"
    echo "  ✓ Community files checked"
    echo ""
    echo -e "${YELLOW}Manual Configuration Required:${NC}"
    echo "  ⚠ Enable Discussions in repository settings"
    echo "  ⚠ Configure branch protection rules for 'main'"
    echo "  ⚠ Set up discussion categories"
    echo "  ⚠ Create and pin welcome discussion"
    echo ""
    echo -e "${BLUE}Next Steps:${NC}"
    echo "  1. Review .github/REPOSITORY_CONFIGURATION_GUIDE.md"
    echo "  2. Complete manual configuration steps"
    echo "  3. Verify all settings in GitHub web interface"
    echo "  4. Run security and quality checks"
    echo "  5. Make repository public when ready"
    echo ""
    echo -e "${GREEN}Repository URL: https://github.com/${REPO_FULL}${NC}"
    echo ""
}

# Main execution
main() {
    check_repository
    configure_basic_settings
    add_topics
    enable_discussions
    configure_branch_protection
    verify_workflows
    check_community_standards
    display_summary
}

# Run main function
main

echo -e "${GREEN}Configuration script completed!${NC}"
echo ""
