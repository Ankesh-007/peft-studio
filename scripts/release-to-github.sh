#!/bin/bash
# PEFT Studio - Complete Release to GitHub Script
# This script handles the entire release process

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

VERSION="1.0.1"
SKIP_BUILD=false
SKIP_TESTS=false
DRY_RUN=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --version)
            VERSION="$2"
            shift 2
            ;;
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo -e "${CYAN}=== PEFT Studio Release to GitHub ===${NC}"
echo -e "${YELLOW}Version: $VERSION${NC}"
echo ""

# Step 1: Clean up unnecessary files
echo -e "${CYAN}[1/8] Cleaning up unnecessary files...${NC}"
if [ "$DRY_RUN" = true ]; then
    bash "$(dirname "$0")/prepare-release.sh" --dry-run
else
    bash "$(dirname "$0")/prepare-release.sh"
fi

# Step 2: Run tests (unless skipped)
if [ "$SKIP_TESTS" = false ]; then
    echo ""
    echo -e "${CYAN}[2/8] Running tests...${NC}"
    npm run test:run
else
    echo ""
    echo -e "${YELLOW}[2/8] Skipping tests...${NC}"
fi

# Step 3: Build the application (unless skipped)
if [ "$SKIP_BUILD" = false ]; then
    echo ""
    echo -e "${CYAN}[3/8] Building application...${NC}"
    npm run build
else
    echo ""
    echo -e "${YELLOW}[3/8] Skipping build...${NC}"
fi

# Step 4: Package installers
echo ""
echo -e "${CYAN}[4/8] Packaging installers...${NC}"
if [ "$DRY_RUN" = false ]; then
    npm run package:all
else
    echo -e "  ${YELLOW}[DRY RUN] Would run: npm run package:all${NC}"
fi

# Step 5: Generate checksums
echo ""
echo -e "${CYAN}[5/8] Generating checksums...${NC}"
if [ "$DRY_RUN" = false ]; then
    npm run generate:checksums
else
    echo -e "  ${YELLOW}[DRY RUN] Would run: npm run generate:checksums${NC}"
fi

# Step 6: Commit changes
echo ""
echo -e "${CYAN}[6/8] Committing changes...${NC}"
if [ "$DRY_RUN" = false ]; then
    git add .
    git commit -m "chore: prepare v$VERSION release" || echo -e "${YELLOW}WARNING: Commit failed (maybe no changes?)${NC}"
else
    echo -e "  ${YELLOW}[DRY RUN] Would run: git add . && git commit -m 'chore: prepare v$VERSION release'${NC}"
fi

# Step 7: Create and push tag
echo ""
echo -e "${CYAN}[7/8] Creating and pushing tag...${NC}"
if [ "$DRY_RUN" = false ]; then
    git tag -a "v$VERSION" -m "Release v$VERSION"
    
    echo -e "  ${CYAN}Pushing to origin...${NC}"
    git push origin main --tags
else
    echo -e "  ${YELLOW}[DRY RUN] Would run: git tag -a v$VERSION -m 'Release v$VERSION'${NC}"
    echo -e "  ${YELLOW}[DRY RUN] Would run: git push origin main --tags${NC}"
fi

# Step 8: Summary
echo ""
echo -e "${CYAN}[8/8] Release Summary${NC}"
echo -e "  ${GREEN}Version: v$VERSION${NC}"
echo -n "  Status: "
if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}DRY RUN COMPLETE${NC}"
else
    echo -e "${GREEN}RELEASED${NC}"
fi
echo ""

if [ "$DRY_RUN" = false ]; then
    echo -e "${CYAN}Next steps:${NC}"
    echo -e "  ${NC}1. Go to: https://github.com/Ankesh-007/peft-studio/releases${NC}"
    echo -e "  ${NC}2. Find the v$VERSION tag${NC}"
    echo -e "  ${NC}3. Click 'Create release from tag'${NC}"
    echo -e "  ${NC}4. Upload installers from the 'release/' directory${NC}"
    echo -e "  ${NC}5. Upload checksums file${NC}"
    echo -e "  ${NC}6. Publish the release${NC}"
else
    echo -e "${YELLOW}Run without --dry-run to actually perform the release.${NC}"
fi

echo ""
echo -e "${GREEN}Release process complete!${NC}"
