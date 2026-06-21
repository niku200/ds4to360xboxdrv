#!/bin/sh
# PNP Migration Script: Move legacy configs to XDG locations

OLD_CONFIG_DIR="$HOME/.pnp"
OLD_CONFIG_FILE="$HOME/.pnp/pnp.conf"
NEW_CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/pnp"
NEW_CONFIG_FILE="$NEW_CONFIG_DIR/config.jsonc"

echo "Checking for legacy PNP configurations..."

if [ -d "$OLD_CONFIG_DIR" ]; then
    echo "Found legacy config directory: $OLD_CONFIG_DIR"
    mkdir -p "$NEW_CONFIG_DIR"

    if [ -f "$OLD_CONFIG_FILE" ]; then
        echo "Legacy config file found. PNP will automatically migrate it on next start."
        echo "A backup will be kept at $OLD_CONFIG_FILE.bak"
        cp "$OLD_CONFIG_FILE" "$OLD_CONFIG_FILE.bak"
    fi

    # Move profiles if any
    if [ -d "$OLD_CONFIG_DIR/controllers" ]; then
        echo "Moving controller profiles to $NEW_CONFIG_DIR/controllers..."
        mv "$OLD_CONFIG_DIR/controllers" "$NEW_CONFIG_DIR/"
    fi

    echo "Migration of files complete."
else
    echo "No legacy ~/.pnp directory found. No action needed."
fi

echo "PNP now uses XDG-compliant paths:"
echo "Config: $NEW_CONFIG_DIR"
echo "Cache:  ${XDG_CACHE_HOME:-$HOME/.cache}/pnp"
