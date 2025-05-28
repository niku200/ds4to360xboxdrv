#!/bin/bash
# Define the Vendor and Product IDs for DualShock 4 (PS4)
DSDEVVID="054c"
DSDEVPID="09cc"

# Path to /proc/bus/input/devices
DEVICES_FILE="/proc/bus/input/devices"

# Max retries and delay for finding the device
MAX_RETRIES=10
RETRY_DELAY_SEC=1

FULL_EVDEV_PATH=""
RETRY_COUNT=0

# Loop to try and find the event device path
while [ -z "$FULL_EVDEV_PATH" ] && [ "$RETRY_COUNT" -lt "$MAX_RETRIES" ]; do
  echo "Attempt $((RETRY_COUNT + 1))/${MAX_RETRIES}: Searching for DualShock 4 controller..." >&2
  EVENT_PATH=$(
    awk -v V="$DSDEVVID" -v P="$DSDEVPID" '
    BEGIN { RS="\n\n"; FS="\n" }
    {
      is_target_device = 0
      event_device = ""
      for (i=1; i<=NF; i++) {
        if ($i ~ "Vendor=" V " Product=" P) {
          is_target_device = 1
        }
        if ($i ~ /^H: Handlers=.*event[0-9]+/) {
          match($i, /event[0-9]+/);
          event_device = substr($i, RSTART, RLENGTH);
        }
      }
      if (is_target_device && event_device != "") {
        print event_device
        exit
      }
    }
    ' "$DEVICES_FILE"
  )

  if [ -n "$EVENT_PATH" ]; then
    FULL_EVDEV_PATH="/dev/input/${EVENT_PATH}"
    echo "DualShock 4 found at: ${FULL_EVDEV_PATH}." >&2
  else
    echo "DualShock 4 not found. Retrying in ${RETRY_DELAY_SEC} second(s)..." >&2
    sleep "$RETRY_DELAY_SEC"
    RETRY_COUNT=$((RETRY_COUNT + 1))
  fi
done

if [ -z "$FULL_EVDEV_PATH" ]; then
  echo "Error: DualShock 4 controller (VID ${DSDEVVID}, PID ${DSDEVPID}) not found after ${MAX_RETRIES} attempts." >&2
  exit 1
fi

# Check if xboxdrv is already running for this device path
if pgrep -f "xboxdrv --evdev ${FULL_EVDEV_PATH}" > /dev/null; then
    echo "xboxdrv is already running for ${FULL_EVDEV_PATH}." >&2
    exit 0
fi

echo "Starting xboxdrv in foreground..." >&2

exec /usr/bin/xboxdrv \
  --evdev "${FULL_EVDEV_PATH}" \
  --mimic-xpad \
  --silent \
  --quiet \
  --force-feedback \
  --axismap -y1=y1,-y2=y2 \
  --evdev-absmap ABS_HAT0X=dpad_x,ABS_HAT0Y=dpad_y,ABS_X=X1,ABS_Y=Y1,ABS_RX=X2,ABS_RY=Y2,ABS_Z=LT,ABS_RZ=RT \
  --evdev-keymap BTN_SOUTH=A,BTN_EAST=B,BTN_NORTH=Y,BTN_WEST=X,BTN_START=start,BTN_MODE=guide,BTN_SELECT=back,BTN_TL=LB,BTN_TR=RB,BTN_TL2=LT,BTN_TR2=RT,BTN_THUMBL=TL,BTN_THUMBR=TR \
  --no-dbus \
  --evdev-grab
