#!/bin/bash

# Comprehensive Test, Build, and Deploy Script for PEFT Studio
# This script runs all tests, builds installers, and prepares for GitHub deployment

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Flags
SKIP_TESTS=false
SKIP_BUILD=false
PLATFORM="windows,linux"
PUSH_TO_GITHUB=false
COMMIT_MESSAGE="Build: Create installers for Windows and Linux"
TESTS_FAILED=false
BUILD_FAILED=false

# Functions
log() { echo -e "${GREEN}$1${NC}"; }
warn() { echo -e "${YELLOW}$1${NC}"; }
error() { echo -e "${RED}$1${NC}"; }
info() { echo -e "${CYAN}$1${NC}"; }
step() { echo -e "\n${MAGENTA}=== $1 ===${NC}"; }

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --platform)
            PLATFORM="$2"
            shift 2
            ;;
        --push)
            PUSH_TO_GITHUB=true
            shift
            ;;
        --message)
            COMMIT_MESSAGE="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--skip-tests] [--skip-build] [--platform windows,linux] [--push] [--message 'commit message']"
            exit 1
            ;;
    esac
done

check_prerequisites() {
    step "Checking Prerequisites"
    
    local missing=()
    
    command -v node &> /dev/null || missing+=("Node.js")
    command -v npm &> /dev/null || missing+=("npm")
    command -v python3 &> /dev/null || missing+=("Python")
    command -v git &> /dev/null || missing+=("Git")
    
    if [ ${#missing[@]} -gt 0 ]; then
        error "Missing prerequisites: ${missing[*]}"
        info "Please install the missing tools and try again"
        exit 1
    fi
    
    log "✓ All prerequisites found"
}

install_dependencies() {
    step "Installing Dependencies"
    
    info "Installing Node.js dependencies..."
    npm ci || { error "npm ci failed"; exit 1; }
    
    info "Installing Python dependencies..."
    cd backend
    python3 -m pip install --upgrade pip
    pip install -r requirements.txt
    pip install pytest pytest-asyncio pytest-cov hypothesis
    cd ..
    
    log "✓ Dependencies installed"
}

run_frontend_tests() {
    step "Running Frontend Tests"
    
    info "Running unit tests..."
    if npm run test:run; then
        log "✓ Frontend tests passed"
        return 0
    else
        warn "⚠ Some frontend tests failed"
        TESTS_FAILED=true
        return 1
    fi
}

run_backend_tests() {
    step "Running Backend Tests"
    
    cd backend
    info "Running Python tests..."
    
    if python3 -m pytest tests/ -v --tb=short --maxfail=5; then
        cd ..
        log "✓ Backend tests passed"
        return 0
    else
        cd ..
        warn "⚠ Some backend tests failed"
        TESTS_FAILED=true
        return 1
    fi
}

run_linting() {
    step "Running Code Quality Checks"
    
    info "Running ESLint..."
    if npm run lint; then
        log "✓ Linting passed"
    else
        warn "⚠ Linting issues found (continuing anyway)"
    fi
    
    info "Running TypeScript type check..."
    if npm run type-check; then
        log "✓ Type check passed"
    else
        warn "⚠ Type check issues found (continuing anyway)"
    fi
}

build_frontend() {
    step "Building Frontend"
    
    if npm run build; then
        if [ ! -d "dist" ]; then
            error "Build output directory 'dist' not found"
            BUILD_FAILED=true
            return 1
        fi
        log "✓ Frontend built successfully"
        return 0
    else
        error "Frontend build failed"
        BUILD_FAILED=true
        return 1
    fi
}

build_installers() {
    local platforms=$1
    step "Building Installers"
    
    IFS=',' read -ra PLATFORM_LIST <<< "$platforms"
    local success=true
    
    for platform in "${PLATFORM_LIST[@]}"; do
        platform=$(echo "$platform" | xargs) # trim whitespace
        
        info "Building $platform installer..."
        
        case "${platform,,}" in
            windows)
                if npx electron-builder --win --config; then
                    log "✓ $platform installer built"
                else
                    error "$platform installer build failed"
                    success=false
                    BUILD_FAILED=true
                fi
                ;;
            linux)
                if npx electron-builder --linux --config; then
                    log "✓ $platform installer built"
                else
                    error "$platform installer build failed"
                    success=false
                    BUILD_FAILED=true
                fi
                ;;
            mac)
                if npx electron-builder --mac --config; then
                    log "✓ $platform installer built"
                else
                    error "$platform installer build failed"
                    success=false
                    BUILD_FAILED=true
                fi
                ;;
            *)
                warn "Unknown platform: $platform (skipping)"
                ;;
        esac
    done
    
    [ "$success" = true ] && return 0 || return 1
}

