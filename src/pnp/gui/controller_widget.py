from gi.repository import Gtk, Adw, GObject

class ControllerWidget(Adw.ActionRow):
    def __init__(self, controller):
        super().__init__(title=controller.name, subtitle=f"Path: {controller.device_path} | Serial: {controller.serial}")
        self.controller = controller

        self.status_icon = Gtk.Image.new_from_icon_name("emblem-system-symbolic")
        self.add_prefix(self.status_icon)

        self.switch = Gtk.Switch()
        self.switch.set_valign(Gtk.Align.CENTER)
        self.switch.set_active(controller.is_active)
        self.switch.connect('notify::active', self._on_switch_activated)

        self.add_suffix(self.switch)

        self.controller.connect('status-changed', self._on_status_changed)
        self._update_ui(controller.is_active)

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
