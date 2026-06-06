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
        self.set_default_size(700, 500)

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(self.main_box)

        self.header = Adw.HeaderBar()
        self.main_box.append(self.header)

        self.toast_overlay = Adw.ToastOverlay()
        self.main_box.append(self.toast_overlay)

        self.view_stack = Adw.ViewStack()

        # Main View
        main_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        main_page.set_margin_all(24)

        clamp = Adw.Clamp()
        clamp.set_child(main_page)
        self.view_stack.add_titled(clamp, "main", "Status")

        # Status Group
        status_group = Adw.PreferencesGroup(title="Status")
        main_page.append(status_group)

        self.status_row = Adw.ActionRow(title="Controller Status", subtitle="Unknown")
        self.status_icon = Gtk.Image.new_from_icon_name("view-refresh-symbolic")
        self.status_row.add_prefix(self.status_icon)
        status_group.add(self.status_row)

        self.service_switch = Gtk.Switch()
        self.service_switch.set_valign(Gtk.Align.CENTER)
        self.service_switch.connect("state-set", self.on_service_switch_toggle)
        self.service_row = Adw.ActionRow(title="Emulation Service", subtitle="Manage systemd service")
        self.service_row.add_suffix(self.service_switch)
        status_group.add(self.service_row)

        self.restart_button = Gtk.Button(label="Restart Service")
        self.restart_button.set_valign(Gtk.Align.CENTER)
        self.restart_button.connect("clicked", self.on_restart_clicked)
        self.service_row.add_suffix(self.restart_button)

        # Settings View
        settings_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        settings_page.set_margin_all(24)

        settings_clamp = Adw.Clamp()
        settings_clamp.set_child(settings_page)
        self.view_stack.add_titled(settings_clamp, "settings", "Configuration")

        config_group = Adw.PreferencesGroup(title="General Settings")
        settings_page.append(config_group)

        self.rumble_row = Adw.ActionRow(title="Rumble Gain", subtitle="Strength of force feedback (e.g., 15%)")
        self.rumble_entry = Gtk.Entry()
        self.rumble_entry.set_valign(Gtk.Align.CENTER)
        self.rumble_row.add_suffix(self.rumble_entry)
        config_group.add(self.rumble_row)

        self.steam_row = Adw.ActionRow(title="Steam Conflict Check", subtitle="Disable mapping when Steam is running")
        self.steam_switch = Gtk.Switch()
        self.steam_switch.set_valign(Gtk.Align.CENTER)
        self.steam_row.add_suffix(self.steam_switch)
        config_group.add(self.steam_row)

        mapping_group = Adw.PreferencesGroup(title="Input Mapping")
        settings_page.append(mapping_group)

        self.axismap_entry = Gtk.Entry()
        self.axismap_row = Adw.ActionRow(title="Axis Map")
        self.axismap_row.add_suffix(self.axismap_entry)
        mapping_group.add(self.axismap_row)

        self.absmap_entry = Gtk.Entry()
        self.absmap_row = Adw.ActionRow(title="Absolute Map")
        self.absmap_row.add_suffix(self.absmap_entry)
        mapping_group.add(self.absmap_row)

        self.keymap_entry = Gtk.Entry()
        self.keymap_row = Adw.ActionRow(title="Key Map")
        self.keymap_row.add_suffix(self.keymap_entry)
        mapping_group.add(self.keymap_row)

        self.save_button = Gtk.Button(label="Save Settings")
        self.save_button.add_css_class("suggested-action")
        self.save_button.connect("clicked", self.on_save_clicked)
        settings_page.append(self.save_button)

        # Logs View
        logs_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        logs_page.set_margin_all(12)
        self.view_stack.add_titled(logs_page, "logs", "Logs")

        self.log_view = Gtk.TextView()
        self.log_view.set_editable(False)
        self.log_view.set_cursor_visible(False)
        self.log_view.set_monospace(True)
        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.set_child(self.log_view)
        logs_page.append(scroll)

        self.view_switcher = Adw.ViewSwitcher()
        self.view_switcher.set_stack(self.view_stack)
        self.header.set_title_widget(self.view_switcher)
        self.toast_overlay.set_child(self.view_stack)

        # Start monitoring
        self.load_config()
        GLib.timeout_add(2000, self.update_status)
        self.update_status()
        self.start_log_monitor()

    def show_toast(self, message):
        toast = Adw.Toast(title=message)
        self.toast_overlay.add_toast(toast)

    def load_config(self):
        config = configparser.ConfigParser()
        if os.path.exists(CONFIG_PATH):
            config.read(CONFIG_PATH)

        self.rumble_entry.set_text(config.get('settings', 'rumble_gain', fallback='15%'))
        self.steam_switch.set_active(config.getboolean('settings', 'steam_conflict_check', fallback=True))
        self.axismap_entry.set_text(config.get('mapping', 'axismap', fallback='-y1=y1,-y2=y2'))
        self.absmap_entry.set_text(config.get('mapping', 'absmap', fallback='ABS_HAT0X=dpad_x,ABS_HAT0Y=dpad_y,ABS_X=X1,ABS_Y=Y1,ABS_RX=X2,ABS_RY=Y2,ABS_Z=LT,ABS_RZ=RT'))
        self.keymap_entry.set_text(config.get('mapping', 'keymap', fallback='BTN_SOUTH=A,BTN_EAST=B,BTN_NORTH=Y,BTN_WEST=X,BTN_START=start,BTN_MODE=guide,BTN_SELECT=back,BTN_TL=LB,BTN_TR=RB,BTN_TL2=LT,BTN_TR2=RT,BTN_THUMBL=TL,BTN_THUMBR=TR'))

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

        tmp_path = "/tmp/ds4to360.conf"
        try:
            with open(tmp_path, "w") as f:
                config.write(f)
            # Use pkexec for safe privilege escalation
            subprocess.run(["pkexec", "mv", tmp_path, CONFIG_PATH], check=True)
            self.show_toast("Settings saved successfully")
        except Exception as e:
            self.show_toast(f"Error saving settings: {e}")

    def update_status(self):
        try:
            res = subprocess.run(["systemctl", "is-active", "ds4-xboxdrv.service"], capture_output=True, text=True)
            is_active = res.stdout.strip() == "active"
            # Prevent feedback loop by only setting if changed
            if self.service_switch.get_active() != is_active:
                self.service_switch.set_active(is_active)
        except:
            is_active = False

        if os.path.exists(STATUS_FILE):
            try:
                with open(STATUS_FILE, "r") as f:
                    data = json.load(f)
                    if data.get("active"):
                        self.status_row.set_subtitle(f"Active: {data.get('device')}")
                        self.status_icon.set_from_icon_name("input-gaming-symbolic")
                    elif data.get("steam_blocking"):
                        self.status_row.set_subtitle("Blocked by Steam")
                        self.status_icon.set_from_icon_name("dialog-warning-symbolic")
                    else:
                        self.status_row.set_subtitle("Idle (Waiting for controller)")
                        self.status_icon.set_from_icon_name("prohibit-symbolic")
            except:
                self.status_row.set_subtitle("Service Running")
        else:
            self.status_row.set_subtitle("Service Running" if is_active else "Service Stopped")
            self.status_icon.set_from_icon_name("prohibit-symbolic")

        return True

    def on_service_switch_toggle(self, switch, state):
        # We check current state to avoid redundant calls
        res = subprocess.run(["systemctl", "is-active", "ds4-xboxdrv.service"], capture_output=True, text=True)
        current_state = res.stdout.strip() == "active"
        if current_state == state: return False

        cmd = "start" if state else "stop"
        try:
            subprocess.run(["pkexec", "systemctl", cmd, "ds4-xboxdrv.service"], check=True)
            self.show_toast(f"Service {cmd}ed")
        except:
            # Revert switch if failed
            switch.set_active(current_state)
        return False

    def on_restart_clicked(self, button):
        try:
            subprocess.run(["pkexec", "systemctl", "restart", "ds4-xboxdrv.service"], check=True)
            self.show_toast("Service restarted")
        except Exception as e:
            self.show_toast(f"Failed to restart: {e}")

    def start_log_monitor(self):
        def monitor():
            try:
                proc = subprocess.Popen(["journalctl", "-u", "ds4-xboxdrv.service", "-f", "-n", "50"],
                                       stdout=subprocess.PIPE, text=True)
                for line in iter(proc.stdout.readline, ""):
                    GLib.idle_add(self.append_log, line)
            except:
                pass
        threading.Thread(target=monitor, daemon=True).start()

    def append_log(self, text):
        buffer = self.log_view.get_buffer()
        buffer.insert(buffer.get_end_iter(), text)
        if buffer.get_line_count() > 1000:
            start = buffer.get_iter_at_line(0)
            end = buffer.get_iter_at_line(100)
            buffer.delete(start, end)

        # Scroll to bottom
        adj = self.log_view.get_vadjustment()
        adj.set_value(adj.get_upper() - adj.get_page_size())
        return False

class Application(Adw.Application):
    def __init__(self):
        super().__init__(application_id="io.github.ds4to360.gui", flags=Gio.ApplicationFlags.FLAGS_NONE)

    def do_activate(self):
        MainWindow(application=self).present()

if __name__ == "__main__":
    Application().run(sys.argv)
