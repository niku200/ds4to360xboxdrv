import sys
import subprocess
import threading
import json
import os
import configparser
import logging
from gi.repository import Gtk, Adw, GLib, Gio

# StatusNotifierItem (SNI) DBus implementation for GTK4 compatibility
# This avoids importing GTK3-based AyatanaAppIndicator3 which causes symbol conflicts.
SNI_INTERFACE = """
<node>
  <interface name="org.kde.StatusNotifierItem">
    <property name="Category" type="s" access="read"/>
    <property name="Id" type="s" access="read"/>
    <property name="Title" type="s" access="read"/>
    <property name="Status" type="s" access="read"/>
    <property name="IconName" type="s" access="read"/>
    <property name="SecondaryIconName" type="s" access="read"/>
    <property name="OverlayIconName" type="s" access="read"/>
    <property name="AttentionIconName" type="s" access="read"/>
    <property name="AttentionMovieName" type="s" access="read"/>
    <property name="ToolTip" type="(sa(iias)ss)" access="read"/>
    <property name="ItemIsMenu" type="b" access="read"/>
    <property name="Menu" type="o" access="read"/>
    <method name="ContextMenu">
      <arg name="x" type="i" direction="in"/>
      <arg name="y" type="i" direction="in"/>
    </method>
    <method name="Activate">
      <arg name="x" type="i" direction="in"/>
      <arg name="y" type="i" direction="in"/>
    </method>
    <method name="SecondaryActivate">
      <arg name="x" type="i" direction="in"/>
      <arg name="y" type="i" direction="in"/>
    </method>
    <method name="Scroll">
      <arg name="delta" type="i" direction="in"/>
      <arg name="orientation" type="s" direction="in"/>
    </method>
    <signal name="NewTitle"/>
    <signal name="NewIcon"/>
    <signal name="NewAttentionIcon"/>
    <signal name="NewOverlayIcon"/>
    <signal name="NewMenu"/>
    <signal name="NewStatus">
      <arg name="status" type="s"/>
    </signal>
    <signal name="NewToolTip"/>
  </interface>
</node>
"""

class StatusNotifierItem:
    def __init__(self, app, id, title, icon_name):
        self.app = app
        self.id = id
        self.title = title
        self.icon_name = icon_name
        self.status = "Active"
        self.category = "ApplicationStatus"

        self.node_info = Gio.DBusNodeInfo.new_for_xml(SNI_INTERFACE)
        self.interface_info = self.node_info.interfaces[0]

        self.bus_id = Gio.bus_own_name(
            Gio.BusType.SESSION,
            f"org.kde.StatusNotifierItem-{os.getpid()}-1",
            Gio.BusNameOwnerFlags.NONE,
            self.on_bus_acquired,
            None, None
        )

    def on_bus_acquired(self, connection, name):
        connection.register_object(
            "/StatusNotifierItem",
            self.interface_info,
            self.handle_method_call,
            self.handle_get_property,
            None
        )
        self.register_with_watcher(connection)

    def handle_method_call(self, connection, sender, object_path, interface_name, method_name, parameters, invocation):
        if method_name == "Activate":
            GLib.idle_add(self.app.on_show_activate, None)
        invocation.return_value(None)

    def handle_get_property(self, connection, sender, object_path, interface_name, property_name):
        props = {
            "Category": GLib.Variant("s", self.category),
            "Id": GLib.Variant("s", self.id),
            "Title": GLib.Variant("s", self.title),
            "Status": GLib.Variant("s", self.status),
            "IconName": GLib.Variant("s", self.icon_name),
            "ItemIsMenu": GLib.Variant("b", False),
            "Menu": GLib.Variant("o", "/MenuBar"),
        }
        return props.get(property_name)

    def register_with_watcher(self, connection):
        connection.call(
            "org.kde.StatusNotifierWatcher",
            "/StatusNotifierWatcher",
            "org.kde.StatusNotifierWatcher",
            "RegisterStatusNotifierItem",
            GLib.Variant("(s)", ["/StatusNotifierItem"]),
            None, Gio.DBusCallFlags.NONE, -1, None, None
        )

from pnp.gui.controller_widget import ControllerWidget

logger = logging.getLogger(__name__)

STATUS_FILE = "/run/pnp/status.json"
CONFIG_DIR = "/etc/pnp"
CONFIG_PATH = "/etc/pnp/pnp.conf"
LEGACY_CONFIG_PATH = "/etc/ds4to360.conf"