show_build_artifacts() {
    step "Build Artifacts"
    
    if [ -d "release" ]; then
        local files=(release/*)
        
        if [ ${#files[@]} -eq 0 ] || [ ! -e "${files[0]}" ]; then
            warn "No build artifacts found in release directory"
            return
        fi
        
        info "\nGenerated installers:"
        local total_size=0
        for file in "${files[@]}"; do
            if [ -f "$file" ]; then
                local size=$(du -h "$file" | cut -f1)
                local size_bytes=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null)
                total_size=$((total_size + size_bytes))
                log "  ✓ $(basename "$file") ($size)"
            fi
        done
        
        local total_mb=$((total_size / 1024 / 1024))
        info "\nTotal size: ${total_mb} MB"
    else
        warn "Release directory not found"
    fi
}

push_to_github() {
    step "Pushing to GitHub"
    
    local status=$(git status --porcelain)
    
    if [ -z "$status" ]; then
        info "No changes to commit"
    else
        info "Staging changes..."
        git add .
        
        info "Committing changes..."
        git commit -m "$COMMIT_MESSAGE"
        
        info "Pushing to GitHub..."
        if git push; then
            log "✓ Changes pushed to GitHub"
        else
            error "Git push failed"
            exit 1
        fi
    fi
    
    local current_branch=$(git rev-parse --abbrev-ref HEAD)
    info "\nCurrent branch: $current_branch"
    info "To create a release, push a tag:"
    info "  git tag v1.0.0"
    info "  git push origin v1.0.0"
    info "\nThis will trigger the GitHub Actions workflow to build and publish installers"
}

show_summary() {
    step "Summary"
    
    if [ "$TESTS_FAILED" = false ] && [ "$BUILD_FAILED" = false ]; then
        log "\n✓ All operations completed successfully!"
    else
        warn "\n⚠ Some operations had issues:"
        [ "$TESTS_FAILED" = true ] && warn "  - Tests failed or had warnings"
        [ "$BUILD_FAILED" = true ] && warn "  - Build failed or had errors"
    fi
    
    info "\nNext steps:"
    if [ -d "release" ]; then
        info "  1. Test the installers in the 'release' directory"
        info "  2. Review the build artifacts"
    fi
    if [ "$PUSH_TO_GITHUB" = true ]; then
        info "  3. Create a release tag to trigger automated builds"
        info "     git tag v1.0.0 && git push origin v1.0.0"
    else
        info "  3. Run with --push to push changes"
    fi
}

# Main execution
log "======================================================================"
log "PEFT Studio - Test, Build, and Deploy"
log "======================================================================"

check_prerequisites
install_dependencies

# Run tests
if [ "$SKIP_TESTS" = false ]; then
    run_linting
    run_frontend_tests
    frontend_result=$?
    run_backend_tests
    backend_result=$?
    
    if [ $frontend_result -ne 0 ] || [ $backend_result -ne 0 ]; then
        warn "\n⚠ Tests failed. Continue with build? (y/N)"
        read -r response
        if [ "$response" != "y" ] && [ "$response" != "Y" ]; then
            info "Build cancelled by user"
            exit 1
        fi
    fi
else
    warn "Skipping tests (as requested)"
fi

# Build
if [ "$SKIP_BUILD" = false ]; then
    if build_frontend; then
        build_installers "$PLATFORM"
        show_build_artifacts
    else
        error "Cannot build installers - frontend build failed"
        exit 1
    fi
else
    warn "Skipping build (as requested)"
fi

# Push to GitHub
if [ "$PUSH_TO_GITHUB" = true ]; then
    push_to_github
fi

show_summary

log "\n======================================================================"
log "Process Complete"
log "======================================================================"
