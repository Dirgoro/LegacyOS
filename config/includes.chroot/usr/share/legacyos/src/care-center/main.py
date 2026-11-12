#!/usr/bin/env python3
import gi, psutil
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GLib

class LegacyCareCenter(Gtk.Window):
    def __init__(self):
        super().__init__(title="Legacy Care Center")
        self.set_default_size(960, 540)
        self.set_resizable(False)
        self.set_position(Gtk.WindowPosition.CENTER)

        css = b"""
        window { background-color: #1a2238; color: #ffffff; }
        .card { background-color: #ffffff; color: #333333; border-radius: 8px; padding: 10px; margin: 5px; }
        .title { font-size: 20px; font-weight: bold; margin: 15px; }
        .card-title { font-size: 14px; color: #666; font-weight: bold; }
        .card-value { font-size: 24px; color: #000; font-weight: bold; }
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(main_box)

        header = Gtk.Label(label="Bem-vindo ao Legacy Care Center")
        header.get_style_context().add_class("title")
        main_box.pack_start(header, False, False, 0)

        self.grid = Gtk.Grid(column_spacing=10, row_spacing=10)
        self.grid.set_halign(Gtk.Align.CENTER)
        main_box.pack_start(self.grid, True, True, 0)

        self.lbl_cpu = Gtk.Label(label="--%")
        self.grid.attach(self.build_card("Processador", self.lbl_cpu, "Uso Atual"), 0, 0, 1, 1)
        self.lbl_ram = Gtk.Label(label="--%")
        self.grid.attach(self.build_card("Memória RAM", self.lbl_ram, "Uso Atual"), 1, 0, 1, 1)
        self.lbl_disk = Gtk.Label(label="--%")
        self.grid.attach(self.build_card("Armazenamento", self.lbl_disk, "Uso do Disco"), 2, 0, 1, 1)
        self.lbl_sys = Gtk.Label(label="--°C")
        self.grid.attach(self.build_card("Temperatura", self.lbl_sys, "CPU"), 3, 0, 1, 1)

        GLib.timeout_add_seconds(3, self.update_cards)
        self.connect("destroy", Gtk.main_quit)

    def build_card(self, title, val_label, sub_text):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        box.get_style_context().add_class("card")
        box.set_size_request(200, 100)
        
        lbl_title = Gtk.Label(label=title, xalign=0)
        lbl_title.get_style_context().add_class("card-title")
        val_label.get_style_context().add_class("card-value")
        val_label.set_xalign(0)
        lbl_sub = Gtk.Label(label=sub_text, xalign=0)
        
        box.pack_start(lbl_title, False, False, 0)
        box.pack_start(val_label, False, False, 0)
        box.pack_start(lbl_sub, False, False, 0)
        return box

    def update_cards(self):
        try:
            self.lbl_cpu.set_text(f"{psutil.cpu_percent()}%")
            self.lbl_ram.set_text(f"{psutil.virtual_memory().percent}%")
            self.lbl_disk.set_text(f"{psutil.disk_usage('/').percent}%")
            temps = psutil.sensors_temperatures()
            if 'coretemp' in temps and temps['coretemp']:
                self.lbl_sys.set_text(f"{temps['coretemp'][0].current}°C")
        except Exception:
            pass
        return True

if __name__ == "__main__":
    app = LegacyCareCenter()
    app.show_all()
    Gtk.main()
