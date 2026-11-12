#!/usr/bin/env python3
import gi, psutil, math
import cairo

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GLib

# --- Classe Customizada para Desenhar os Anéis com PyCairo ---
class RingGraph(Gtk.Overlay):
    def __init__(self, size=100, line_width=8, color=(0.0, 0.4, 1.0)):
        super().__init__()
        self.set_size_request(size, size)
        self.percentage = 0
        self.line_width = line_width
        self.color = color

        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.connect("draw", self.on_draw)
        self.add(self.drawing_area)

        self.label = Gtk.Label(label="0%")
        self.label.get_style_context().add_class("ring-label")
        self.label.set_halign(Gtk.Align.CENTER)
        self.label.set_valign(Gtk.Align.CENTER)
        self.add_overlay(self.label)

    def set_percentage(self, value):
        self.percentage = value
        self.label.set_text(f"{int(value)}%")
        self.drawing_area.queue_draw()

    def set_label_text(self, text):
        self.label.set_text(text)

    def on_draw(self, widget, cr):
        width = widget.get_allocated_width()
        height = widget.get_allocated_height()
        radius = (min(width, height) - self.line_width) / 2
        center_x, center_y = width / 2, height / 2

        cr.set_line_width(self.line_width)
        cr.set_source_rgb(0.88, 0.90, 0.94)
        cr.arc(center_x, center_y, radius, 0, 2 * math.pi)
        cr.stroke()

        cr.set_source_rgb(*self.color)
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        start_angle = -math.pi / 2
        end_angle = start_angle + (2 * math.pi * (self.percentage / 100))
        if self.percentage > 0:
            cr.arc(center_x, center_y, radius, start_angle, end_angle)
            cr.stroke()

