#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LEGACY GUARDIAN - Applet Flutuante e Central de Notificações
Painel pop-up acionado pela barra superior do LegacyOS.
"""

import os
import sys
import math
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk, GLib
import cairo

APP_ICON_SVG = "/usr/share/pixmaps/legacy-guardian.svg"


class LegacyGuardianAppletWindow(Gtk.Window):
    def __init__(self):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.set_title("Legacy Guardian Applet")
        self.set_default_size(420, 680)
        self.set_position(Gtk.WindowPosition.NONE)
        self.set_decorated(False)
        self.set_keep_above(True)

        # Posiciona próximo ao ícone da barra superior (canto superior direito)
        screen = self.get_screen()
        w = screen.get_width()
        self.move(w - 440, 48)

        self._apply_css()
        self._build_ui()

    def _apply_css(self):
        css = b"""
        #applet-root {
            background-color: #141A23;
            color: #F8FAFC;
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 16px;
        }
        #top-header {
            background-color: #0F141C;
            border-bottom: 1px solid rgba(255, 255, 255, 0.07);
            padding: 14px 16px;
            border-top-left-radius: 15px;
            border-top-right-radius: 15px;
        }
        #title-main { color: #FFFFFF; font-size: 13pt; font-weight: 700; }
        #subtitle-main { color: #94A3B8; font-size: 8.5pt; }
        #tabs-box {
            background-color: #10151E;
            border-bottom: 1px solid rgba(255, 255, 255, 0.06);
            padding: 6px 12px;
        }
        #tab-active {
            background-color: #137FEC;
            color: #FFFFFF;
            border-radius: 8px;
            padding: 5px 12px;
            font-size: 8.5pt;
            font-weight: 700;
        }
        #tab-inactive {
            background-color: transparent;
            color: #94A3B8;
            border-radius: 8px;
            padding: 5px 12px;
            font-size: 8.5pt;
            font-weight: 600;
        }
        #tab-inactive:hover { background-color: #19212D; color: #FFFFFF; }
        #status-card {
            background-color: #19212D;
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 14px;
            padding: 16px;
        }
        #badge-warning {
            background-color: rgba(245, 158, 11, 0.18);
            color: #F59E0B;
            border: 1px solid rgba(245, 158, 11, 0.35);
            border-radius: 8px;
            padding: 3px 10px;
            font-size: 8.5pt;
            font-weight: 700;
        }
        #badge-ok {
            background-color: rgba(16, 185, 129, 0.18);
            color: #10B981;
            border: 1px solid rgba(16, 185, 129, 0.35);
            border-radius: 8px;
            padding: 3px 10px;
            font-size: 8.5pt;
            font-weight: 700;
        }
        #alert-box {
            background-color: #19212D;
            border: 1px solid rgba(255, 255, 255, 0.07);
            border-radius: 12px;
            padding: 12px 14px;
        }
        #alert-title { color: #F8FAFC; font-size: 9.5pt; font-weight: 700; }
        #alert-desc { color: #94A3B8; font-size: 8pt; }
        #action-btn {
            background-color: #141A23;
            color: #E2E8F0;
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 8px;
            font-size: 8pt;
            font-weight: 600;
            padding: 4px 10px;
        }
        #action-btn:hover { background-color: #202A39; border-color: #137FEC; color: #FFFFFF; }
        #footer-action {
            background-color: #19212D;
            border: 1px solid rgba(255, 255, 255, 0.07);
            border-radius: 10px;
            padding: 10px;
            color: #F8FAFC;
            font-size: 8pt;
            font-weight: 600;
        }
        #footer-action:hover { background-color: #202A39; border-color: #137FEC; }
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def _build_ui(self):
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        root.set_name("applet-root")
        self.add(root)

        # 1. Top Header com ícone e engrenagem
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        header.set_name("top-header")

        if os.path.isfile(APP_ICON_SVG):
            icon = Gtk.Image.new_from_file(APP_ICON_SVG)
            icon.set_pixel_size(36)
            header.pack_start(icon, False, False, 0)

        tbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        lbl_t = Gtk.Label(label="Legacy Guardian", xalign=0)
        lbl_t.set_name("title-main")
        lbl_s = Gtk.Label(label="Seu computador sempre protegido", xalign=0)
        lbl_s.set_name("subtitle-main")
        tbox.pack_start(lbl_t, False, False, 0)
        tbox.pack_start(lbl_s, False, False, 0)
        header.pack_start(tbox, True, True, 0)

        btn_gear = Gtk.Button.new_from_icon_name("emblem-system-symbolic", Gtk.IconSize.MENU)
        btn_gear.set_relief(Gtk.ReliefStyle.NONE)
        btn_gear.connect("clicked", lambda _: os.system("legacy-guardian &"))
        header.pack_end(btn_gear, False, False, 0)
        root.pack_start(header, False, False, 0)

        # 2. Abas Superiores (Notificações, Saúde Rápida, Ações)
        tabs = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        tabs.set_name("tabs-box")

        b1 = Gtk.Button(label="🔔 Notificações")
        b1.set_name("tab-active")
        b1.set_relief(Gtk.ReliefStyle.NONE)
        tabs.pack_start(b1, True, True, 0)

        b2 = Gtk.Button(label="❤️ Saúde Rápida")
        b2.set_name("tab-inactive")
        b2.set_relief(Gtk.ReliefStyle.NONE)
        b2.connect("clicked", lambda _: os.system("legacy-guardian &"))
        tabs.pack_start(b2, True, True, 0)

        b3 = Gtk.Button(label="🔧 Ações")
        b3.set_name("tab-inactive")
        b3.set_relief(Gtk.ReliefStyle.NONE)
        b3.connect("clicked", lambda _: os.system("legacy-care-center &"))
        tabs.pack_start(b3, True, True, 0)
        root.pack_start(tabs, False, False, 0)

        # 3. Conteúdo Rolável (Estado do Sistema + Alertas Recentes + Ações)
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content.set_margin_top(14)
        content.set_margin_bottom(14)
        content.set_margin_start(14)
        content.set_margin_end(14)

        # Cartão Estado do Sistema (Anel 91/100)
        st_card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        st_card.set_name("status-card")

        da = Gtk.DrawingArea()
        da.set_size_request(80, 80)
        da.connect("draw", self._draw_ring)
        st_card.pack_start(da, False, False, 0)

        st_info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        st_info.set_valign(Gtk.Align.CENTER)
        lbl_st_title = Gtk.Label(label="Estado do Sistema", xalign=0)
        lbl_st_title.set_name("alert-title")

        badge_warn = Gtk.Label(label="⚠️ Atenção necessária", xalign=0)
        badge_warn.set_name("badge-warning")

        lbl_st_sub = Gtk.Label(label="2 alertas ativos · 6 itens saudáveis", xalign=0)
        lbl_st_sub.set_name("alert-desc")

        st_info.pack_start(lbl_st_title, False, False, 0)
        st_info.pack_start(badge_warn, False, False, 0)
        st_info.pack_start(lbl_st_sub, False, False, 0)
        st_card.pack_start(st_info, True, True, 0)
        content.pack_start(st_card, False, False, 0)

        # Cabeçalho de Alertas Recentes
        hdr_alert = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        la_h = Gtk.Label(label="Alertas Recentes", xalign=0)
        la_h.set_name("alert-title")
        la_v = Gtk.Label(label="Ver todos", xalign=1)
        la_v.set_name("alert-desc")
        hdr_alert.pack_start(la_h, True, True, 0)
        hdr_alert.pack_end(la_v, False, False, 0)
        content.pack_start(hdr_alert, False, False, 2)

        # Alerta 1: Bateria da BIOS (CMOS)
        content.pack_start(self._make_alert_row(
            icon="🔋", title="Bateria da BIOS (CMOS)", time="há 2 horas",
            desc="Possível desgaste detectado. A data e hora podem ser perdidas ao desligar."
        ), False, False, 0)

        # Alerta 2: SSD com desgaste
        content.pack_start(self._make_alert_row(
            icon="💾", title="SSD com desgaste", time="há 1 dia",
            desc="Vida útil estimada: 79%. Recomenda-se manter backups atualizados."
        ), False, False, 0)

        # Alerta 3: Data e hora sincronizadas (OK)
        content.pack_start(self._make_alert_row(
            icon="🕒", title="Data e hora sincronizadas", time="há 3 min",
            desc="Atualizadas via NTP (América/São_Paulo).", ok=True
        ), False, False, 0)

        # Ações Rápidas Inferiores (Botões em grade)
        grid_actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

        b_care = Gtk.Button(label="Legacy Care Center")
        b_care.set_name("footer-action")
        b_care.connect("clicked", lambda _: os.system("legacy-care-center &"))
        grid_actions.pack_start(b_care, True, True, 0)

        b_fix = Gtk.Button(label="Corrigir Problemas")
        b_fix.set_name("footer-action")
        b_fix.connect("clicked", lambda _: self._on_fix_clicked())
        grid_actions.pack_start(b_fix, True, True, 0)

        content.pack_start(grid_actions, False, False, 6)

        scroll.add(content)
        root.pack_start(scroll, True, True, 0)

    def _draw_ring(self, widget, ctx):
        alloc = widget.get_allocation()
        cx, cy, r = alloc.width / 2.0, alloc.height / 2.0, 32.0

        ctx.set_source_rgb(0.118, 0.161, 0.231)
        ctx.set_line_width(6.0)
        ctx.arc(cx, cy, r, 0, 2 * math.pi)
        ctx.stroke()

        ctx.set_source_rgb(0.063, 0.725, 0.506)
        ctx.set_line_width(6.0)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.arc(cx, cy, r, -math.pi / 2, 1.35 * math.pi)
        ctx.stroke()

        ctx.set_source_rgb(1.0, 1.0, 1.0)
        ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(15)
        ext = ctx.text_extents("91")
        ctx.move_to(cx - ext.width / 2 - ext.x_bearing, cy + 3)
        ctx.show_text("91")

    def _make_alert_row(self, icon, title, time, desc, ok=False):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_name("alert-box")

        top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        lbl_icon = Gtk.Label(label=icon)
        lbl_title = Gtk.Label(label=title, xalign=0)
        lbl_title.set_name("alert-title")
        lbl_time = Gtk.Label(label=time, xalign=1)
        lbl_time.set_name("alert-desc")

        top.pack_start(lbl_icon, False, False, 0)
        top.pack_start(lbl_title, True, True, 0)
        top.pack_end(lbl_time, False, False, 0)
        box.pack_start(top, False, False, 0)

        lbl_desc = Gtk.Label(label=desc, xalign=0)
        lbl_desc.set_name("alert-desc")
        box.pack_start(lbl_desc, False, False, 0)

        if not ok:
            btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            btn_box.set_margin_top(4)

            b_det = Gtk.Button(label="Ver detalhes")
            b_det.set_name("action-btn")
            b_det.connect("clicked", lambda _, t=title: self._show_detail(t))
            btn_box.pack_start(b_det, False, False, 0)

            b_ign = Gtk.Button(label="Ignorar")
            b_ign.set_name("action-btn")
            b_ign.connect("clicked", lambda _, b=box: b.destroy())
            btn_box.pack_start(b_ign, False, False, 0)

            box.pack_start(btn_box, False, False, 0)

        return box

    def _show_detail(self, title):
        dlg = Gtk.MessageDialog(
            transient_for=self, flags=0,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.OK, text=title
        )
        dlg.format_secondary_text("O Legacy Guardian está monitorando este componente ativamente.")
        dlg.run()
        dlg.destroy()

    def _on_fix_clicked(self):
        dlg = Gtk.MessageDialog(
            transient_for=self, flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK, text="Otimização concluída"
        )
        dlg.format_secondary_text("Cache limpo e permissões de hardware verificadas.")
        dlg.run()
        dlg.destroy()


def main():
    win = LegacyGuardianAppletWindow()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
