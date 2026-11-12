#!/usr/bin/env python3
import gi, subprocess
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GLib

class LegacyControlCenter(Gtk.Window):
    def __init__(self):
        super().__init__(title="LegacyOS Control Center")
        
        # Dimensionamento dinâmico para telas pequenas
        screen = Gdk.Screen.get_default()
        max_width = min(850, screen.get_width() - 20)
        max_height = min(550, screen.get_height() - 50)
        self.set_default_size(max_width, max_height)
        self.set_resizable(True)
        self.set_position(Gtk.WindowPosition.CENTER)

        # Carrega o CSS Global
        css_provider = Gtk.CssProvider()
        try:
            css_provider.load_from_path('/usr/share/themes/LegacyOS-Theme/gtk-3.0/gtk.css')
            Gtk.StyleContext.add_provider_for_screen(
                Gdk.Screen.get_default(), css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
        except Exception:
            pass

        # Layout Principal com ScrolledWindow para telas minúsculas
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.add(scrolled_window)

        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        scrolled_window.add(main_box)

        # Sidebar
        sidebar = Gtk.StackSidebar()
        sidebar.set_size_request(200, -1)
        sidebar.get_style_context().add_class("sidebar")
        main_box.pack_start(sidebar, False, False, 0)

        # Stack
        stack = Gtk.Stack()
        stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        stack.set_transition_duration(300)
        main_box.pack_start(stack, True, True, 0)
        sidebar.set_stack(stack)

        stack.add_titled(self.create_icons_page(), "icons", "Ícones")
        stack.add_titled(self.create_display_page(), "display", "Tela e Vídeo")
        stack.add_titled(self.create_appearance_page(), "appearance", "Aparência")
        stack.add_titled(self.create_about_page(), "about", "Sobre")

        self.connect("destroy", Gtk.main_quit)

    def create_icons_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        box.set_margin_top(20); box.set_margin_bottom(20)
        box.set_margin_start(20); box.set_margin_end(20)

        lbl = Gtk.Label(label="Configurações de Ícones")
        lbl.set_markup("<span size='x-large' weight='bold'>Configurações de Ícones</span>")
        lbl.set_xalign(0)
        box.pack_start(lbl, False, False, 10)

        card_show = self.create_card("Visibilidade")
        btn_hide_all = Gtk.Button(label="Ocultar Todos os Ícones")
        btn_hide_all.connect("clicked", lambda w: self.run_cmd("xfconf-query -c xfce4-desktop -p /desktop-icons/style -s 0"))
        btn_show_all = Gtk.Button(label="Mostrar Ícones Padrão")
        btn_show_all.connect("clicked", lambda w: self.run_cmd("xfconf-query -c xfce4-desktop -p /desktop-icons/style -s 3"))
        hbox_show = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        hbox_show.pack_start(btn_show_all, True, True, 0)
        hbox_show.pack_start(btn_hide_all, True, True, 0)
        card_show.pack_start(hbox_show, True, True, 0)
        box.pack_start(card_show, False, False, 0)

        card_align = self.create_card("Alinhamento dos Ícones")
        grid = Gtk.Grid(column_spacing=10, row_spacing=10)
        btn_right = Gtk.Button(label="Direita (Padrão)"); btn_right.get_style_context().add_class("suggested-action")
        btn_right.connect("clicked", lambda w: self.run_cmd("bash /usr/bin/legacyos-move-icons.sh right"))
        btn_left = Gtk.Button(label="Esquerda")
        btn_left.connect("clicked", lambda w: self.run_cmd("bash /usr/bin/legacyos-move-icons.sh left"))
        btn_top = Gtk.Button(label="Topo")
        btn_top.connect("clicked", lambda w: self.run_cmd("bash /usr/bin/legacyos-move-icons.sh top"))
        btn_bottom = Gtk.Button(label="Inferior")
        btn_bottom.connect("clicked", lambda w: self.run_cmd("bash /usr/bin/legacyos-move-icons.sh bottom"))
        grid.attach(btn_left, 0, 0, 1, 1); grid.attach(btn_right, 1, 0, 1, 1)
        grid.attach(btn_top, 0, 1, 1, 1); grid.attach(btn_bottom, 1, 1, 1, 1)
        card_align.pack_start(grid, True, True, 0)
        box.pack_start(card_align, False, False, 0)
        return box

    def create_display_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        box.set_margin_top(20); box.set_margin_bottom(20)
        box.set_margin_start(20); box.set_margin_end(20)
        lbl = Gtk.Label(label="Tela e Vídeo")
        lbl.set_markup("<span size='x-large' weight='bold'>Tela e Vídeo</span>")
        lbl.set_xalign(0)
        box.pack_start(lbl, False, False, 10)
        card = self.create_card("Configurações de Vídeo")
        desc = Gtk.Label(label="Altere a resolução, frequência e escala usando o gerenciador nativo otimizado do XFCE.")
        desc.set_line_wrap(True); desc.set_xalign(0)
        card.pack_start(desc, False, False, 5)
        btn_display = Gtk.Button(label="Abrir Configurações de Tela")
        btn_display.get_style_context().add_class("suggested-action")
        btn_display.connect("clicked", lambda w: self.run_cmd("xfce4-display-settings"))
        card.pack_start(btn_display, False, False, 10)
        box.pack_start(card, False, False, 0)
        return box

    def create_appearance_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        box.set_margin_top(20); box.set_margin_bottom(20)
        box.set_margin_start(20); box.set_margin_end(20)
        lbl = Gtk.Label(label="Aparência")
        lbl.set_markup("<span size='x-large' weight='bold'>Aparência</span>")
        lbl.set_xalign(0)
        box.pack_start(lbl, False, False, 10)
        card = self.create_card("Papel de Parede e Tema")
        btn_wall = Gtk.Button(label="Alterar Papel de Parede")
        btn_wall.connect("clicked", lambda w: self.run_cmd("xfce4-appearance-settings"))
        card.pack_start(btn_wall, False, False, 5)
        box.pack_start(card, False, False, 0)
        return box

    def create_about_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        box.set_margin_top(20); box.set_margin_bottom(20)
        box.set_margin_start(20); box.set_margin_end(20)
        lbl = Gtk.Label(label="Sobre o LegacyOS")
        lbl.set_markup("<span size='x-large' weight='bold'>LegacyOS 1.0</span>")
        lbl.set_xalign(0)
        box.pack_start(lbl, False, False, 10)
        card = self.create_card("Informações do Sistema")
        desc = Gtk.Label(label="Desempenho moderno. Hardware clássico.\n\nSistema operacional leve e seguro desenvolvido para revitalizar computadores antigos.")
        desc.set_line_wrap(True); desc.set_xalign(0)
        card.pack_start(desc, False, False, 5)
        box.pack_start(card, False, False, 0)
        return box

    def create_card(self, title):
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        card.get_style_context().add_class("card-panel")
        lbl = Gtk.Label(label=title)
        lbl.set_markup(f"<span weight='bold' color='#718096'>{title}</span>")
        lbl.set_xalign(0)
        card.pack_start(lbl, False, False, 0)
        return card

    def run_cmd(self, cmd):
        subprocess.Popen(cmd, shell=True)

if __name__ == "__main__":
    app = LegacyControlCenter()
    app.show_all()
    Gtk.main()
