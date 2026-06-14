#!/bin/sh
# pnp-steam-run: Force Steam Input for any executable
# Usage: pnp-steam-run /path/to/game --args

if [ -z "$1" ]; then
    echo "Usage: pnp-steam-run /path/to/game [args...]"
    exit 1
fi

# The "Proxy AppID" trick. 480 is 'Spacewar'.
PROXY_APPID=480

# Check if Steam is running
if ! pgrep -x steam > /dev/null; then
    echo "Error: Steam is not running. Please start Steam first."
    exit 1
fi

# Ensure the executable exists
if [ ! -f "$1" ]; then
    echo "Error: Executable '$1' not found."
    exit 1
fi

# Try to find gameoverlayrenderer.so to ensure overlay and Steam Input hooks
# Common paths for Steam
STEAM_ROOT="$HOME/.steam/steam"
OVERLAY_SO="$STEAM_ROOT/ubuntu12_32/gameoverlayrenderer.so"
OVERLAY_SO_64="$STEAM_ROOT/ubuntu12_64/gameoverlayrenderer.so"

if [ -f "$OVERLAY_SO_64" ]; then
    export LD_PRELOAD="$OVERLAY_SO_64:$LD_PRELOAD"
elif [ -f "$OVERLAY_SO" ]; then
    export LD_PRELOAD="$OVERLAY_SO:$LD_PRELOAD"
fi

echo "Launching game with Steam Input proxy (AppID $PROXY_APPID) and Overlay hooks..."
echo "PNP will automatically pause once Steam Input engages."

# Export SteamAppId to force Steam Input mapping
export SteamAppId=$PROXY_APPID
export SteamGameId=$PROXY_APPID

# Run the game
exec "$@"
