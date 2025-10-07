#!/bin/bash
# CodeCritique - Comprehensive Build Script (Bash)
# Builds both portable executable and desktop app distributions

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Functions for colored output
success() {
    echo -e "${GREEN}✅ $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Parse command line arguments
PORTABLE_ONLY=false
DESKTOP_ONLY=false
CLEAN=false
HELP=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --portable-only)
            PORTABLE_ONLY=true
            shift
            ;;
        --desktop-only)
            DESKTOP_ONLY=true
            shift
            ;;
        --clean)
            CLEAN=true
            shift
            ;;
        --help|-h)
            HELP=true
            shift
            ;;
        *)
            error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Show help
if [ "$HELP" = true ]; then
    echo -e "${GREEN}CodeCritique Build Script${NC}"
    echo ""
    echo -e "${YELLOW}Usage: ./build_all.sh [options]${NC}"
    echo ""
    echo -e "${CYAN}Options:${NC}"
    echo "  --portable-only    Build only portable version"
    echo "  --desktop-only     Build only desktop version"
    echo "  --clean           Clean build directories only"
    echo "  --help, -h         Show this help message"
    echo ""
    echo -e "${YELLOW}Examples:${NC}"
    echo "  ./build_all.sh                    # Build both versions"
    echo "  ./build_all.sh --portable-only    # Build only portable"
    echo "  ./build_all.sh --desktop-only     # Build only desktop"
    echo "  ./build_all.sh --clean           # Clean directories"
    exit 0
fi

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${GREEN}🚀 CodeCritique Build Script${NC}"
echo -e "${BLUE}Project Root: $PROJECT_ROOT${NC}"

# Change to project root
cd "$PROJECT_ROOT"

# Check for conflicting options
if [ "$PORTABLE_ONLY" = true ] && [ "$DESKTOP_ONLY" = true ]; then
    error "Cannot specify both --portable-only and --desktop-only"
    exit 1
fi

# Clean directories if requested
if [ "$CLEAN" = true ]; then
    info "Cleaning build directories..."
    
    DIRS_TO_CLEAN=("build" "dist" "portable" "releases")
    for dir in "${DIRS_TO_CLEAN[@]}"; do
        if [ -d "$dir" ]; then
            rm -rf "$dir"
            success "Cleaned $dir"
        fi
    done
    
    success "Build directories cleaned!"
    exit 0
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        error "Python is not installed or not in PATH"
        info "Please install Python from https://python.org"
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

# Check Python version
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1)
info "Using Python: $PYTHON_VERSION"

# Build process
BUILD_ARGS=()
if [ "$PORTABLE_ONLY" = true ]; then
    BUILD_ARGS+=("--portable-only")
fi
if [ "$DESKTOP_ONLY" = true ]; then
    BUILD_ARGS+=("--desktop-only")
fi

info "Starting build process..."
info "Arguments: ${BUILD_ARGS[*]}"

# Run the Python build script
PYTHON_SCRIPT="$PROJECT_ROOT/scripts/py/build_all.py"

if [ ! -f "$PYTHON_SCRIPT" ]; then
    error "Build script not found: $PYTHON_SCRIPT"
    exit 1
fi

# Run the build
BUILD_COMMAND="$PYTHON_CMD \"$PYTHON_SCRIPT\" ${BUILD_ARGS[*]}"
info "Running: $BUILD_COMMAND"

if eval "$BUILD_COMMAND"; then
    success "Build completed successfully!"
    
    # Show release packages
    RELEASES_DIR="$PROJECT_ROOT/releases"
    if [ -d "$RELEASES_DIR" ]; then
        info "Release packages created:"
        for file in "$RELEASES_DIR"/*; do
            if [ -f "$file" ]; then
                echo -e "  ${BLUE}📦 $(basename "$file")${NC}"
            fi
        done
    fi
    
    echo ""
    success "All builds completed successfully!"
    echo -e "${CYAN}📦 Release packages: $RELEASES_DIR${NC}"
    echo -e "${YELLOW}🚀 You can now distribute the release packages!${NC}"
    
else
    error "Build failed with exit code: $?"
    exit 1
fi

