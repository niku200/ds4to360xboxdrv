#!/bin/bash

# PNP Package Builder Script
# Automates the creation of DEB, RPM, and Pacman packages.
# Supports native and Docker-based builds.

VERSION="5.2.0"
OUTPUT_DIR="dist-packages"
mkdir -p "$OUTPUT_DIR"

build_deb() {
    echo "Building Debian package..."
    if [[ "$DOCKER" == "true" ]]; then
        docker run --rm -v "$(pwd)":/build -w /build debian:bullseye sh -c "
            apt update && apt install -y debhelper python3-all python3-pip python3-venv curl
            curl -sSf https://rye-up.com/get | RYE_INSTALL_OPTION='--yes' bash
            source \$HOME/.rye/env
            dpkg-buildpackage -us -uc -b"
    else
        dpkg-buildpackage -us -uc -b
    fi
    mv ../pnp_${VERSION}_*.deb "$OUTPUT_DIR/" 2>/dev/null || true
}

build_rpm() {
    echo "Building RPM package..."
    if [[ "$DOCKER" == "true" ]]; then
        docker run --rm -v "$(pwd)":/build -w /build fedora:latest sh -c "
            dnf install -y rpm-build python3-devel curl
            curl -sSf https://rye-up.com/get | RYE_INSTALL_OPTION='--yes' bash
            source \$HOME/.rye/env
            rpmbuild -ba pnp.spec"
    else
        rpmbuild -ba pnp.spec
    fi
    mv ~/rpmbuild/RPMS/*/*.rpm "$OUTPUT_DIR/" 2>/dev/null || true
}

build_arch() {
    echo "Building Arch Linux package..."
    if [[ "$DOCKER" == "true" ]]; then
        docker run --rm -v "$(pwd)":/build -w /build archlinux:latest sh -c "
            pacman -Syu --noconfirm base-devel python curl
            useradd -m builduser
            chown -R builduser:builduser /build
            sudo -u builduser bash -c 'curl -sSf https://rye-up.com/get | RYE_INSTALL_OPTION=\"--yes\" bash && source \$HOME/.rye/env && makepkg -f'"
    else
        makepkg -f
    fi
    mv pnp-*.pkg.tar.zst "$OUTPUT_DIR/" 2>/dev/null || true
}

DOCKER="false"
if [[ "$1" == "--docker" ]]; then
    DOCKER="true"
    shift
fi

case "$1" in
    --all)
        build_deb
        build_rpm
        build_arch
        ;;
    --deb)
        build_deb
        ;;
    --rpm)
        build_rpm
        ;;
    --arch)
        build_arch
        ;;
    *)
        echo "Usage: $0 [--docker] [--all|--deb|--rpm|--arch]"
        exit 1
        ;;
esac
