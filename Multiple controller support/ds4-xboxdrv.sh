#!/bin/bash

LOCK_FILE="/var/lock/ds4-xboxdrv.lock"
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

DS4_VID="054c"; DS4_PID="09cc"
PS3_VID="054c"; PS3_PID="0268"
PS5_VID="054c"; PS5_PID="0ce6"
DEVICES_FILE="/proc/bus/input/devices"
CHECK_INTERVAL_SEC=5

declare -A CONTROLLER_MAP
declare -A EVSIEVE_PIDS
declare -A XBOXDRV_PIDS
declare -A VIRTUAL_LINKS
declare -A VIRTUAL_EVENTS

function cleanup_controller() {
  local event_path="$1"
  local virt_link="${VIRTUAL_LINKS[$event_path]}"
  local virt_event="${VIRTUAL_EVENTS[$event_path]}"
  local xboxdrv_pid="${XBOXDRV_PIDS[$event_path]}"
  local evsieve_pid="${EVSIEVE_PIDS[$event_path]}"
  [ -n "$xboxdrv_pid" ] && kill "$xboxdrv_pid" 2>/dev/null && wait "$xboxdrv_pid" 2>/dev/null
  [ -n "$evsieve_pid" ] && kill "$evsieve_pid" 2>/dev/null && wait "$evsieve_pid" 2>/dev/null
  [ -n "$virt_link" ] && [ -L "$virt_link" ] && rm -f "$virt_link"
  unset CONTROLLER_MAP["$event_path"]
  unset EVSIEVE_PIDS["$event_path"]
  unset XBOXDRV_PIDS["$event_path"]
  unset VIRTUAL_LINKS["$event_path"]
  unset VIRTUAL_EVENTS["$event_path"]
}

function steam_running() {
  pgrep -x "steam" >/dev/null || pgrep -x "steam.sh" >/dev/null || pgrep -x "steamwebhelper" >/dev/null
}

while true; do
  # Scan for all supported controllers
  mapfile -t found_devices < <(
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
      }
    }
    ' "$DEVICES_FILE"
  )

  # Build a map for all detected devices
  declare -A new_map
  for info in "${found_devices[@]}"; do
    read -r event_path vid pid <<<"$info"
    full_evdev="/dev/input/${event_path}"
    # The key is the event_path (eventX)
    new_map["$event_path"]="$vid:$pid:$full_evdev"
  done

  # Remove controllers no longer present
  for event_path in "${!CONTROLLER_MAP[@]}"; do
    if [[ -z "${new_map[$event_path]}" || $(steam_running) ]]; then
      echo "$(date): Controller $event_path disconnected or Steam running. Cleaning up..."
      cleanup_controller "$event_path"
    fi
  done

  # Add new controllers or restart if processes died
  for event_path in "${!new_map[@]}"; do
    read -r vid pid devpath <<<"$(echo "${new_map[$event_path]}" | tr ':' ' ')"
    virt_link="/dev/input/evsieve_${event_path}"
    CONTROLLER_MAP["$event_path"]="$vid:$pid:$devpath"
    VIRTUAL_LINKS["$event_path"]="$virt_link"

    # (re)start evsieve if not running for this device
    evsieve_pid="${EVSIEVE_PIDS[$event_path]}"
    if ! kill -0 "$evsieve_pid" 2>/dev/null; then
      [ -L "$virt_link" ] && rm -f "$virt_link"
      echo "$(date): Starting evsieve for $devpath as $virt_link..."
      sudo evsieve --input "$devpath" grab --output create-link="$virt_link" name="Evsieve DS4 Virtual $event_path" &
      EVSIEVE_PIDS["$event_path"]=$!
      # Wait for symlink
      for i in {1..10}; do [ -L "$virt_link" ] && break; sleep 0.25; done
      if ! [ -L "$virt_link" ]; then
        echo "$(date): Failed to create $virt_link. Skipping $event_path."
        cleanup_controller "$event_path"
        continue
      fi
      VIRTUAL_LINKS["$event_path"]="$virt_link"
      echo "evsieve started for $event_path with PID: ${EVSIEVE_PIDS[$event_path]}"
    fi

    # (re)start xboxdrv if not running for this device
    xboxdrv_pid="${XBOXDRV_PIDS[$event_path]}"
    virt_event="/dev/input/$(basename $(readlink -f "$virt_link"))"
    VIRTUAL_EVENTS["$event_path"]="$virt_event"
    if ! kill -0 "$xboxdrv_pid" 2>/dev/null; then
      case "$pid" in
        "$DS4_PID") echo "Controller $event_path type: DualShock 4 (PS4)";;
        "$PS3_PID") echo "Controller $event_path type: DualShock 3 (PS3)";;
        "$PS5_PID") echo "Controller $event_path type: DualSense (PS5)";;
        *) echo "Controller $event_path type: Unknown (pid=$pid)";;
      esac
      sleep 1
      XBOXDRV_CMD="/usr/bin/xboxdrv \
        --evdev \"${virt_event}\" \
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
      XBOXDRV_PIDS["$event_path"]=$!
      echo "xboxdrv started for $event_path with PID: ${XBOXDRV_PIDS[$event_path]}"
    fi
  done

  sleep "$CHECK_INTERVAL_SEC"
done