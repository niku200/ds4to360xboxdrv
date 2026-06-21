#!/bin/sh

# PNP Package Builder Script
# Automates the creation of DEB, RPM, and Pacman packages.
# Supports native and Docker-based builds.

VERSION="5.2.0"
PROJECT_NAME="pnp"
OUTPUT_DIR="dist-packages"
SOURCE_TARBALL="${PROJECT_NAME}-${VERSION}.tar.gz"

mkdir -p "$OUTPUT_DIR"

# Step 1: Prepare local source tarball
echo "Preparing local source tarball: $SOURCE_TARBALL..."
# We use git archive if in a git repo, otherwise use tar
if git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
    git archive --format=tar.gz --prefix="${PROJECT_NAME}-${VERSION}/" -o "$SOURCE_TARBALL" HEAD
else
    tar -czf "$SOURCE_TARBALL" --transform "s|^|${PROJECT_NAME}-${VERSION}/|" --exclude="$SOURCE_TARBALL" --exclude="$OUTPUT_DIR" .
fi

build_deb() {
    echo "Building Debian package..."
    if [ "$DOCKER" = "true" ]; then
        docker run --rm -v "$(pwd)":/build -w /build debian:bookworm sh -c "
            apt update && apt install -y debhelper python3-all python3-pip python3-venv curl
            curl -LsSf https://astral.sh/uv/install.sh | sh
            . \$HOME/.local/bin/env
            dpkg-buildpackage -us -uc -b"
    else
        if ! command -v dpkg-buildpackage > /dev/null 2>&1; then
            echo "Error: dpkg-buildpackage not found. Install 'dpkg-dev' or run with --docker."
            return 1
        fi
        dpkg-buildpackage -us -uc -b
    fi
    # Use glob carefully in POSIX sh, it should work if file exists
    for f in ../pnp_${VERSION}_*.deb; do
        if [ -f "$f" ]; then mv "$f" "$OUTPUT_DIR/"; fi
    done
}

build_rpm() {
    echo "Building RPM package..."
    if [ "$DOCKER" = "true" ]; then
        docker run --rm -v "$(pwd)":/build -w /build fedora:latest sh -c "
            dnf install -y rpm-build python3-devel curl
            curl -LsSf https://astral.sh/uv/install.sh | sh
            . \$HOME/.local/bin/env
            mkdir -p ~/rpmbuild/SOURCES
            cp $SOURCE_TARBALL ~/rpmbuild/SOURCES/
            rpmbuild -ba pnp.spec"
    else
        if ! command -v rpmbuild > /dev/null 2>&1; then
            echo "Error: rpmbuild not found. Install 'rpm-build' or run with --docker."
            return 1
        fi
        mkdir -p "$HOME/rpmbuild/SOURCES"
        cp "$SOURCE_TARBALL" "$HOME/rpmbuild/SOURCES/"
        rpmbuild -ba pnp.spec
    fi
    for f in "$HOME"/rpmbuild/RPMS/*/*.rpm; do
        if [ -f "$f" ]; then mv "$f" "$OUTPUT_DIR/"; fi
    done
}

build_arch() {
    echo "Building Arch Linux package..."
    if [ "$DOCKER" = "true" ]; then
        docker run --rm -v "$(pwd)":/build -w /build archlinux:latest sh -c "
            pacman -Syu --noconfirm base-devel python curl
            useradd -m builduser
            chown -R builduser:builduser /build
            sudo -u builduser bash -c 'curl -LsSf https://astral.sh/uv/install.sh | sh && . \$HOME/.local/bin/env && makepkg -f'"
    else
        if ! command -v makepkg > /dev/null 2>&1; then
            echo "Error: makepkg not found. Run with --docker."
            return 1
        fi
        makepkg -f
    fi
    for f in pnp-*.pkg.tar.zst; do
        if [ -f "$f" ]; then mv "$f" "$OUTPUT_DIR/"; fi
    done
}

cleanup() {
    echo "Cleaning up..."
    rm -f "$SOURCE_TARBALL"
}

DOCKER="false"
if [ "$1" = "--docker" ]; then
    DOCKER="true"
    shift
fi

case "$1" in
    --all)
        build_deb
        build_rpm
        build_arch
        cleanup
        ;;
    --deb)
        build_deb
        cleanup
        ;;
    --rpm)
        build_rpm
        cleanup
        ;;
    --arch)
        build_arch
        cleanup
        ;;
    *)
        echo "Usage: $0 [--docker] [--all|--deb|--rpm|--arch]"
        cleanup
        exit 1
        ;;
esac
