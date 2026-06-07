#!/usr/bin/env python3
import sys
import os
import json
import subprocess
import configparser
import threading
import time
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio

CONFIG_PATH = "/etc/ds4to360.conf"
STATUS_FILE = "/run/ds4to360/status.json"

class MainWindow(Adw.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.set_title("DS4 to Xbox 360")
        self.set_default_size(900, 700)

        # Main Layout using ToolbarView
        self.toolbar_view = Adw.ToolbarView()
        self.set_content(self.toolbar_view)

        # Header Bar
        self.header = Adw.HeaderBar()
        self.toolbar_view.add_top_bar(self.header)

        # View Switcher in Header
        self.view_stack = Adw.ViewStack()
        self.view_switcher_title = Adw.ViewSwitcherTitle()
        self.view_switcher_title.set_stack(self.view_stack)
        self.view_switcher_title.set_title("DS4 to Xbox 360")
        self.header.set_title_widget(self.view_switcher_title)

        # About button
        menu_button = Gtk.MenuButton()
        menu_button.set_icon_name("help-about-symbolic")
        self.header.pack_end(menu_button)

        # Toast Overlay
        self.toast_overlay = Adw.ToastOverlay()
        self.toast_overlay.set_child(self.view_stack)
        self.toolbar_view.set_content(self.toast_overlay)

        self.setup_status_page()
        self.setup_settings_page()
        self.setup_tester_page()
        self.setup_logs_page()

        # Bottom View Switcher Bar (visible on narrow windows)
        self.view_switcher_bar = Adw.ViewSwitcherBar()
        self.view_switcher_bar.set_stack(self.view_stack)
        self.toolbar_view.add_bottom_bar(self.view_switcher_bar)

        self.load_config()
        GLib.timeout_add(1000, self.update_status)
        self.update_status()
        self.start_log_monitor()

    def setup_status_page(self):
        page_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        self.status_page = Adw.StatusPage(
            title="Waiting for Controller",
            description="Connect your Sony controller (DS3, DS4, or DualSense) via Bluetooth or USB.",
            icon_name="input-gaming-symbolic"
        )
        page_box.append(self.status_page)

        clamp = Adw.Clamp()
        clamp.set_maximum_size(600)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        clamp.set_child(box)
        page_box.append(clamp)

        # Connected Controllers Group
        self.controllers_group = Adw.PreferencesGroup(title="Active Mappings")
        self.no_controllers_row = Adw.ActionRow(title="No controllers detected")
        self.controllers_group.add(self.no_controllers_row)
        box.append(self.controllers_group)

        # Service Management Group
        service_group = Adw.PreferencesGroup(title="System Service")
        box.append(service_group)

        self.service_switch = Gtk.Switch()
        self.service_switch.set_valign(Gtk.Align.CENTER)
        self.service_switch.connect("state-set", self.on_service_switch_toggle)

        self.service_row = Adw.ActionRow(title="Emulation Service", subtitle="Runs in background and handles controller translation")
        self.service_row.add_suffix(self.service_switch)
        service_group.add(self.service_row)

        restart_btn = Gtk.Button(icon_name="view-refresh-symbolic")
        restart_btn.set_valign(Gtk.Align.CENTER)
        restart_btn.set_tooltip_text("Restart Service")
        restart_btn.add_css_class("flat")
        restart_btn.connect("clicked", self.on_restart_clicked)
        self.service_row.add_suffix(restart_btn)

        page_box.set_margin_bottom(40)
        scroll = Gtk.ScrolledWindow()
        scroll.set_child(page_box)

        self.view_stack.add_titled_with_icon(scroll, "status", "Status", "dialog-information-symbolic")

    def setup_settings_page(self):
        settings_page = Adw.PreferencesPage()

        # General Group
        gen_group = Adw.PreferencesGroup(title="General Settings")
        settings_page.add(gen_group)

        self.rumble_entry = Gtk.Entry()
        self.rumble_entry.set_valign(Gtk.Align.CENTER)
        rumble_row = Adw.ActionRow(title="Rumble Gain", subtitle="Global force feedback strength")
        rumble_row.add_suffix(self.rumble_entry)
        gen_group.add(rumble_row)

        self.steam_switch = Gtk.Switch()
        self.steam_switch.set_valign(Gtk.Align.CENTER)
        steam_row = Adw.ActionRow(title="Steam Conflict Prevention", subtitle="Automatically pause emulation when Steam is running")
        steam_row.add_suffix(self.steam_switch)
        gen_group.add(steam_row)

        # Mapping Group
        map_group = Adw.PreferencesGroup(title="Xboxdrv Mappings", description="Customize how buttons and axes are translated")
        settings_page.add(map_group)

        self.axismap_entry = Gtk.Entry()
        self.absmap_entry = Gtk.Entry()
        self.keymap_entry = Gtk.Entry()

        for title, entry, desc in [
            ("Axis Map", self.axismap_entry, "Mapping for analog sticks"),
            ("Absolute Map", self.absmap_entry, "Mapping for triggers and d-pad"),
            ("Key Map", self.keymap_entry, "Mapping for face buttons and others")
        ]:
            row = Adw.ActionRow(title=title, subtitle=desc)
            entry.set_valign(Gtk.Align.CENTER)
            entry.set_hexpand(True)
            row.add_suffix(entry)
            map_group.add(row)

        # Footer Actions
        footer_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        footer_box.set_margin_top(32)
        footer_box.set_margin_bottom(32)

        save_btn = Gtk.Button(label="Save & Apply Settings")
        save_btn.add_css_class("suggested-action")
        save_btn.add_css_class("pill")
        save_btn.set_halign(Gtk.Align.CENTER)
        save_btn.set_size_request(250, -1)
        save_btn.connect("clicked", self.on_save_clicked)
        footer_box.append(save_btn)

        settings_page.set_child(footer_box)

        # Actually Libadwaita PreferencesPage uses a different way to append non-group widgets
        # but let's stick to groups for better look
        footer_group = Adw.PreferencesGroup()
        footer_group.add(save_btn)
        settings_page.add(footer_group)

        self.view_stack.add_titled_with_icon(settings_page, "settings", "Settings", "emblem-system-symbolic")

    def setup_tester_page(self):
        page = Adw.StatusPage(title="Controller Tester", description="Verify inputs from the virtual Xbox 360 controller.", icon_name="input-gaming-symbolic")

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        box.set_margin_all(24)

        self.tester_label = Gtk.Label(label="Emulation is currently inactive.")
        self.tester_label.add_css_class("title-2")
        box.append(self.tester_label)

        info_label = Gtk.Label(label="Your system should now see one or more 'Xbox 360 Wireless Receiver' devices.")
        info_label.add_css_class("dim-label")
        box.append(info_label)

        # Grid for buttons (visual feedback placeholder)
        self.tester_grid = Gtk.Grid()
        self.tester_grid.set_column_spacing(12)
        self.tester_grid.set_row_spacing(12)
        self.tester_grid.set_halign(Gtk.Align.CENTER)
        # In a real app, we'd use python-evdev to read the virtual device and update these
        box.append(self.tester_grid)

        page.set_child(box)
        self.view_stack.add_titled_with_icon(page, "tester", "Tester", "preferences-desktop-peripherals-symbolic")

    def setup_logs_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        # Toolbar for logs
        log_tools = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        log_tools.set_margin_all(6)

        clear_btn = Gtk.Button(label="Clear Logs")
        clear_btn.connect("clicked", lambda _: self.log_view.get_buffer().set_text(""))
        log_tools.append(clear_btn)

        box.append(log_tools)

        self.log_view = Gtk.TextView()
        self.log_view.set_editable(False)
        self.log_view.set_monospace(True)
        self.log_view.set_margin_all(12)
        self.log_view.add_css_class("card")

        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.set_child(self.log_view)
        box.append(scroll)

        self.view_stack.add_titled_with_icon(box, "logs", "Logs", "view-list-bullet-symbolic")

    def show_toast(self, message):
        self.toast_overlay.add_toast(Adw.Toast(title=message))

    def load_config(self):
        config = configparser.ConfigParser()
        if os.path.exists(CONFIG_PATH):
            config.read(CONFIG_PATH)

        self.rumble_entry.set_text(config.get('settings', 'rumble_gain', fallback='15%'))
        self.steam_switch.set_active(config.getboolean('settings', 'steam_conflict_check', fallback=True))
        self.axismap_entry.set_text(config.get('mapping', 'axismap', fallback='-y1=y1,-y2=y2'))
        self.absmap_entry.set_text(config.get('mapping', 'absmap', fallback='ABS_HAT0X=dpad_x,ABS_HAT0Y=dpad_y,ABS_X=X1,ABS_Y=Y1,ABS_RX=X2,ABS_RY=Y2,ABS_Z=LT,ABS_RZ=RT'))
        self.keymap_entry.set_text(config.get('mapping', 'keymap', fallback='BTN_SOUTH=A,BTN_EAST=B,BTN_NORTH=Y,BTN_WEST=X,BTN_START=start,BTN_MODE=guide,BTN_SELECT=back,BTN_TL=LB,BTN_TR=RB,BTN_TL2=LT,BTN_TR2=RT,BTN_THUMBL=TL,BTN_THUMBR=TR'))

    def update_status(self):
        # Service status
        try:
            res = subprocess.run(["systemctl", "is-active", "ds4-xboxdrv.service"], capture_output=True, text=True)
            is_active = res.stdout.strip() == "active"
            if self.service_switch.get_active() != is_active:
                self.service_switch.set_state(is_active)
        except: is_active = False

        # Backend status
        if os.path.exists(STATUS_FILE):
            try:
                with open(STATUS_FILE, "r") as f:
                    data = json.load(f)

                    # Update controllers list
                    while (row := self.controllers_group.get_first_child()):
                        self.controllers_group.remove(row)

                    active_controllers = data.get("controllers", [])
                    if not active_controllers:
                        self.controllers_group.add(Adw.ActionRow(title="No controllers mapped", subtitle="Connect a controller or check logs"))
                    else:
                        for name in active_controllers:
                            row = Adw.ActionRow(title=name, subtitle="Connected & Mapped")
                            row.add_prefix(Gtk.Image.new_from_icon_name("input-gaming-symbolic"))
                            badge = Gtk.Label(label="Active")
                            badge.add_css_class("success")
                            badge.add_css_class("pill")
                            row.add_suffix(badge)
                            self.controllers_group.add(row)

                    if data.get("active"):
                        self.status_page.set_title(f"{len(active_controllers)} Controller(s) Ready")
                        self.status_page.set_description("Emulation is active. You can now play games using your Sony controller.")
                        self.status_page.set_icon_name("input-gaming-symbolic")
                        self.tester_label.set_label("Virtual Xbox 360 Controller Active")
                    elif data.get("steam_blocking"):
                        self.status_page.set_title("Paused (Steam Conflict)")
                        self.status_page.set_description("Emulation is temporarily paused because Steam is running.")
                        self.status_page.set_icon_name("dialog-warning-symbolic")
                        self.tester_label.set_label("Inactive (Steam Conflict)")
                    else:
                        self.status_page.set_title("Waiting for Controller")
                        self.status_page.set_description("Service is running but no supported controllers were found.")
                        self.status_page.set_icon_name("input-gaming-symbolic")
                        self.tester_label.set_label("Idle (No controller)")
            except: pass
        else:
            if not is_active:
                self.status_page.set_title("Service is Offline")
                self.status_page.set_description("Please start the emulation service to begin.")
                self.status_page.set_icon_name("prohibit-symbolic")
            else:
                self.status_page.set_title("Initializing...")
                self.status_page.set_description("The backend is starting up...")

        return True

    def on_save_clicked(self, button):
        config = configparser.ConfigParser()
        if os.path.exists(CONFIG_PATH): config.read(CONFIG_PATH)

        if 'settings' not in config: config['settings'] = {}
        if 'mapping' not in config: config['mapping'] = {}

        config['settings']['rumble_gain'] = self.rumble_entry.get_text()
        config['settings']['steam_conflict_check'] = 'true' if self.steam_switch.get_active() else 'false'
        config['mapping']['axismap'] = self.axismap_entry.get_text()
        config['mapping']['absmap'] = self.absmap_entry.get_text()
        config['mapping']['keymap'] = self.keymap_entry.get_text()

        tmp_path = f"/tmp/ds4to360-{os.getuid()}.conf"
        try:
            with open(tmp_path, "w") as f:
                config.write(f)
            subprocess.run(["pkexec", "mv", tmp_path, CONFIG_PATH], check=True)
            self.show_toast("Configuration saved successfully")
            self.on_restart_clicked(None)
        except Exception as e:
            self.show_toast(f"Error saving config: {e}")

    def on_service_switch_toggle(self, switch, state):
        res = subprocess.run(["systemctl", "is-active", "ds4-xboxdrv.service"], capture_output=True, text=True)
        current = res.stdout.strip() == "active"
        if current == state: return False

        cmd = "start" if state else "stop"
        try:
            subprocess.run(["pkexec", "systemctl", cmd, "ds4-xboxdrv.service"], check=True)
            self.show_toast(f"Emulation service {cmd}ed")
        except:
            switch.set_active(current)
        return False

    def on_restart_clicked(self, button):
        try:
            subprocess.run(["pkexec", "systemctl", "restart", "ds4-xboxdrv.service"], check=True)
            self.show_toast("Service restarted")
        except: pass

    def start_log_monitor(self):
        def monitor():
            try:
                proc = subprocess.Popen(["journalctl", "-u", "ds4-xboxdrv.service", "-f", "-n", "100"],
                                       stdout=subprocess.PIPE, text=True)
                for line in iter(proc.stdout.readline, ""):
                    GLib.idle_add(self.append_log, line)
            except: pass
        threading.Thread(target=monitor, daemon=True).start()

    def append_log(self, text):
        buffer = self.log_view.get_buffer()
        buffer.insert(buffer.get_end_iter(), text)
        if buffer.get_line_count() > 1000:
            buffer.delete(buffer.get_iter_at_line(0), buffer.get_iter_at_line(50))

        adj = self.log_view.get_vadjustment()
        adj.set_value(adj.get_upper() - adj.get_page_size())
        return False

class Application(Adw.Application):
    def __init__(self):
        super().__init__(application_id="io.github.ds4to360.gui", flags=Gio.ApplicationFlags.FLAGS_NONE)

    def do_activate(self):
        MainWindow(application=self).present()

def main():
    app = Application()
    return app.run(sys.argv)

if __name__ == "__main__":
    main()
