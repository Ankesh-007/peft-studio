#!/bin/bash
# Test Release Script
# This script helps automate parts of the release testing process

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
GRAY='\033[0;90m'
NC='\033[0m' # No Color

function write_success() { echo -e "${GREEN}✅ $1${NC}"; }
function write_error() { echo -e "${RED}❌ $1${NC}"; }
function write_info() { echo -e "${CYAN}ℹ️  $1${NC}"; }
function write_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }

# Configuration
REPO_OWNER="Ankesh-007"
REPO_NAME="peft-studio"
GITHUB_API="https://api.github.com"

# Parse arguments
VERSION=""
CHECK_WORKFLOW=false
VERIFY_ASSETS=false
VERIFY_CHECKSUMS=false
ALL=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --version)
            VERSION="$2"
            shift 2
            ;;
        --check-workflow)
            CHECK_WORKFLOW=true
            shift
            ;;
        --verify-assets)
            VERIFY_ASSETS=true
            shift
            ;;
        --verify-checksums)
            VERIFY_CHECKSUMS=true
            shift
            ;;
        --all)
            ALL=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--version VERSION] [--check-workflow] [--verify-assets] [--verify-checksums] [--all]"
            exit 1
            ;;
    esac
done

function get_latest_test_release() {
    write_info "Fetching latest test release..."
    
    local releases=$(curl -s "$GITHUB_API/repos/$REPO_OWNER/$REPO_NAME/releases")
    local test_release=$(echo "$releases" | jq -r '[.[] | select(.tag_name | contains("-test"))] | .[0]')
    
    if [ "$test_release" == "null" ] || [ -z "$test_release" ]; then
        write_warning "No test releases found"
        return 1
    fi
    
    local tag_name=$(echo "$test_release" | jq -r '.tag_name')
    write_success "Found test release: $tag_name"
    echo "$test_release"
}

function test_workflow_status() {
    local tag_name=$1
    write_info "Checking workflow status for $tag_name..."
    
    local workflows=$(curl -s "$GITHUB_API/repos/$REPO_OWNER/$REPO_NAME/actions/runs?event=push")
    local release_workflow=$(echo "$workflows" | jq -r "[.workflow_runs[] | select(.name == \"Release\" and .head_branch == \"$tag_name\")] | .[0]")
    
    if [ "$release_workflow" == "null" ] || [ -z "$release_workflow" ]; then
        write_warning "No workflow runs found for $tag_name"
        return 1
    fi
    
    local status=$(echo "$release_workflow" | jq -r '.status')
    local conclusion=$(echo "$release_workflow" | jq -r '.conclusion')
    local url=$(echo "$release_workflow" | jq -r '.html_url')
    
    write_info "Workflow Status: $status"
    write_info "Conclusion: $conclusion"
    write_info "URL: $url"
    
    if [ "$status" == "completed" ] && [ "$conclusion" == "success" ]; then
        write_success "Workflow completed successfully"
        return 0
    elif [ "$status" == "in_progress" ]; then
        write_warning "Workflow is still in progress"
        return 1
    else
        write_error "Workflow failed or was cancelled"
        return 1
    fi
}

function test_release_assets() {
    local release=$1
    write_info "Verifying release assets..."
    
    local expected_patterns=(
        "PEFT-Studio-Setup-.*\.exe"
        "PEFT-Studio-.*-portable\.exe"
        "PEFT-Studio-.*\.dmg"
        "PEFT-Studio-.*-mac\.zip"
        "PEFT-Studio-.*\.AppImage"
        "peft-studio_.*_amd64\.deb"
        "SHA256SUMS\.txt"
    )
    
    local assets=$(echo "$release" | jq -r '.assets')
    local all_found=true
    
    for pattern in "${expected_patterns[@]}"; do
        local found=$(echo "$assets" | jq -r ".[] | select(.name | test(\"$pattern\")) | .name" | head -n 1)
        
        if [ -n "$found" ]; then
            local size=$(echo "$assets" | jq -r ".[] | select(.name == \"$found\") | .size")
            local size_mb=$(echo "scale=2; $size / 1048576" | bc)
            write_success "Found: $found (${size_mb} MB)"
        else
            write_error "Missing: $pattern"
            all_found=false
        fi
    done
    
    if [ "$all_found" == true ]; then
        write_success "All expected assets are present"
        return 0
    else
        write_error "Some assets are missing"
        return 1
    fi
}

function test_checksums() {
    local release=$1
    write_info "Verifying checksums..."
    
    # Find SHA256SUMS.txt asset
    local checksums_asset=$(echo "$release" | jq -r '.assets[] | select(.name == "SHA256SUMS.txt")')
    
    if [ -z "$checksums_asset" ] || [ "$checksums_asset" == "null" ]; then
        write_error "SHA256SUMS.txt not found in release assets"
        return 1
    fi
    
    write_success "Found SHA256SUMS.txt"
    
    # Download checksums file
    local temp_dir=$(mktemp -d)
    local checksums_url=$(echo "$checksums_asset" | jq -r '.browser_download_url')
    local checksums_path="$temp_dir/SHA256SUMS.txt"
    
    write_info "Downloading SHA256SUMS.txt..."
    if curl -sL "$checksums_url" -o "$checksums_path"; then
        # Read and display checksums
        local line_count=$(wc -l < "$checksums_path")
        write_info "Checksums file contains $line_count entries:"
        
        while IFS= read -r line; do
            if [ -n "$line" ]; then
                local hash=$(echo "$line" | awk '{print $1}')
                local file=$(echo "$line" | awk '{print $2}')
                echo -e "${GRAY}  $file: ${hash:0:16}...${NC}"
            fi
        done < "$checksums_path"
        
        write_success "Checksums file is valid"
        rm -rf "$temp_dir"
        return 0
    else
        write_error "Failed to download checksums"
        rm -rf "$temp_dir"
        return 1
    fi
}

