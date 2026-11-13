#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LegacyOS App Grid Launcher (Aplicativos)
Interface em grade com barra lateral de categorias, busca instantânea e 0 MB em background.
"""

import os
import subprocess
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("Gio", "2.0")
gi.require_version("Pango", "1.0")
from gi.repository import Gtk, Gdk, Gio, Pango  # noqa: E402


CATEGORIES = [
    ("all", "Todos os Aplicativos", "view-app-grid-symbolic"),
    ("Network", "Internet", "applications-internet-symbolic"),
    ("Office", "Escritório", "applications-office-symbolic"),
    ("AudioVideo", "Multimídia", "applications-multimedia-symbolic"),
    ("Graphics", "Gráficos", "applications-graphics-symbolic"),
    ("Utility", "Acessórios", "applications-utilities-symbolic"),
    ("System", "Sistema", "applications-system-symbolic"),
]

PLACES = [
    ("Início", os.path.expanduser("~"), "user-home-symbolic"),
    ("Documentos", os.path.expanduser("~/Documentos"), "folder-documents-symbolic"),
    ("Downloads", os.path.expanduser("~/Downloads"), "folder-download-symbolic"),
]

CSS_STYLE = b"""
window#legacyos-apps-window {
    background-color: #111827;
    color: #F8FAFC;
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.10);
}

#apps-header {
    background-color: #0B1120;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    padding: 8px 14px;
}

#apps-sidebar {
    background-color: #0B1120;
    border-right: 1px solid rgba(255, 255, 255, 0.08);
    padding: 10px 8px;
}

.sidebar-section-label {
    color: #64748B;
    font-size: 8.5pt;
    font-weight: 700;
    margin: 8px 10px 4px 10px;
}

#apps-sidebar list,
#apps-sidebar row {
    background-color: transparent;
    color: #CBD5E1;
    border-radius: 8px;
    padding: 6px 10px;
    margin: 1px 0;
}

#apps-sidebar row:hover {
    background-color: #1E293B;
    color: #FFFFFF;
}

#apps-sidebar row:selected {
    background-color: #0284C7;
    color: #FFFFFF;
    font-weight: 600;
}

#apps-search {
    background-color: #1E293B;
    color: #F8FAFC;
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 8px;
    padding: 4px 10px;
    min-width: 220px;
}

#apps-search:focus {
    border-color: #0284C7;
}

flowboxchild {
    border-radius: 10px;
    padding: 8px 4px;
    margin: 2px;
    transition: background-color 120ms ease;
}

flowboxchild:hover {
    background-color: rgba(30, 41, 59, 0.85);
}

flowboxchild:selected {
    background-color: rgba(2, 132, 199, 0.35);
    border: 1px solid rgba(56, 189, 248, 0.55);
}

.app-title-label {
    color: #F1F5F9;
    font-size: 9.2pt;
    font-weight: 500;
    margin-top: 6px;
}

