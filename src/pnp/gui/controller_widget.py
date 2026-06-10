from gi.repository import Gtk, Adw, GObject, GLib

class ControllerWidget(Adw.ActionRow):
    def __init__(self, controller):
        super().__init__(title=controller.name, subtitle=f"Path: {controller.device_path} | Serial: {controller.serial}")
        self.controller = controller

        self.status_icon = Gtk.Image.new_from_icon_name("emblem-system-symbolic")
        self.add_prefix(self.status_icon)

        # Battery info
        self.battery_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.battery_icon = Gtk.Image()
        self.battery_label = Gtk.Label()
        self.battery_label.add_css_class("caption")
        self.battery_box.append(self.battery_icon)
        self.battery_box.append(self.battery_label)
        self.add_suffix(self.battery_box)

        self.switch = Gtk.Switch()
        self.switch.set_valign(Gtk.Align.CENTER)
        self.switch.set_active(controller.is_active)
        self.switch.connect('notify::active', self._on_switch_activated)

        self.add_suffix(self.switch)

        self.handler_ids = {
            'status-changed': self.controller.connect('status-changed', self._on_status_changed),
            'battery-changed': self.controller.connect('battery-changed', self._on_battery_changed),
        }

        self.connect("destroy", self._on_destroy)

        self._update_ui(controller.is_active)
        self._on_battery_changed(controller, controller.battery_percentage, controller.battery_status)

    def _on_battery_changed(self, controller, percentage, status):
        GLib.idle_add(self._on_battery_changed_idle, percentage, status)

    def _on_battery_changed_idle(self, percentage, status):
        if percentage < 0:
            self.battery_box.set_visible(False)
            return False

        self.battery_box.set_visible(True)
        self.battery_label.set_text(f"{percentage}%")

        icon_name = "battery-missing-symbolic"
        if status == "Charging":
            if percentage < 20: icon_name = "battery-caution-charging-symbolic"
            elif percentage < 40: icon_name = "battery-low-charging-symbolic"
            elif percentage < 60: icon_name = "battery-good-charging-symbolic"
            elif percentage < 80: icon_name = "battery-full-charging-symbolic"
            else: icon_name = "battery-full-charged-symbolic"
        else:
            if percentage < 10: icon_name = "battery-empty-symbolic"
            elif percentage < 30: icon_name = "battery-caution-symbolic"
            elif percentage < 50: icon_name = "battery-low-symbolic"
            elif percentage < 80: icon_name = "battery-good-symbolic"
            else: icon_name = "battery-full-symbolic"

        self.battery_icon.set_from_icon_name(icon_name)
        self.set_tooltip_text(f"Battery: {percentage}% ({status})")
        return False

    def _on_switch_activated(self, switch, gparam):
        if switch.get_active():
            self.controller.start()
        else:
            self.controller.stop()

    def _on_status_changed(self, controller, active):
        GLib.idle_add(self._on_status_changed_idle, active)

    def _on_status_changed_idle(self, active):
        self.switch.set_active(active)
        self._update_ui(active)
        return False

    def _update_ui(self, active):
        if active:
            self.status_icon.set_from_icon_name("emblem-ok-symbolic")
            self.status_icon.add_css_class("success")
        else:
            self.status_icon.set_from_icon_name("emblem-important-symbolic")
            self.status_icon.remove_css_class("success")

    def _on_destroy(self, widget):
        # Disconnect signals to allow garbage collection
        for signal_name, handler_id in self.handler_ids.items():
            if self.controller.handler_is_connected(handler_id):
                self.controller.disconnect(handler_id)
        self.handler_ids.clear()