function test_release_notes() {
    local release=$1
    write_info "Verifying release notes..."
    
    local body=$(echo "$release" | jq -r '.body')
    
    local required_sections=(
        "Downloads"
        "Installation"
        "Windows"
        "macOS"
        "Linux"
        "Checksums"
        "System Requirements"
    )
    
    local all_found=true
    
    for section in "${required_sections[@]}"; do
        if echo "$body" | grep -q "$section"; then
            write_success "Found section: $section"
        else
            write_warning "Missing section: $section"
            all_found=false
        fi
    done
    
    if [ "$all_found" == true ]; then
        write_success "All required sections are present in release notes"
        return 0
    else
        write_warning "Some sections are missing from release notes"
        return 1
    fi
}

function show_test_checklist() {
    local release=$1
    local tag_name=$(echo "$release" | jq -r '.tag_name')
    local html_url=$(echo "$release" | jq -r '.html_url')
    
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  Release Testing Checklist${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${YELLOW}Release: $tag_name${NC}"
    echo -e "${YELLOW}URL: $html_url${NC}"
    echo ""
    echo -e "${CYAN}Manual Testing Required:${NC}"
    echo ""
    echo "  [ ] Download Windows installer"
    echo "  [ ] Verify Windows installer checksum"
    echo "  [ ] Test Windows installation wizard"
    echo "  [ ] Verify Windows shortcuts created"
    echo "  [ ] Test Windows portable version"
    echo ""
    echo "  [ ] Download macOS DMG"
    echo "  [ ] Verify macOS DMG checksum"
    echo "  [ ] Test macOS drag-and-drop installation"
    echo "  [ ] Verify macOS application signature (if signed)"
    echo "  [ ] Test macOS ZIP archive"
    echo ""
    echo "  [ ] Download Linux AppImage"
    echo "  [ ] Verify Linux AppImage checksum"
    echo "  [ ] Test Linux AppImage execution"
    echo "  [ ] Verify Linux desktop integration"
    echo "  [ ] Test Linux DEB package installation"
    echo ""
    echo "  [ ] Test auto-update mechanism"
    echo "  [ ] Verify update notification appears"
    echo "  [ ] Test update download and installation"
    echo "  [ ] Verify application restarts with new version"
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${CYAN}Documentation:${NC}"
    echo -e "${GRAY}  - Test Release Process: docs/developer-guide/test-release-process.md${NC}"
    echo -e "${GRAY}  - Windows Testing: docs/developer-guide/test-windows-installer.md${NC}"
    echo -e "${GRAY}  - macOS Testing: docs/developer-guide/test-macos-installer.md${NC}"
    echo -e "${GRAY}  - Linux Testing: docs/developer-guide/test-linux-installer.md${NC}"
    echo -e "${GRAY}  - Auto-Update Testing: docs/developer-guide/test-auto-update.md${NC}"
    echo ""
}

# Check for required tools
if ! command -v jq &> /dev/null; then
    write_error "jq is required but not installed. Please install it first."
    echo "  Ubuntu/Debian: sudo apt-get install jq"
    echo "  macOS: brew install jq"
    echo "  Fedora: sudo dnf install jq"
    exit 1
fi

if ! command -v curl &> /dev/null; then
    write_error "curl is required but not installed. Please install it first."
    exit 1
fi

# Main execution
echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  PEFT Studio Release Testing Script${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Get release to test
release=""

if [ -n "$VERSION" ]; then
    write_info "Fetching release for version $VERSION..."
    release=$(curl -s "$GITHUB_API/repos/$REPO_OWNER/$REPO_NAME/releases/tags/$VERSION")
    
    if [ -z "$release" ] || [ "$release" == "null" ]; then
        write_error "Failed to fetch release $VERSION"
        exit 1
    fi
    
    write_success "Found release: $VERSION"
else
    release=$(get_latest_test_release)
    if [ $? -ne 0 ]; then
        write_error "No test release found. Please create a test release first."
        exit 1
    fi
fi

# Run tests based on parameters
all_passed=true

if [ "$ALL" == true ] || [ "$CHECK_WORKFLOW" == true ]; then
    echo ""
    tag_name=$(echo "$release" | jq -r '.tag_name')
    if ! test_workflow_status "$tag_name"; then
        all_passed=false
    fi
fi

if [ "$ALL" == true ] || [ "$VERIFY_ASSETS" == true ]; then
    echo ""
    if ! test_release_assets "$release"; then
        all_passed=false
    fi
fi

if [ "$ALL" == true ] || [ "$VERIFY_CHECKSUMS" == true ]; then
    echo ""
    if ! test_checksums "$release"; then
        all_passed=false
    fi
fi

if [ "$ALL" == true ]; then
    echo ""
    test_release_notes "$release" || true
fi

# Show checklist
echo ""
show_test_checklist "$release"

# Summary
echo ""
if [ "$all_passed" == true ]; then
    write_success "Automated tests passed! Proceed with manual testing."
else
    write_error "Some automated tests failed. Review the output above."
    exit 1
fi

echo ""