flowboxchild:selected .app-title-label {
    background-color: #0284C7;
    color: #FFFFFF;
    border-radius: 6px;
    padding: 1px 6px;
}
"""


def map_app_category(raw_categories):
    """Mapeia as categorias XDG de um .desktop para as seções principais do LegacyOS."""
    if not raw_categories:
        return "Utility"
    tokens = {c.strip() for c in raw_categories.split(";") if c.strip()}
    if tokens & {"Network", "WebBrowser", "Email", "Chat"}:
        return "Network"
    if tokens & {"Office", "WordProcessor", "Spreadsheet", "Presentation", "Publishing"}:
        return "Office"
    if tokens & {"AudioVideo", "Audio", "Video", "Player", "Recorder"}:
        return "AudioVideo"
    if tokens & {"Graphics", "2DGraphics", "3DGraphics", "Photography", "Viewer"}:
        return "Graphics"
    if tokens & {"System", "Settings", "PackageManager", "Monitor", "HardwareSettings"}:
        return "System"
    return "Utility"


class AppTile(Gtk.FlowBoxChild):
    """Representa um item de aplicativo na grade."""

    def __init__(self, app_info):
        super().__init__()
        self.app_info = app_info
        self.app_name = app_info.get_display_name() or app_info.get_name() or "Aplicativo"
        self.app_desc = app_info.get_description() or ""
        raw_cats = app_info.get_categories() if hasattr(app_info, "get_categories") else ""
        self.mapped_category = map_app_category(raw_cats)

        self.set_tooltip_text(f"{self.app_name}\n{self.app_desc}".strip())

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        box.set_size_request(104, 92)
        box.set_valign(Gtk.Align.START)

        gicon = app_info.get_icon()
        if gicon is not None:
            image = Gtk.Image.new_from_gicon(gicon, Gtk.IconSize.DIALOG)
        else:
            image = Gtk.Image.new_from_icon_name("application-x-executable", Gtk.IconSize.DIALOG)
        image.set_pixel_size(48)
        image.set_halign(Gtk.Align.CENTER)

        label = Gtk.Label(label=self.app_name)
        label.get_style_context().add_class("app-title-label")
        label.set_line_wrap(True)
        label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        label.set_lines(2)
        label.set_max_width_chars(14)
        label.set_ellipsize(Pango.EllipsizeMode.END)
        label.set_justify(Gtk.Justification.CENTER)
        label.set_halign(Gtk.Align.CENTER)

        box.pack_start(image, False, False, 0)
        box.pack_start(label, False, False, 0)
        self.add(box)


class LegacyAppsWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="Aplicativos")
        self.set_name("legacyos-apps-window")
        self.set_icon_name("legacyos-logo")
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_decorated(False)
        self.set_skip_taskbar_hint(False)

        self.active_category = "all"
        self.search_query = ""

        # Ajusta dimensões conforme resolução da tela (compatível com 1024x600)
        screen = self.get_screen()
        scr_w = screen.get_width() if screen else 1024
        scr_h = screen.get_height() if screen else 600
        win_w = min(840, scr_w - 60)
        win_h = min(480, scr_h - 96)
        self.set_default_size(win_w, win_h)

        # Aplica CSS escuro
        provider = Gtk.CssProvider()
        provider.load_from_data(CSS_STYLE)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        self.connect("key-press-event", self.on_key_press)

        root_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.add(root_box)

        # ------------------------------------------------------------------
        # 1. BARRA LATERAL ESQUERDA (CATEGORIAS E LOCAIS)
        # ------------------------------------------------------------------
        sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        sidebar.set_name("apps-sidebar")
        sidebar.set_size_request(185, -1)

        cat_header = Gtk.Label(label="CATEGORIAS")
        cat_header.set_xalign(0.0)
        cat_header.get_style_context().add_class("sidebar-section-label")
        sidebar.pack_start(cat_header, False, False, 0)

        self.cat_listbox = Gtk.ListBox()
        self.cat_listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        for cat_id, cat_label, icon_name in CATEGORIES:
            row = Gtk.ListBoxRow()
            row.cat_id = cat_id
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            ico = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.MENU)
            lbl = Gtk.Label(label=cat_label)
            lbl.set_xalign(0.0)
            hbox.pack_start(ico, False, False, 0)
            hbox.pack_start(lbl, True, True, 0)
            row.add(hbox)
            self.cat_listbox.add(row)

        self.cat_listbox.select_row(self.cat_listbox.get_row_at_index(0))
        self.cat_listbox.connect("row-selected", self.on_category_selected)
        sidebar.pack_start(self.cat_listbox, False, False, 0)

        places_header = Gtk.Label(label="LOCAIS")
        places_header.set_xalign(0.0)
        places_header.get_style_context().add_class("sidebar-section-label")
        sidebar.pack_start(places_header, False, False, 4)

        places_listbox = Gtk.ListBox()
        places_listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        for place_name, place_path, icon_name in PLACES:
            row = Gtk.ListBoxRow()
            row.place_path = place_path
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            ico = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.MENU)
            lbl = Gtk.Label(label=place_name)
            lbl.set_xalign(0.0)
            hbox.pack_start(ico, False, False, 0)
            hbox.pack_start(lbl, True, True, 0)
            row.add(hbox)
            places_listbox.add(row)

        places_listbox.connect("row-activated", self.on_place_activated)
        sidebar.pack_start(places_listbox, False, False, 0)

        root_box.pack_start(sidebar, False, False, 0)

        # ------------------------------------------------------------------
        # 2. ÁREA PRINCIPAL (CABEÇALHO + GRADE DE ÍCONES)
        # ------------------------------------------------------------------
        right_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        header.set_name("apps-header")

        self.header_title = Gtk.Label(label="Todos os Aplicativos")
        self.header_title.set_markup("<b>Todos os Aplicativos</b>")
        header.pack_start(self.header_title, False, False, 0)

        spacer = Gtk.Box()
        header.pack_start(spacer, True, True, 0)

        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_name("apps-search")
        self.search_entry.set_placeholder_text("Pesquisar aplicativos...")
        self.search_entry.connect("search-changed", self.on_search_changed)
        header.pack_start(self.search_entry, False, False, 0)

        close_btn = Gtk.Button.new_from_icon_name("window-close-symbolic", Gtk.IconSize.MENU)
        close_btn.set_relief(Gtk.ReliefStyle.NONE)
        close_btn.set_tooltip_text("Fechar (Esc)")
        close_btn.connect("clicked", lambda *_: Gtk.main_quit())
        header.pack_start(close_btn, False, False, 0)

        right_box.pack_start(header, False, False, 0)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self.flowbox = Gtk.FlowBox()
        self.flowbox.set_valign(Gtk.Align.START)
        self.flowbox.set_max_children_per_line(6)
        self.flowbox.set_min_children_per_line(3)
        self.flowbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.flowbox.set_activate_on_single_click(False)
        self.flowbox.set_row_spacing(8)
        self.flowbox.set_column_spacing(8)
        self.flowbox.set_margin_top(14)
        self.flowbox.set_margin_bottom(14)
        self.flowbox.set_margin_start(14)
        self.flowbox.set_margin_end(14)
        self.flowbox.set_filter_func(self.filter_tile)
        self.flowbox.connect("child-activated", self.on_tile_activated)

        self.populate_apps()
        scrolled.add(self.flowbox)
        right_box.pack_start(scrolled, True, True, 0)

        root_box.pack_start(right_box, True, True, 0)

    def populate_apps(self):
        apps = Gio.AppInfo.get_all()
        visible_apps = [app for app in apps if app.should_show()]
        visible_apps.sort(key=lambda a: (a.get_display_name() or "").lower())

        for app in visible_apps:
            # Evita exibir o próprio lançador dentro da grade
            app_id = app.get_id() or ""
            if "legacyos-apps" in app_id:
                continue
            tile = AppTile(app)
            self.flowbox.add(tile)

    def filter_tile(self, child):
        if self.active_category != "all" and child.mapped_category != self.active_category:
            return False
        if self.search_query:
            q = self.search_query
            if q not in child.app_name.lower() and q not in child.app_desc.lower():
                return False
        return True

    def on_category_selected(self, _listbox, row):
        if row is None:
            return
        self.active_category = row.cat_id
        for cid, clabel, _ in CATEGORIES:
            if cid == self.active_category:
                self.header_title.set_markup(f"<b>{clabel}</b>")
                break
        self.flowbox.invalidate_filter()

    def on_search_changed(self, entry):
        self.search_query = entry.get_text().strip().lower()
        self.flowbox.invalidate_filter()

    def on_place_activated(self, _listbox, row):
        path = getattr(row, "place_path", os.path.expanduser("~"))
        os.makedirs(path, exist_ok=True)
        subprocess.Popen(["thunar", path], start_new_session=True)
        Gtk.main_quit()

    def on_tile_activated(self, _flowbox, tile):
        try:
            tile.app_info.launch([], None)
        except Exception:
            pass
        Gtk.main_quit()

    def on_key_press(self, _widget, event):
        if event.keyval == Gdk.KEY_Escape:
            Gtk.main_quit()
            return True
        if not self.search_entry.has_focus() and event.string and event.string.isprintable():
            self.search_entry.grab_focus()
        return False


def main():
    win = LegacyAppsWindow()
    win.show_all()
    win.search_entry.grab_focus()
    Gtk.main()


if __name__ == "__main__":
    main()
