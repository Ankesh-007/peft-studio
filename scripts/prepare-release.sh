#!/bin/bash
# PEFT Studio - Prepare Release Script
# This script cleans up unnecessary files and prepares for release

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
GRAY='\033[0;90m'
NC='\033[0m' # No Color

DRY_RUN=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
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

echo -e "${CYAN}=== PEFT Studio Release Preparation ===${NC}"
echo ""

# Files and directories to remove
items_to_remove=(
    # Build artifacts
    "release/win-unpacked"
    "release/builder-debug.yml"
    "release/builder-effective-config.yaml"
    "dist/assets"
    "dist/samples"
    "dist/index.html"
    "dist/stats.html"
    "build/signing-status-macos.txt"
    "build/signing-status.txt"
    
    # Backend cache and temporary files
    "backend/.hypothesis"
    "backend/.pytest_cache"
    "backend/__pycache__"
    "backend/data/cache"
    "backend/data/peft_studio.db"
    "backend/data/security_audit.log"
    "backend/artifacts"
    "backend/checkpoints"
    
    # Node modules cache
    ".vite"
    
    # Spec documentation (keep only essential)
    ".kiro/specs/peft-application-fix/RELEASE_PUBLICATION_GUIDE.md"
    ".kiro/specs/peft-application-fix/RELEASE_NOTES_v1.0.1.md"
    ".kiro/specs/peft-application-fix/FINAL_CHECKPOINT_VERIFICATION.md"
    ".kiro/specs/peft-application-fix/RELEASE_1.0.1_SUMMARY.md"
    ".kiro/specs/peft-application-fix/GITHUB_RELEASE_GUIDE.md"
    ".kiro/specs/peft-application-fix/INSTALLER_TESTING_GUIDE.md"
)

total_items=${#items_to_remove[@]}
removed_count=0
skipped_count=0

echo -e "${YELLOW}Found $total_items items to clean up${NC}"
echo ""

if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}DRY RUN MODE - No files will be deleted${NC}"
    echo ""
fi

for item in "${items_to_remove[@]}"; do
    if [ -e "$item" ]; then
        if [ -d "$item" ]; then
            size=$(du -sh "$item" 2>/dev/null | cut -f1 || echo "unknown")
        else
            size=$(du -h "$item" 2>/dev/null | cut -f1 || echo "unknown")
        fi
        
        echo -e "  ${RED}[REMOVE]${NC} $item ($size)"
        
        if [ "$DRY_RUN" = false ]; then
            rm -rf "$item" && ((removed_count++)) || ((skipped_count++))
        fi
    else
        echo -e "  ${GRAY}[SKIP]${NC} $item (not found)"
        ((skipped_count++))
    fi
done

echo ""
echo -e "${CYAN}=== Cleanup Summary ===${NC}"
if [ "$DRY_RUN" = true ]; then
    echo -e "  ${YELLOW}Would remove: $removed_count items${NC}"
else
    echo -e "  ${GREEN}Removed: $removed_count items${NC}"
fi
echo -e "  ${GRAY}Skipped: $skipped_count items${NC}"
echo ""

# Verify critical files still exist
echo -e "${CYAN}=== Verifying Critical Files ===${NC}"
critical_files=(
    "package.json"
    "README.md"
    "LICENSE"
    "CHANGELOG.md"
    "electron/main.js"
    "backend/main.py"
    "backend/requirements.txt"
    "build/.gitkeep"
    "build/README.md"
)

all_critical_exist=true
for file in "${critical_files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "  ${GREEN}[OK]${NC} $file"
    else
        echo -e "  ${RED}[MISSING]${NC} $file"
        all_critical_exist=false
    fi
done

echo ""

if [ "$all_critical_exist" = false ]; then
    echo -e "${RED}ERROR: Some critical files are missing!${NC}"
    exit 1
fi

if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}Dry run complete. Run without --dry-run to actually remove files.${NC}"
else
    echo -e "${GREEN}Cleanup complete! Ready for release.${NC}"
fi

echo ""
echo -e "${CYAN}Next steps:${NC}"
echo -e "  ${NC}1. Run: npm run build${NC}"
echo -e "  ${NC}2. Run: npm run package:all${NC}"
echo -e "  ${NC}3. Run: npm run generate:checksums${NC}"
echo -e "  ${NC}4. Commit changes: git add . && git commit -m 'chore: prepare v1.0.1 release'${NC}"
echo -e "  ${NC}5. Create tag: git tag -a v1.0.1 -m 'Release v1.0.1'${NC}"
echo -e "  ${NC}6. Push: git push origin main --tags${NC}"
echo ""
