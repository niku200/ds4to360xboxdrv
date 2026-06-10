import os
import logging
from gi.repository import Gtk, GLib, Gio

logger = logging.getLogger(__name__)

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
  <interface name="com.canonical.dbusmenu">
    <method name="GetLayout">
      <arg name="parentId" type="i" direction="in"/>
      <arg name="recursionDepth" type="i" direction="in"/>
      <arg name="propertyNames" type="as" direction="in"/>
      <arg name="revision" type="u" direction="out"/>
      <arg name="layout" type="(ia{sv}av)" direction="out"/>
    </method>
    <method name="GetGroupProperties">
      <arg name="ids" type="ai" direction="in"/>
      <arg name="propertyNames" type="as" direction="in"/>
      <arg name="properties" type="a(ia{sv})" direction="out"/>
    </method>
    <method name="GetProperty">
      <arg name="id" type="i" direction="in"/>
      <arg name="name" type="s" direction="in"/>
      <arg name="value" type="v" direction="out"/>
    </method>
    <method name="Event">
      <arg name="id" type="i" direction="in"/>
      <arg name="eventId" type="s" direction="in"/>
      <arg name="data" type="v" direction="in"/>
      <arg name="timestamp" type="u" direction="in"/>
    </method>
    <signal name="LayoutUpdated">
      <arg name="revision" type="u"/>
      <arg name="parentId" type="i"/>
    </signal>
  </interface>
</node>
"""

class StatusNotifierItem:
    def __init__(self, app, id: str, title: str, icon_name: str):
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
            Gio.BusNameOwnerFlags.ALLOW_REPLACEMENT | Gio.BusNameOwnerFlags.REPLACE,
            self.on_bus_acquired,
            self._on_name_acquired,
            self._on_name_lost
        )

    def _on_name_acquired(self, conn, name):
        logger.debug(f"SNI name acquired: {name}")

    def _on_name_lost(self, conn, name):
        logger.debug(f"SNI name lost: {name}")

    def on_bus_acquired(self, connection, name):
        connection.register_object(
            "/StatusNotifierItem",
            self.interface_info,
            self.handle_method_call,
            self.handle_get_property,
            None
        )
        # Register DBusMenu
        connection.register_object(
            "/MenuBar",
            self.node_info.interfaces[1],
            self.handle_menu_method_call,
            None, None
        )
        self.register_with_watcher(connection)

    def handle_method_call(self, connection, sender, object_path, interface_name, method_name, parameters, invocation):
        if method_name == "Activate":
            GLib.idle_add(self.app.on_show_activate, None)
        elif method_name == "ContextMenu":
            # For some shells, ContextMenu method call should be handled.
            # We don't have a separate context menu object, but we can trigger
            # the DBusMenu refresh if needed.
            pass
        invocation.return_value(None)

    def handle_menu_method_call(self, connection, sender, object_path, interface_name, method_name, parameters, invocation):
        if method_name == "GetLayout":
            # (parentId: i, recursionDepth: i, propertyNames: as) -> (revision: u, layout: (ia{sv}av))
            steam_state = "Enabled" if getattr(self.app, 'steam_check_enabled', True) else "Disabled"
            revision = getattr(self, '_menu_revision', 1)

            # Build layout as (ia{sv}av)
            # The children MUST be GLib.Variant("av", [...])
            layout = (
                0, # root id
                {"children-display": GLib.Variant("s", "submenu")},
                [
                    GLib.Variant("v", GLib.Variant("(ia{sv}av)", (1, {"label": GLib.Variant("s", "Show PNP Interface")}, []))),
                    GLib.Variant("v", GLib.Variant("(ia{sv}av)", (2, {"label": GLib.Variant("s", f"Steam Pause: {steam_state}")}, []))),
                    GLib.Variant("v", GLib.Variant("(ia{sv}av)", (3, {"type": GLib.Variant("s", "separator")}, []))),
                    GLib.Variant("v", GLib.Variant("(ia{sv}av)", (4, {"label": GLib.Variant("s", "Exit Application")}, [])))
                ]
            )
            invocation.return_value(GLib.Variant("(u(ia{sv}av))", (revision, layout)))
        elif method_name == "GetGroupProperties":
            # (ids: ai, propertyNames: as) -> (properties: a(ia{sv}))
            ids, props = parameters
            res = []
            steam_state = "Enabled" if getattr(self.app, 'steam_check_enabled', True) else "Disabled"
            for id in ids:
                if id == 1:
                    res.append((1, {"label": GLib.Variant("s", "Show PNP Interface")}))
                elif id == 2:
                    res.append((2, {"label": GLib.Variant("s", f"Steam Pause: {steam_state}")}))
                elif id == 3:
                    res.append((3, {"type": GLib.Variant("s", "separator")}))
                elif id == 4:
                    res.append((4, {"label": GLib.Variant("s", "Exit Application")}))
            invocation.return_value(GLib.Variant("(a(ia{sv}))", [res]))
        elif method_name == "Event":
            id, event_id, data, timestamp = parameters
            if id == 1:
                GLib.idle_add(self.app.on_show_activate, None)
            elif id == 2:
                GLib.idle_add(self.app.on_toggle_steam_check, None)
            elif id == 4:
                GLib.idle_add(self.app.on_quit_activate, None)
            invocation.return_value(None)
        else:
            invocation.return_value(None)

    def handle_get_property(self, connection, sender, object_path, interface_name, property_name):
        props = {
            "Category": GLib.Variant("s", self.category),
            "Id": GLib.Variant("s", self.id),
            "Title": GLib.Variant("s", self.title),
            "Status": GLib.Variant("s", self.status),
            "IconName": GLib.Variant("s", self.icon_name),
            "ItemIsMenu": GLib.Variant("b", True),
            "Menu": GLib.Variant("o", "/MenuBar"),
        }
        return props.get(property_name)

    def update_menu(self):
        # Increment revision
        self._menu_revision = getattr(self, '_menu_revision', 1) + 1
        # Notify that layout has changed
        bus = Gio.BusType.SESSION
        Gio.bus_get(bus, None, self._on_bus_ready_for_signal)

    def _on_bus_ready_for_signal(self, _, res):
        try:
            conn = Gio.bus_get_finish(res)
            conn.emit_signal(
                None,
                "/MenuBar",
                "com.canonical.dbusmenu",
                "LayoutUpdated",
                GLib.Variant("(ui)", (self._menu_revision, 0))
            )
        except:
            pass

    def cleanup(self):
        if hasattr(self, 'bus_id'):
            Gio.bus_unown_name(self.bus_id)
            del self.bus_id

    def register_with_watcher(self, connection):
        def on_call_done(conn, res):
            try:
                conn.call_finish(res)
                logger.debug("SNI successfully registered with watcher.")
            except Exception as e:
                logger.debug(f"SNI registration failed (optional): {e}")

        # Register using the full service name AND the object path
        # Some watchers expect the full path or just the object path.
        # Standard SNI says it should be the object path, and it will use the sender's bus name.
        connection.call(
            "org.kde.StatusNotifierWatcher",
            "/StatusNotifierWatcher",
            "org.kde.StatusNotifierWatcher",
            "RegisterStatusNotifierItem",
            GLib.Variant("(s)", ["/StatusNotifierItem"]),
            None, Gio.DBusCallFlags.NONE, -1, None, on_call_done
        )
