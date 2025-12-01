#!/bin/bash

# Build script for PEFT Studio (Unix/Linux/macOS)
# Usage: ./scripts/build.sh [windows|mac|linux|all]

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}$1${NC}"
}

warn() {
    echo -e "${YELLOW}$1${NC}"
}

error() {
    echo -e "${RED}$1${NC}"
}

info() {
    echo -e "${CYAN}$1${NC}"
}

# Check prerequisites
check_prerequisites() {
    log "\n=== Checking Prerequisites ==="
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        error "Node.js is not installed"
        exit 1
    fi
    
    # Check npm
    if ! command -v npm &> /dev/null; then
        error "npm is not installed"
        exit 1
    fi
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        warn "node_modules not found. Running npm install..."
        npm install
    fi
    
    log "Prerequisites check complete"
}

# Build frontend
build_frontend() {
    log "\n=== Building Frontend ==="
    npm run build
    log "Frontend build complete"
}

# Build installer
build_installer() {
    local platform=$1
    log "\n=== Building $platform Installer ==="
    
    case $platform in
        windows)
            npx electron-builder --win
            ;;
        mac)
            npx electron-builder --mac
            ;;
        linux)
            npx electron-builder --linux
            ;;
        all)
            npx electron-builder --win --mac --linux
            ;;
        *)
            error "Unknown platform: $platform"
            error "Valid platforms: windows, mac, linux, all"
            exit 1
            ;;
    esac
    
    log "$platform installer build complete"
}

# Show outputs
show_outputs() {
    log "\n=== Build Outputs ==="
    
    if [ -d "release" ]; then
        info "\nGenerated installers:"
        ls -lh release/ | grep -v "^d" | awk '{print "  - " $9 " (" $5 ")"}'
    else
        warn "No release directory found"
    fi
}

# Main
main() {
    local platform=${1:-all}
    
    log "======================================================================"
    log "PEFT Studio Build Script"
    log "======================================================================"
    
    check_prerequisites
    build_frontend
    build_installer "$platform"
    show_outputs
    
    log "\n=== Build Complete ==="
    log "Installers are in the release/ directory"
}

main "$@"