class LegacyCareCenter(Gtk.Window):
    def __init__(self):
        super().__init__(title="Legacy Care Center")
        
        # --- Lógica de Dimensionamento Dinâmico (Telas Pequenas) ---
        screen = Gdk.Screen.get_default()
        max_width = min(1050, screen.get_width() - 20)
        max_height = min(650, screen.get_height() - 50)
        self.set_default_size(max_width, max_height)
        self.set_resizable(True)
        self.set_position(Gtk.WindowPosition.CENTER)

        # Barra de rolagem de segurança para telas minúsculas
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.add(scrolled_window)

        # CSS Embutido para o visual
        css = b"""
        window { background-color: #1a2238; }
        .sidebar { background-color: #141D29; padding: 20px 10px; border-right: 1px solid #2a3b5c; }
        .sidebar-title { color: #4a90e2; font-size: 18px; font-weight: bold; margin-bottom: 30px; }
        .menu-item { color: #a0aec0; padding: 12px; font-weight: bold; background: none; border: none; box-shadow: none; }
        .menu-item:hover { color: white; background-color: #1E2B3A; border-radius: 8px; }
        
        .content-area { background-color: #F4F7FA; padding: 30px; border-top-right-radius: 20px; border-bottom-right-radius: 20px; }
        .header-title { font-size: 24px; font-weight: bold; color: #1E293B; margin-bottom: 20px; }
        
        .card-panel { background-color: #FFFFFF; border-radius: 12px; padding: 20px; border: 1px solid #E2E8F0; box-shadow: 0 4px 6px rgba(0,0,0,0.02); }
        .card-title { font-size: 14px; font-weight: bold; color: #718096; margin-bottom: 5px; }
        .card-value { font-size: 28px; font-weight: bold; color: #1A202C; }
        
        .ring-label { font-size: 20px; font-weight: bold; color: #1A202C; }
        
        .btn-action { background-color: #0066FF; color: white; border-radius: 8px; padding: 12px 24px; font-weight: bold; border: none; }
        .btn-action:hover { background-color: #0A74DA; }
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        # O main_box agora vai dentro do ScrolledWindow
        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        scrolled_window.add(main_box)

        # --- SIDEBAR (Dark Glass) ---
        sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        sidebar.set_size_request(220, -1)
        sidebar.get_style_context().add_class("sidebar")
        
        lbl_logo = Gtk.Label(label="LegacyOS")
        lbl_logo.get_style_context().add_class("sidebar-title")
        lbl_logo.set_xalign(0)
        sidebar.pack_start(lbl_logo, False, False, 10)

        menu_items = ["Visão Geral", "Hardware", "Sistema", "Limpeza", "Otimização", "Drivers", "Relatórios"]
        for item in menu_items:
            btn = Gtk.Button(label=item)
            btn.get_style_context().add_class("menu-item")
            btn.set_xalign(0)
            sidebar.pack_start(btn, False, False, 0)

        main_box.pack_start(sidebar, False, False, 0)

        # --- ÁREA DE CONTEÚDO (Light Mode) ---
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        content_box.get_style_context().add_class("content-area")
        main_box.pack_start(content_box, True, True, 0)

        # Título
        header = Gtk.Label(label="Bem-vindo ao Legacy Care Center")
        header.get_style_context().add_class("header-title")
        header.set_xalign(0)
        content_box.pack_start(header, False, False, 0)

        # Grid para os cards
        grid = Gtk.Grid(column_spacing=20, row_spacing=20)
        content_box.pack_start(grid, True, True, 0)

        # --- CARD: Pontuação Geral (Score) ---
        score_card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        score_card.get_style_context().add_class("card-panel")
        
        self.ring_score = RingGraph(size=100, line_width=12, color=(0.086, 0.639, 0.290))
        self.ring_score.set_percentage(92)
        
        score_text_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        score_title = Gtk.Label(label="Pontuação Geral")
        score_title.get_style_context().add_class("card-title")
        score_title.set_xalign(0)
        score_desc = Gtk.Label(label="Sistema Saudável\nNenhum erro crítico detectado.")
        score_desc.set_xalign(0)
        score_text_box.pack_start(score_title, False, False, 0)
        score_text_box.pack_start(score_desc, False, False, 0)
        
        score_card.pack_start(self.ring_score, False, False, 0)
        score_card.pack_start(score_text_box, True, True, 0)
        grid.attach(score_card, 0, 0, 2, 1)

        # --- CARDS DE HARDWARE ---
        self.card_cpu, self.ring_cpu, self.lbl_cpu_val = self.create_hardware_card("Processador", "Intel Atom N450", (0.0, 0.4, 1.0))
        grid.attach(self.card_cpu, 0, 1, 1, 1)

        self.card_ram, self.ring_ram, self.lbl_ram_val = self.create_hardware_card("Memória RAM", "2 GB DDR3", (0.0, 0.4, 1.0))
        grid.attach(self.card_ram, 1, 1, 1, 1)

        self.card_disk, self.ring_disk, self.lbl_disk_val = self.create_hardware_card("Armazenamento", "SSD 120 GB", (0.0, 0.4, 1.0))
        grid.attach(self.card_disk, 0, 2, 1, 1)

        self.card_temp, self.ring_temp, self.lbl_temp_val = self.create_hardware_card("Temperatura", "Sensor CPU", (0.92, 0.70, 0.03))
        grid.attach(self.card_temp, 1, 2, 1, 1)

        # Botão de Ação
        btn_fix = Gtk.Button(label="Executar Diagnóstico Completo e Otimizar")
        btn_fix.get_style_context().add_class("btn-action")
        btn_fix.set_halign(Gtk.Align.END)
        content_box.pack_end(btn_fix, False, False, 0)

        self.connect("destroy", Gtk.main_quit)
        GLib.timeout_add_seconds(2, self.update_data)

    def create_hardware_card(self, title, sub_text, color):
        card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        card.get_style_context().add_class("card-panel")
        
        ring = RingGraph(size=80, line_width=8, color=color)
        
        text_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        text_box.set_valign(Gtk.Align.CENTER)
        
        lbl_title = Gtk.Label(label=title)
        lbl_title.get_style_context().add_class("card-title")
        lbl_title.set_xalign(0)
        
        lbl_sub = Gtk.Label(label=sub_text)
        lbl_sub.set_xalign(0)
        
        text_box.pack_start(lbl_title, False, False, 0)
        text_box.pack_start(lbl_sub, False, False, 0)
        
        card.pack_start(ring, False, False, 0)
        card.pack_start(text_box, True, True, 0)
        
        return card, ring, lbl_sub

    def update_data(self):
        try:
            cpu = psutil.cpu_percent()
            self.ring_cpu.set_percentage(cpu)
            
            ram = psutil.virtual_memory().percent
            self.ring_ram.set_percentage(ram)
            
            disk = psutil.disk_usage('/').percent
            self.ring_disk.set_percentage(disk)
            
            temps = psutil.sensors_temperatures()
            if 'coretemp' in temps and temps['coretemp']:
                temp = temps['coretemp'][0].current
                self.ring_temp.set_label_text(f"{int(temp)}°C")
            else:
                self.ring_temp.set_label_text("--°C")
        except Exception:
            pass
        return True

if __name__ == "__main__":
    app = LegacyCareCenter()
    app.show_all()
    Gtk.main()
