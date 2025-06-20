#!/bin/bash

LOCK_FILE="/var/run/ds4-xboxdrv.lock"
if [ -f "$LOCK_FILE" ]; then
  EXISTING_PID=$(cat "$LOCK_FILE" 2>/dev/null)
  if [ -n "$EXISTING_PID" ] && kill -0 "$EXISTING_PID" 2>/dev/null; then
    echo "$(date): Another instance of ds4-xboxdrv.sh is already running (PID: $EXISTING_PID). Exiting."
    exit 1
  else
    echo "$(date): Stale lock file found for PID $EXISTING_PID. Removing."
    rm -f "$LOCK_FILE"
  fi
fi
echo $$ > "$LOCK_FILE"
trap 'rm -f "$LOCK_FILE"' EXIT

DS4_VID="054c"; DS4_PID="09cc" # DualShock 4
PS3_VID="054c"; PS3_PID="0268" # DualShock 3 / Sixaxis
PS5_VID="054c"; PS5_PID="0ce6" # DualSense (PS5)
DEVICES_FILE="/proc/bus/input/devices"
CHECK_INTERVAL_SEC=5

CURRENT_XBOXDRV_PID=""
CURRENT_EVSIEVE_PID=""
CURRENT_EVDEV_PATH=""
CURRENT_VIRTUAL_LINK=""
CURRENT_DEVICE_ID=""

function cleanup() {
  [ -n "$CURRENT_XBOXDRV_PID" ] && kill "$CURRENT_XBOXDRV_PID" 2>/dev/null && wait "$CURRENT_XBOXDRV_PID" 2>/dev/null
  [ -n "$CURRENT_EVSIEVE_PID" ] && kill "$CURRENT_EVSIEVE_PID" 2>/dev/null && wait "$CURRENT_EVSIEVE_PID" 2>/dev/null
  [ -n "$CURRENT_VIRTUAL_LINK" ] && [ -L "$CURRENT_VIRTUAL_LINK" ] && rm -f "$CURRENT_VIRTUAL_LINK"
  CURRENT_XBOXDRV_PID=""
  CURRENT_EVSIEVE_PID=""
  CURRENT_EVDEV_PATH=""
  CURRENT_VIRTUAL_LINK=""
  CURRENT_DEVICE_ID=""
}