class MainWindow(Adw.ApplicationWindow):
    def __init__(self, manager, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.manager = manager
        self.is_observer = manager is None

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

        if not self.is_observer:
            self.manager.connect('controller-list-changed', self._on_controllers_changed)
            self._refresh_controllers()
        else:
            GLib.timeout_add(1000, self._update_observer_status)

        self.load_config()
        self.start_log_monitor()

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

        save_btn = Gtk.Button(label="Save & Apply", halign=Gtk.Align.CENTER, margin_top=24, css_classes=["suggested-action", "pill"])
        save_btn.set_size_request(200, -1)
        save_btn.connect("clicked", self.on_save_clicked)
        self.settings_page.add(save_btn)

        self.view_stack.add_titled_with_icon(self.settings_page, "settings", "Settings", "emblem-system-symbolic")

    def setup_tester_page(self):
        page = Adw.StatusPage(title="Tester", description="Verify inputs (Visualizer coming soon)", icon_name="input-gaming-symbolic")
        self.view_stack.add_titled_with_icon(page, "tester", "Tester", "preferences-desktop-peripherals-symbolic")

    def setup_logs_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
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

        self.connect("destroy", self._on_destroy)

    def _on_destroy(self, *args):
        self.log_monitor_active = False
        if hasattr(self, 'log_proc'):
            self.log_proc.terminate()
        if not self.is_observer:
            self.manager.stop_all()

    def load_config(self):
        config = configparser.ConfigParser(interpolation=None)
        if os.path.exists(CONFIG_PATH):
            config.read(CONFIG_PATH)
        elif os.path.exists(LEGACY_CONFIG_PATH):
            config.read(LEGACY_CONFIG_PATH)

        self.rumble_entry.set_text(config.get('settings', 'rumble_gain', fallback='15%'))
        self.steam_switch.set_active(config.getboolean('settings', 'steam_conflict_check', fallback=True))
        self.axismap_entry.set_text(config.get('mapping', 'axismap', fallback='-y1=y1,-y2=y2'))
        self.absmap_entry.set_text(config.get('mapping', 'absmap', fallback='ABS_X=x1,ABS_Y=y1,ABS_Z=x2,ABS_RZ=y2,ABS_HAT0X=dpad_x,ABS_HAT0Y=dpad_y'))
        self.keymap_entry.set_text(config.get('mapping', 'keymap', fallback='BTN_SOUTH=a,BTN_EAST=b,BTN_NORTH=x,BTN_WEST=y,BTN_TL=lb,BTN_TR=rb,BTN_THUMBL=tl,BTN_THUMBR=tr,BTN_SELECT=back,BTN_START=start,BTN_MODE=guide'))

    def on_save_clicked(self, button):
        config = configparser.ConfigParser(interpolation=None)
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

        tmp_path = f"/tmp/pnp-{os.getuid()}.conf"
        try:
            with open(tmp_path, "w") as f:
                config.write(f)
            # Combine multiple operations into one pkexec call
            cmd = f"mkdir -p {CONFIG_DIR} && mv {tmp_path} {CONFIG_PATH} && chmod 644 {CONFIG_PATH}"
            subprocess.run(["pkexec", "sh", "-c", cmd], check=True)
            self.show_toast("Settings saved. Restart service to apply.")
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            self.show_toast(f"Error saving: {e}")

    def show_toast(self, message):
        self.toast_overlay.add_toast(Adw.Toast(title=message))

    def _on_controllers_changed(self, manager):
        GLib.idle_add(self._refresh_controllers)

    def _refresh_controllers(self):
        while (child := self.controllers_group.get_first_child()):
            self.controllers_group.remove(child)

        if not self.manager.controllers:
            self.controllers_group.add(Adw.ActionRow(title="No controllers detected"))
        else:
            for controller in self.manager.controllers.values():
                self.controllers_group.add(ControllerWidget(controller))

    def _update_observer_status(self):
        if not os.path.exists(STATUS_FILE):
            self.status_page.set_title("Service Initializing...")
            return True

        try:
            with open(STATUS_FILE, "r") as f:
                data = json.load(f)

            while (child := self.controllers_group.get_first_child()):
                self.controllers_group.remove(child)

            controllers = data.get("controllers", [])
            if not controllers:
                self.controllers_group.add(Adw.ActionRow(title="No controllers active in service"))
            else:
                for name in controllers:
                    row = Adw.ActionRow(title=name, subtitle="Managed by system service")
                    row.add_prefix(Gtk.Image.new_from_icon_name("input-gaming-symbolic"))
                    badge = Gtk.Label(label="Running")
                    badge.add_css_class("success")
                    badge.add_css_class("pill")
                    row.add_suffix(badge)
                    self.controllers_group.add(row)

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
                    GLib.idle_add(self.append_log, line)
            except: pass
        threading.Thread(target=monitor, daemon=True).start()

    def append_log(self, text):
        buffer = self.log_view.get_buffer()
        buffer.insert(buffer.get_end_iter(), text)
        if buffer.get_line_count() > 1000:
            buffer.delete(buffer.get_iter_at_line(0), buffer.get_iter_at_line(50))
        return False

class Application(Adw.Application):
    def __init__(self, manager):
        super().__init__(application_id="io.github.pakrohk.pnp", flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.manager = manager
        self.missing_deps = []
        self.indicator = None

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

    def do_activate(self):
        try:
            win = self.get_active_window()
            if not win:
                win = MainWindow(self.manager, application=self)
                self.setup_indicator()

            win.present()

            if self.missing_deps:
                msg = f"Missing system dependencies: {', '.join(self.missing_deps)}. Please install them for the application to function correctly."
                toast = Adw.Toast(title=msg)
                toast.set_timeout(10)
                win.toast_overlay.add_toast(toast)
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
