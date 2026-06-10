import sys
import subprocess
import threading
import json
import os
import configparser
import logging
import tempfile
from typing import Optional, List
from gi.repository import Gtk, Adw, GLib, Gio, Gdk
try:
    import evdev
except ImportError:
    evdev = None

def is_service_active():
    import subprocess
    try:
        res = subprocess.run(["systemctl", "is-active", "pnp.service"], capture_output=True, text=True)
        return res.stdout.strip() == "active"
    except:
        return False

def check_dependencies():
    import shutil
    missing = []
    if not shutil.which('xboxdrv'):
        missing.append('xboxdrv')
    if not shutil.which('evsieve'):
        missing.append('evsieve')
    return missing

from pnp.gui.controller_widget import ControllerWidget
from pnp.gui.tray import StatusNotifierItem

logger = logging.getLogger(__name__)

STATUS_FILE = "/run/pnp/status.json"
CONFIG_DIR = "/etc/pnp"
CONFIG_PATH = "/etc/pnp/pnp.conf"
LEGACY_CONFIG_PATH = "/etc/ds4to360.conf"

class MainWindow(Adw.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.manager = None
        self.is_observer = True

        self.set_title("PNP – PS NOT PS")
        self.set_default_size(900, 700)

        # Style Manager for dark theme
        self.style_manager = Adw.StyleManager.get_default()
        self.style_manager.set_color_scheme(Adw.ColorScheme.PREFER_DARK)

        # Main Layout
        self.toolbar_view = Adw.ToolbarView()
        self.set_content(self.toolbar_view)

        # Header Bar
        self.header = Adw.HeaderBar()
        self.toolbar_view.add_top_bar(self.header)

        # View Stack and Switcher
        self.view_stack = Adw.ViewStack()
        self.view_switcher_title = Adw.ViewSwitcherTitle()
        self.view_switcher_title.set_stack(self.view_stack)
        self.header.set_title_widget(self.view_switcher_title)

        # Toast Overlay
        self.toast_overlay = Adw.ToastOverlay()
        self.toast_overlay.set_child(self.view_stack)
        self.toolbar_view.set_content(self.toast_overlay)

        # Setup Pages
        self.setup_status_page()
        self.setup_settings_page()
        self.setup_tester_page()
        self.setup_logs_page()

        # Bottom View Switcher Bar
        self.view_switcher_bar = Adw.ViewSwitcherBar()
        self.view_switcher_bar.set_stack(self.view_stack)
        self.toolbar_view.add_bottom_bar(self.view_switcher_bar)

        # Connect destroy signal early
        self.connect("destroy", self._on_destroy)

        # Defer manager initialization to background to keep UI responsive
        GLib.idle_add(self._init_backend)

        self.load_config()
        self.setup_css()
        self.start_log_monitor()

    def _init_backend(self):
        try:
            if is_service_active():
                logger.info("Service is active. GUI running in observer mode.")
                self.is_observer = True
                self.manager = None
            else:
                logger.info("Service inactive. Starting local manager.")
                from pnp.core.manager import ControllerManager
                self.is_observer = False
                self.manager = ControllerManager()
                self.manager.start()
                self.manager_handler_id = self.manager.connect('controller-list-changed', self._on_controllers_changed)
                self._refresh_controllers()

            if self.is_observer:
                self.observer_timer_id = GLib.timeout_add(1000, self._update_observer_status)

            # Tester update is always useful, but let's run it at a reasonable rate
            self.tester_timer_id = GLib.timeout_add(2000, self._update_tester_list)
            # Run once immediately
            self._update_tester_list()

            # Check dependencies
            missing = check_dependencies()
            if missing:
                self.show_toast(f"Missing dependencies: {', '.join(missing)}")
        except Exception as e:
            logger.error(f"Failed to initialize backend: {e}")
            self.show_toast("Backend initialization failed. See logs.")
        return False

    def setup_status_page(self):
        page_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        self.status_page = Adw.StatusPage(
            title="PNP Controller Mapper",
            description="Manage your DualShock and DualSense controllers.",
            icon_name="input-gaming-symbolic"
        )
        page_box.append(self.status_page)

        clamp = Adw.Clamp(maximum_size=600)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        clamp.set_child(box)
        page_box.append(clamp)

        self.controllers_group = Adw.PreferencesGroup(title="Active Controllers")
        box.append(self.controllers_group)

        self.controllers_list = Gtk.ListBox()
        self.controllers_list.add_css_class("boxed-list")
        self.controllers_list.set_selection_mode(Gtk.SelectionMode.NONE)
        self.controllers_group.add(self.controllers_list)

        scroll = Gtk.ScrolledWindow()
        scroll.set_child(page_box)
        self.view_stack.add_titled_with_icon(scroll, "status", "Status", "network-transmit-receive-symbolic")

    def setup_settings_page(self):
        self.settings_page = Adw.PreferencesPage()

        # General Settings
        gen_group = Adw.PreferencesGroup(title="General Settings")
        self.settings_page.add(gen_group)

        self.steam_switch = Gtk.Switch(valign=Gtk.Align.CENTER)
        steam_row = Adw.ActionRow(title="Steam Conflict Prevention", subtitle="Pause emulation when Steam is running")
        steam_row.add_suffix(self.steam_switch)
        gen_group.add(steam_row)

        self.rumble_entry = Gtk.Entry(valign=Gtk.Align.CENTER)
        rumble_row = Adw.ActionRow(title="Rumble Gain", subtitle="Global force feedback strength")
        rumble_row.add_suffix(self.rumble_entry)
        gen_group.add(rumble_row)

        # Mapping Settings
        map_group = Adw.PreferencesGroup(title="Global Mapping", description="Default translation for all controllers")
        self.settings_page.add(map_group)

        self.axismap_entry = Gtk.Entry(valign=Gtk.Align.CENTER, hexpand=True)
        self.absmap_entry = Gtk.Entry(valign=Gtk.Align.CENTER, hexpand=True)
        self.keymap_entry = Gtk.Entry(valign=Gtk.Align.CENTER, hexpand=True)

        for title, entry, desc in [
            ("Axis Map", self.axismap_entry, "Analog stick mappings"),
            ("Absolute Map", self.absmap_entry, "Triggers and D-pad mappings"),
            ("Key Map", self.keymap_entry, "Buttons mappings")
        ]:
            row = Adw.ActionRow(title=title, subtitle=desc)
            row.add_suffix(entry)
            map_group.add(row)

        # Standalone Button handling in AdwPreferencesPage
        # Adw.PreferencesPage.add only takes Adw.PreferencesGroup.
        # For other widgets, we wrap them in a group without title.
        btn_group = Adw.PreferencesGroup()
        save_btn = Gtk.Button(label="Save & Apply", halign=Gtk.Align.CENTER, margin_top=24, css_classes=["suggested-action", "pill"])
        save_btn.set_size_request(200, -1)
        save_btn.connect("clicked", self.on_save_clicked)
        btn_group.add(save_btn)
        self.settings_page.add(btn_group)

        self.view_stack.add_titled_with_icon(self.settings_page, "settings", "Settings", "emblem-system-symbolic")

    def setup_tester_page(self):
        self.tester_timer_id = None
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12, margin_top=12, margin_bottom=12, margin_start=12, margin_end=12)

        status_page = Adw.StatusPage(
            title="Input Tester",
            description="Verify your virtual Xbox 360 controller is working.",
            icon_name="input-gaming-symbolic"
        )
        box.append(status_page)

        clamp = Adw.Clamp(maximum_size=800)
        inner_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        clamp.set_child(inner_box)
        box.append(clamp)

        self.tester_label = Gtk.Label(label="No input detected yet. Move sticks or press buttons on your controller.")
        self.tester_label.add_css_class("body")
        self.tester_label.set_wrap(True)
        self.tester_label.set_justify(Gtk.Justification.CENTER)
        inner_box.append(self.tester_label)

        self.tester_list = Gtk.ListBox()
        self.tester_list.add_css_class("boxed-list")
        self.tester_list.set_selection_mode(Gtk.SelectionMode.NONE)
        inner_box.append(self.tester_list)

        scroll = Gtk.ScrolledWindow()
        scroll.set_child(box)
        self.view_stack.add_titled_with_icon(scroll, "tester", "Tester", "preferences-desktop-peripherals-symbolic")

        self.active_testers = {} # path -> {row, bars: {code -> progress}}

    def _update_tester_list(self):
        # Synchronize tester rows with active controllers
        active_paths = set()

        # Only iterate manager controllers if we have a manager (manager mode)
        if self.manager:
            for controller in list(self.manager.controllers.values()):
                if controller.is_active:
                    link_id = f"{controller.serial}_{os.path.basename(controller.device_path)}"
                    evsieve_link = f"/dev/input/evsieve_{link_id}"
                    if os.path.exists(evsieve_link):
                        active_paths.add(evsieve_link)
                        if evsieve_link not in self.active_testers:
                            self._add_tester_row(evsieve_link, controller.name)

        # Add virtual Xbox 360 controllers (output of xboxdrv)
        # These usually appear as /dev/input/js* or /dev/input/event*
        # but with 'Microsoft' or 'Xbox 360' in their name.
        import pyudev
        ctx = pyudev.Context()
        for device in ctx.list_devices(subsystem='input', ID_INPUT_JOYSTICK='1'):
            model = device.get('ID_MODEL', '').lower()
            if 'xbox' in model or 'microsoft' in model:
                path = device.device_node
                if path and path not in active_paths:
                    active_paths.add(path)
                    if path not in self.active_testers:
                        self._add_tester_row(path, f"Virtual: {device.get('ID_MODEL', 'Xbox 360 Controller')}")

        # Remove stale testers
        for path in list(self.active_testers.keys()):
            if path not in active_paths:
                self.tester_list.remove(self.active_testers[path]['row'])
                del self.active_testers[path]

        if not active_paths:
            self.tester_label.set_text("No virtual controllers active. Enable a controller in the Status tab to test here.")
        else:
            self.tester_label.set_text(f"Monitoring {len(active_paths)} active virtual controller(s).")

        return True

    def _add_tester_row(self, path, name):
        is_virtual = "Virtual" in name
        row = Adw.ActionRow(title=name, subtitle=f"Device: {path}")

        icon = "input-gaming-symbolic" if not is_virtual else "controller-symbolic"
        row.add_prefix(Gtk.Image.new_from_icon_name(icon))

        badge = Gtk.Label(label="Virtual" if is_virtual else "Physical")
        badge.add_css_class("pill")
        badge.add_css_class("info" if is_virtual else "success")
        row.add_suffix(badge)

        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=24, margin_top=6, margin_bottom=6)

        # Left: Controller Visualizer
        viz_grid = Gtk.Grid(column_spacing=8, row_spacing=8)
        viz_grid.set_halign(Gtk.Align.CENTER)
        viz_grid.set_valign(Gtk.Align.CENTER)

        viz_buttons = {}
        def add_viz(label, code, row, col):
            lbl = Gtk.Label(label=label)
            lbl.add_css_class("controller-btn")
            lbl.add_css_class("dim-label")
            lbl.set_size_request(32, 32)
            viz_grid.attach(lbl, col, row, 1, 1)
            viz_buttons[code] = lbl

        # Advanced Controller Visualizer Grid (5x7)
        # Col 0: Left Shoulder/Trigger
        # Col 1-2: D-Pad & Left Stick
        # Col 3: Function buttons (Center)
        # Col 4-5: Action buttons & Right Stick
        # Col 6: Right Shoulder/Trigger

        # Action Buttons (Diamond)
        add_viz("Y", 308, 1, 5)
        add_viz("X", 307, 2, 4)
        add_viz("B", 305, 2, 6)
        add_viz("A", 304, 3, 5)

        # D-Pad
        add_viz("DU", 16, 1, 1)
        add_viz("DL", 18, 2, 0)
        add_viz("DR", 19, 2, 2)
        add_viz("DD", 17, 3, 1)

        # Function Buttons
        add_viz("Bk", 314, 2, 3)
        add_viz("G", 316, 1, 3)
        add_viz("St", 315, 3, 3)

        # Shoulders
        add_viz("LB", 310, 0, 1)
        add_viz("RB", 311, 0, 5)

        # Thumbstick Clicks
        add_viz("L3", 317, 4, 1)
        add_viz("R3", 318, 4, 5)

        # D-pad (usually 16 or Hat) - for now just buttons if available
        # In xboxdrv mapping, dpad usually mapped to keys or hat
        # We can add them if they come through as keys

        main_box.append(viz_grid)

        # Right: Bars
        right_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6, hexpand=True)
        grid = Gtk.Grid(column_spacing=12, row_spacing=4)
        right_box.append(grid)

        bars = {}
        axes = [("LX", 0), ("LY", 1), ("RX", 2), ("RY", 3), ("LT", 4), ("RT", 5)]
        for i, (label, code) in enumerate(axes):
            lbl = Gtk.Label(label=label)
            lbl.add_css_class("caption")
            progress = Gtk.ProgressBar(hexpand=True, valign=Gtk.Align.CENTER)
            progress.set_fraction(0.5 if i < 4 else 0.0)
            grid.attach(lbl, 0, i, 1, 1)
            grid.attach(progress, 1, i, 1, 1)
            bars[code] = progress

        main_box.append(right_box)

        # Add visualizer buttons to the main buttons dict for updates
        buttons = viz_buttons

        row.set_activatable_widget(None)
        row.add_suffix(main_box)
        self.tester_list.append(row)

        self.active_testers[path] = {'row': row, 'bars': bars, 'buttons': buttons}

        # Start a thread to read evdev events for this device
        if evdev:
            threading.Thread(target=self._read_evdev_events, args=(path,), daemon=True).start()

    def _read_evdev_events(self, path):
        # Throttle updates for high-frequency axis events
        last_update = {} # code -> time
        try:
            with evdev.InputDevice(path) as device:
                for event in device.read_loop():
                    if path not in self.active_testers or not self.log_monitor_active:
                        break

                    now = GLib.get_monotonic_time() / 1000000.0
                    if event.type == evdev.ecodes.EV_ABS:
                        # Throttle axes to ~60Hz to prevent main loop congestion
                        if now - last_update.get(event.code, 0) < 0.016:
                            continue
                        last_update[event.code] = now
                        absinfo = device.absinfo(event.code)
                        GLib.idle_add(self._update_tester_bar, path, event.code, event.value, absinfo)
                    elif event.type == evdev.ecodes.EV_KEY:
                        GLib.idle_add(self._update_tester_button, path, event.code, event.value)
        except Exception as e:
            # Only log error if it's not a common 'Device vanished' error during shutdown
            if self.log_monitor_active:
                logger.debug(f"Info: Stopped monitoring evdev for {path}: {e}")

    def _update_tester_button(self, path, code, value):
        if path in self.active_testers:
            buttons = self.active_testers[path]['buttons']
            if code in buttons:
                lbl = buttons[code]
                if value:
                    lbl.remove_css_class("dim-label")
                    lbl.add_css_class("success")
                else:
                    lbl.add_css_class("dim-label")
                    lbl.remove_css_class("success")
        return False

    def _update_tester_bar(self, path, code, value, absinfo):
        if path in self.active_testers:
            bars = self.active_testers[path]['bars']
            # Map evdev codes to our tester bars (xbox 360 codes)
            # ABS_X=0, ABS_Y=1, ABS_RX=3, ABS_RY=4, ABS_Z=2 (LT), ABS_RZ=5 (RT)
            mapping = {0: 0, 1: 1, 3: 2, 4: 3, 2: 4, 5: 5}
            if code in mapping:
                bar_idx = mapping[code]
                fraction = (value - absinfo.min) / (absinfo.max - absinfo.min)
                bars[bar_idx].set_fraction(fraction)
        return False

    def setup_logs_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)

        # Toolbar for logs
        action_bar = Gtk.ActionBar()
        copy_btn = Gtk.Button(label="Copy All Logs")
        copy_btn.add_css_class("pill")
        copy_btn.connect("clicked", self._on_copy_logs_clicked)
        action_bar.pack_start(copy_btn)
        box.append(action_bar)

        self.log_view = Gtk.TextView(editable=False, monospace=True)
        self.log_view.set_margin_start(12)
        self.log_view.set_margin_end(12)
        self.log_view.set_margin_top(12)
        self.log_view.set_margin_bottom(12)
        self.log_view.add_css_class("card")

        scroll = Gtk.ScrolledWindow(vexpand=True)
        scroll.set_child(self.log_view)
        box.append(scroll)

        self.view_stack.add_titled_with_icon(box, "logs", "Logs", "view-list-bullet-symbolic")

    def _on_destroy(self, *args):
        self.log_monitor_active = False
        if hasattr(self, 'log_proc'):
            self.log_proc.terminate()

        if not self.is_observer:
            if hasattr(self, 'manager_handler_id'):
                self.manager.disconnect(self.manager_handler_id)
            if hasattr(self, 'tester_timer_id') and self.tester_timer_id:
                GLib.source_remove(self.tester_timer_id)
            self.manager.stop_all()
        else:
            if hasattr(self, 'observer_timer_id'):
                GLib.source_remove(self.observer_timer_id)

    def load_config(self):
        config = configparser.ConfigParser(interpolation=None, delimiters=('=',))
        if os.path.exists(CONFIG_PATH):
            config.read(CONFIG_PATH)
        elif os.path.exists(LEGACY_CONFIG_PATH):
            config.read(LEGACY_CONFIG_PATH)

        self.rumble_entry.set_text(config.get('settings', 'rumble_gain', fallback='15%'))
        self.steam_switch.set_active(config.getboolean('settings', 'steam_conflict_check', fallback=True))
        self.axismap_entry.set_text(config.get('mapping', 'axismap', fallback='-y1=y1,-y2=y2'))
        self.absmap_entry.set_text(config.get('mapping', 'absmap', fallback='ABS_X=x1,ABS_Y=y1,ABS_RX=x2,ABS_RY=y2,ABS_Z=lt,ABS_RZ=rt,ABS_HAT0X=dpad_x,ABS_HAT0Y=dpad_y'))
        self.keymap_entry.set_text(config.get('mapping', 'keymap', fallback='BTN_SOUTH=a,BTN_EAST=b,BTN_NORTH=x,BTN_WEST=y,BTN_TL=lb,BTN_TR=rb,BTN_TL2=lt,BTN_TR2=rt,BTN_THUMBL=tl,BTN_THUMBR=tr,BTN_SELECT=back,BTN_START=start,BTN_MODE=guide'))

    def on_save_clicked(self, button):
        config = configparser.ConfigParser(interpolation=None, delimiters=('=',))
        if os.path.exists(CONFIG_PATH):
            config.read(CONFIG_PATH)
        elif os.path.exists(LEGACY_CONFIG_PATH):
            config.read(LEGACY_CONFIG_PATH)

        if 'settings' not in config: config['settings'] = {}
        if 'mapping' not in config: config['mapping'] = {}

        config['settings']['rumble_gain'] = self.rumble_entry.get_text()
        config['settings']['steam_conflict_check'] = 'true' if self.steam_switch.get_active() else 'false'
        config['mapping']['axismap'] = self.axismap_entry.get_text()
        config['mapping']['absmap'] = self.absmap_entry.get_text()
        config['mapping']['keymap'] = self.keymap_entry.get_text()

        try:
            with tempfile.NamedTemporaryFile(mode="w", prefix="pnp-", suffix=".conf", delete=False) as tmp:
                config.write(tmp)
                tmp_path = tmp.name

            # Combine multiple operations into one pkexec call
            # Use 'install' to set permissions and copy in one go
            cmd = f"mkdir -p {CONFIG_DIR} && install -m 644 {tmp_path} {CONFIG_PATH} && rm {tmp_path}"
            subprocess.run(["pkexec", "sh", "-c", cmd], check=True)
            self.show_toast("Settings saved. Restart service to apply.")
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            self.show_toast(f"Error saving: {e}")

    def show_toast(self, message):
        self.toast_overlay.add_toast(Adw.Toast(title=message))

    def _on_copy_logs_clicked(self, btn):
        buffer = self.log_view.get_buffer()
        text = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), False)
        clipboard = self.get_display().get_clipboard()
        clipboard.set(text)
        self.show_toast("Logs copied to clipboard")

    def _on_controllers_changed(self, manager):
        GLib.idle_add(self._refresh_controllers)

    def _refresh_controllers(self):
        while (child := self.controllers_list.get_first_child()):
            if isinstance(child, Gtk.ListBoxRow):
                row = child.get_child()
                if hasattr(row, 'cleanup'):
                    row.cleanup()
            self.controllers_list.remove(child)

        if not self.manager.controllers:
            row = Adw.ActionRow(title="No controllers detected")
            self.controllers_list.append(row)
        else:
            for controller in self.manager.controllers.values():
                self.controllers_list.append(ControllerWidget(controller))

    def _update_observer_status(self):
        if not os.path.exists(STATUS_FILE):
            self.status_page.set_title("Service Initializing...")
            return True

        try:
            with open(STATUS_FILE, "r") as f:
                data = json.load(f)

            while (child := self.controllers_list.get_first_child()):
                self.controllers_list.remove(child)

            controllers = data.get("controllers", [])
            if not controllers:
                self.controllers_list.append(Adw.ActionRow(title="No controllers active in service"))
            else:
                for name in controllers:
                    row = Adw.ActionRow(title=name, subtitle="Managed by system service")
                    row.add_prefix(Gtk.Image.new_from_icon_name("input-gaming-symbolic"))
                    badge = Gtk.Label(label="Running")
                    badge.add_css_class("success")
                    badge.add_css_class("pill")
                    row.add_suffix(badge)
                    self.controllers_list.append(row)

            if data.get("steam_blocking"):
                self.status_page.set_title("Paused (Steam Conflict)")
            else:
                self.status_page.set_title(f"{len(controllers)} Controller(s) Active")

        except Exception as e:
            logger.error(f"Error reading status file: {e}")

        return True

    def start_log_monitor(self):
        self.log_monitor_active = True
        def monitor():
            try:
                self.log_proc = subprocess.Popen(["journalctl", "-u", "pnp.service", "-f", "-n", "100"],
                                       stdout=subprocess.PIPE, text=True)
                for line in iter(self.log_proc.stdout.readline, ""):
                    if not self.log_monitor_active:
                        break
                    if line:
                        GLib.idle_add(self.append_log, line)
                if self.log_proc:
                    self.log_proc.terminate()
            except:
                pass
        threading.Thread(target=monitor, daemon=True).start()

    def append_log(self, text):
        if not text: return False
        # Deduplicate and summarize logs in the UI with a counter
        # Strip timestamp for comparison if it's in standard format
        # e.g. "2026-06-10 16:33:15 - "
        cmp_text = text
        if " - " in text:
            cmp_text = text.split(" - ", 1)[-1]

        if hasattr(self, '_last_log') and self._last_log == cmp_text:
            self._log_count += 1
            buffer = self.log_view.get_buffer()
            # Update the last line to include the count
            it_start = buffer.get_iter_at_line(buffer.get_line_count() - 1)
            # Handle PyGObject ResultTuple
            if not isinstance(it_start, Gtk.TextIter):
                it_start = it_start[1]
            it_end = buffer.get_end_iter()
            buffer.delete(it_start, it_end)
            buffer.insert_with_tags_by_name(buffer.get_end_iter(), f"{text.strip()} (x{self._log_count})\n", self._last_tag)
            return False

        self._last_log = cmp_text
        self._log_count = 1

        buffer = self.log_view.get_buffer()

        # Colorize and format
        tag_name = "normal"
        if "error" in text.lower() or "fail" in text.lower() or "critical" in text.lower():
            tag_name = "error"
        elif "warn" in text.lower():
            tag_name = "warn"
        elif "info" in text.lower():
            tag_name = "info"
        elif "debug" in text.lower():
            tag_name = "debug"

        self._last_tag = tag_name

        # Apply tags if not already created
        if not buffer.get_tag_table().lookup("error"):
            buffer.create_tag("error", foreground="#ff5555", weight=700)
            buffer.create_tag("warn", foreground="#f1fa8c")
            buffer.create_tag("info", foreground="#8be9fd")
            buffer.create_tag("debug", foreground="#6272a4")
            buffer.create_tag("normal", foreground="#f8f8f2")

        buffer.insert_with_tags_by_name(buffer.get_end_iter(), text, tag_name)

        # Scroll to bottom
        GLib.idle_add(lambda: self.log_view.scroll_to_mark(buffer.get_insert(), 0.0, True, 0.0, 1.0))

        if buffer.get_line_count() > 500:
            start_iter = buffer.get_iter_at_line(0)
            if not isinstance(start_iter, Gtk.TextIter): start_iter = start_iter[1]
            end_iter = buffer.get_iter_at_line(20)
            if not isinstance(end_iter, Gtk.TextIter): end_iter = end_iter[1]
            buffer.delete(start_iter, end_iter)

        return False

    def setup_css(self):
        if not hasattr(self, '_css_loaded'):
            provider = Gtk.CssProvider()
            provider.load_from_data(b"""
                .controller-btn {
                    border-radius: 50%;
                    background: alpha(@theme_fg_color, 0.1);
                    border: 1px solid alpha(@theme_fg_color, 0.2);
                    font-size: 10px;
                    font-weight: bold;
                }
                .controller-btn.success {
                    background: @success_bg_color;
                    color: @success_fg_color;
                }
            """)
            Gtk.StyleContext.add_provider_for_display(
                Gdk.Display.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
            self._css_loaded = True


class Application(Adw.Application):
    def __init__(self):
        # Use NON_UNIQUE flag to completely avoid registration timeouts and DBus locks.
        # This allows the GUI to always start immediately as a shell.
        super().__init__(application_id=None, flags=Gio.ApplicationFlags.NON_UNIQUE)
        self.indicator = None
        self.steam_check_enabled = True

    def setup_indicator(self):
        try:
            self.indicator = StatusNotifierItem(
                self,
                "pnp",
                "PNP Controller Mapper",
                "input-gaming-symbolic"
            )
            logger.info("GTK4-compatible System Tray (SNI) initialized via DBus.")
        except Exception as e:
            logger.error(f"Failed to initialize System Tray: {e}")

    def on_show_activate(self, _):
        win = self.get_active_window()
        if win:
            win.present()

    def on_quit_activate(self, _):
        self.quit()

    def on_toggle_steam_check(self, _):
        self.steam_check_enabled = not self.steam_check_enabled
        if self.indicator:
            self.indicator.update_menu()
        win = self.get_active_window()
        if win:
            win.steam_switch.set_active(self.steam_check_enabled)
            win.show_toast(f"Steam check {'enabled' if self.steam_check_enabled else 'disabled'}")

    def do_startup(self):
        Adw.Application.do_startup(self)
        # Initialize the tray in startup, but safely
        GLib.idle_add(self.setup_indicator)

    def do_activate(self):
        try:
            win = self.get_active_window()
            if not win:
                win = MainWindow(application=self)

            win.present()
        except Exception as e:
            logger.critical(f"Failed to activate application: {e}", exc_info=True)
            # Show a fallback error dialog if possible
            dialog = Gtk.MessageDialog(
                transient_for=None,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Critical Error",
                secondary_text=f"Failed to start the application: {e}"
            )
            dialog.connect("response", lambda d, r: d.destroy())
            dialog.show()