while true; do
  # --- Find controller (as before) ---
  EVENT_INFO=$(
    awk -v DS4_V="$DS4_VID" -v DS4_P="$DS4_PID" \
        -v PS3_V="$PS3_VID" -v PS3_P="$PS3_PID" \
        -v PS5_V="$PS5_VID" -v PS5_P="$PS5_PID" '
    BEGIN { RS="\n\n"; FS="\n" }
    {
      is_target_device = 0
      current_vid = ""
      current_pid = ""
      event_device = ""
      is_joystick = 0
      for (i=1; i<=NF; i++) {
        if ($i ~ /^I:.*Vendor=/) {
            match($i, /Vendor=([0-9a-fA-F]+)/); current_vid = tolower(substr($i, RSTART+7, RLENGTH-7))
            match($i, /Product=([0-9a-fA-F]+)/); current_pid = tolower(substr($i, RSTART+8, RLENGTH-8))
        }
        if ($i ~ /^H: Handlers=.*event[0-9]+/) {
          match($i, /event[0-9]+/); event_device = substr($i, RSTART, RLENGTH)
        }
        if ($i ~ /^H: Handlers=.*js[0-9]+/) {
          is_joystick = 1
        }
      }
      if (current_vid == DS4_V && current_pid == DS4_P) { is_target_device = 1; }
      else if (current_vid == PS3_V && current_pid == PS3_P) { is_target_device = 1; }
      else if (current_vid == PS5_V && current_pid == PS5_P) { is_target_device = 1; }
      if (is_target_device && event_device != "" && is_joystick) {
        print event_device " " current_vid " " current_pid
        exit
      }
    }
    ' "$DEVICES_FILE"
  )

  if [ -n "$EVENT_INFO" ]; then
    read -r EVENT_PATH DETECTED_VID DETECTED_PID <<< "$EVENT_INFO"
    FULL_EVDEV_PATH="/dev/input/${EVENT_PATH}"
    DEVICE_ID="${DETECTED_VID}:${DETECTED_PID}:${FULL_EVDEV_PATH}"
  else
    # No controller: clean up and wait
    if [ -n "$CURRENT_DEVICE_ID" ]; then
      echo "$(date): Controller disconnected. Cleaning up..."
      cleanup
    fi
    sleep "$CHECK_INTERVAL_SEC"
    continue
  fi

  # --- If device changed, clean up first ---
  if [ "$DEVICE_ID" != "$CURRENT_DEVICE_ID" ]; then
    echo "$(date): New controller detected or device changed."
    cleanup
    CURRENT_DEVICE_ID="$DEVICE_ID"
  fi

  # --- Steam running? If so, cleanup and do not run mapping ---
  if pgrep -x "steam" >/dev/null || pgrep -x "steam.sh" >/dev/null || pgrep -x "steamwebhelper" >/dev/null; then
    if [ -n "$CURRENT_XBOXDRV_PID" ] || [ -n "$CURRENT_EVSIEVE_PID" ]; then
      echo "$(date): Steam detected. Cleaning up mapping processes."
      cleanup
    fi
    sleep "$CHECK_INTERVAL_SEC"
    continue
  fi

  # --- If processes not running, start them ---
  # (restarts only if not alive)
  VIRTUAL_LINK="/dev/input/evsieve_ds4"
  if ! kill -0 "$CURRENT_EVSIEVE_PID" 2>/dev/null; then
    [ -L "$VIRTUAL_LINK" ] && rm -f "$VIRTUAL_LINK"
    echo "$(date): Starting evsieve for $FULL_EVDEV_PATH..."
    sudo evsieve --input "$FULL_EVDEV_PATH" grab ff --output create-link="$VIRTUAL_LINK" name="Evsieve DS4 Virtual" &
    CURRENT_EVSIEVE_PID=$!
    # Wait for symlink
    for i in {1..10}; do [ -L "$VIRTUAL_LINK" ] && break; sleep 0.5; done
    if ! [ -L "$VIRTUAL_LINK" ]; then
      echo "$(date): Failed to create evsieve virtual link at $VIRTUAL_LINK. Retrying."
      kill "$CURRENT_EVSIEVE_PID" 2>/dev/null
      wait "$CURRENT_EVSIEVE_PID" 2>/dev/null
      CURRENT_EVSIEVE_PID=""
      sleep "$CHECK_INTERVAL_SEC"
      continue
    fi
    CURRENT_VIRTUAL_LINK="$VIRTUAL_LINK"
    echo "evsieve started with PID: $CURRENT_EVSIEVE_PID"
  fi

  if ! kill -0 "$CURRENT_XBOXDRV_PID" 2>/dev/null; then
    VIRTUAL_EVSOCK_DEVICE="/dev/input/$(basename $(readlink -f $CURRENT_VIRTUAL_LINK))"
    echo "Virtual evsieve device created at: $VIRTUAL_EVSOCK_DEVICE"
    case "${DETECTED_PID}" in
      "${DS4_PID}")
        echo "Controller Type: DualShock 4 (PS4)"
        ;;
      "${PS3_PID}")
        echo "Controller Type: DualShock 3 / Sixaxis (PS3)"
        ;;
      "${PS5_PID}")
        echo "Controller Type: DualSense (PS5)"
        ;;
      *)
        echo "Controller Type: Unknown supported PlayStation controller (PID: ${DETECTED_PID})"
        ;;
    esac
    sleep 1
    XBOXDRV_CMD="/usr/bin/xboxdrv \
      --evdev \"${VIRTUAL_EVSOCK_DEVICE}\" \
      --mimic-xpad \
      --silent \
      --quiet \
      --force-feedback \
      --rumble-gain 15% \
      --axismap -y1=y1,-y2=y2 \
      --evdev-absmap ABS_HAT0X=dpad_x,ABS_HAT0Y=dpad_y,ABS_X=X1,ABS_Y=Y1,ABS_RX=X2,ABS_RY=Y2,ABS_Z=LT,ABS_RZ=RT \
      --evdev-keymap BTN_SOUTH=A,BTN_EAST=B,BTN_NORTH=Y,BTN_WEST=X,BTN_START=start,BTN_MODE=guide,BTN_SELECT=back,BTN_TL=LB,BTN_TR=RB,BTN_TL2=LT,BTN_TR2=RT,BTN_THUMBL=TL,BTN_THUMBR=TR \
      --no-dbus"
    eval "$XBOXDRV_CMD" &
    CURRENT_XBOXDRV_PID=$!
    echo "xboxdrv started with PID: $CURRENT_XBOXDRV_PID"
  fi

  sleep "$CHECK_INTERVAL_SEC"
done
