#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting multi-distribution packaging process...${NC}"

# Check if rye is installed
if ! command -v rye &> /dev/null; then
    echo -e "${RED}Error: rye is not installed.${NC}"
    exit 1
fi

# Build the artifacts using rye
echo -e "${GREEN}Building sdist and wheel with rye...${NC}"
rye build --clean

# Extract version from pyproject.toml
VERSION=$(grep -m 1 'version =' pyproject.toml | cut -d '"' -f 2)
PKGNAME="ds4to360xboxdrv"

# Create output directory
OUTPUT_DIR="dist/packages"
mkdir -p "$OUTPUT_DIR"

# Function to build for Arch Linux
build_arch() {
    echo -e "${GREEN}Building Arch Linux package (pkg.tar.zst)...${NC}"
    if [ "$USE_DOCKER" = true ]; then
        docker run --rm -v "$(pwd):/app" -w /app archlinux:latest bash -c "
            pacman -Syu --noconfirm base-devel python-installer curl
            # Install rye manually since it is in AUR
            curl -sSf https://rye.astral.sh/get | RYE_INSTALL_OPTION=\"--yes\" bash
            source \$HOME/.rye/env
            cp dist/${PKGNAME}-${VERSION}.tar.gz .
            # makepkg cannot be run as root
            useradd -m builduser
            chown -R builduser:builduser .
            sudo -u builduser bash -c 'source \$HOME/.rye/env && makepkg -f'
            mv *.pkg.tar.zst dist/packages/
        "
    elif command -v makepkg &> /dev/null; then
        cp "dist/${PKGNAME}-${VERSION}.tar.gz" .
        makepkg -f
        mv *.pkg.tar.zst "$OUTPUT_DIR/"
        rm "${PKGNAME}-${VERSION}.tar.gz"
    else
        echo -e "${RED}Skipping Arch build: makepkg not found and --docker not used.${NC}"
    fi
}

# Function to build for Debian/Ubuntu
build_deb() {
    echo -e "${GREEN}Building Debian/Ubuntu package (.deb)...${NC}"
    if [ "$USE_DOCKER" = true ]; then
        docker run --rm -v "$(pwd):/app" -w /app ubuntu:22.04 bash -c "
            apt-get update
            apt-get install -y debhelper python3-all python3-installer curl
            curl -sSf https://rye.astral.sh/get | RYE_INSTALL_OPTION=\"--yes\" bash
            source \$HOME/.rye/env
            dpkg-buildpackage -us -uc -b
            mv ../${PKGNAME}_${VERSION}-1_*.deb dist/packages/
        "
    elif command -v dpkg-buildpackage &> /dev/null; then
        dpkg-buildpackage -us -uc -b
        mv ../${PKGNAME}_${VERSION}-1_*.deb "$OUTPUT_DIR/"
    else
        echo -e "${RED}Skipping Debian build: dpkg-buildpackage not found and --docker not used.${NC}"
    fi
}

# Function to build for Fedora/RPM
build_rpm() {
    echo -e "${GREEN}Building RPM package (.rpm)...${NC}"
    if [ "$USE_DOCKER" = true ]; then
        docker run --rm -v "$(pwd):/app" -w /app fedora:latest bash -c "
            dnf install -y rpm-build python3-devel python3-installer curl
            curl -sSf https://rye.astral.sh/get | RYE_INSTALL_OPTION=\"--yes\" bash
            source \$HOME/.rye/env
            mkdir -p ~/rpmbuild/{SOURCES,SPECS,RPMS,SRPMS,BUILD}
            cp dist/${PKGNAME}-${VERSION}.tar.gz ~/rpmbuild/SOURCES/
            cp ${PKGNAME}.spec ~/rpmbuild/SPECS/
            rpmbuild -ba ~/rpmbuild/SPECS/${PKGNAME}.spec
            mv ~/rpmbuild/RPMS/*/${PKGNAME}-*.rpm dist/packages/
        "
    elif command -v rpmbuild &> /dev/null; then
        mkdir -p ~/rpmbuild/{SOURCES,SPECS,RPMS,SRPMS,BUILD}
        cp "dist/${PKGNAME}-${VERSION}.tar.gz" ~/rpmbuild/SOURCES/
        cp "${PKGNAME}.spec" ~/rpmbuild/SPECS/
        rpmbuild -ba ~/rpmbuild/SPECS/${PKGNAME}.spec
        mv ~/rpmbuild/RPMS/*/${PKGNAME}-*.rpm "$OUTPUT_DIR/"
    else
        echo -e "${RED}Skipping RPM build: rpmbuild not found and --docker not used.${NC}"
    fi
}

# Parse arguments
BUILD_ALL=true
USE_DOCKER=false
TARGETS=()

for arg in "$@"; do
    case $arg in
        --arch)   TARGETS+=("arch"); BUILD_ALL=false ;;
        --deb)    TARGETS+=("deb"); BUILD_ALL=false ;;
        --rpm)    TARGETS+=("rpm"); BUILD_ALL=false ;;
        --docker) USE_DOCKER=true ;;
        --all)    BUILD_ALL=true ;;
        *)        echo "Unknown argument: $arg" ;;
    esac
done

if [ "$BUILD_ALL" = true ]; then
    build_arch
    build_deb
    build_rpm
else
    for t in "${TARGETS[@]}"; do
        case $t in
            arch) build_arch ;;
            deb)  build_deb ;;
            rpm)  build_rpm ;;
        esac
    done
fi

echo -e "${BLUE}Packaging process complete. Packages are in $OUTPUT_DIR/${NC}"
