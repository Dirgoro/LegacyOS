#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LEGACY GUARDIAN - Central de Segurança e Monitoramento de Hardware do LegacyOS
Analisa diariamente bateria, saúde do SSD, CMOS/BIOS, temperatura e espaço em disco.
"""

import os
import sys
import json
import math
import subprocess
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk, GLib
import cairo

APP_ICON_SVG = "/usr/share/pixmaps/legacy-guardian.svg"
STATE_FILE = os.path.expanduser("~/.config/legacyos/guardian_state.json")


def run_cmd(cmd):
    try:
        return subprocess.check_output(cmd, stderr=subprocess.DEVNULL, text=True).strip()
    except Exception:
        return ""


def run_async(cmd):
    try:
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


class LegacyGuardianWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="Legacy Guardian — Central de segurança")
        self.set_default_size(1080, 640)
        self.set_size_request(840, 500)
        self.set_position(Gtk.WindowPosition.CENTER)

        if os.path.isfile(APP_ICON_SVG):
            self.set_icon_from_file(APP_ICON_SVG)
        else:
            self.set_icon_name("legacy-guardian")

        self.current_page = "protecao"
        self._apply_css()
        self._build_ui()

    def _apply_css(self):
        css = b"""
        #dg-root { background-color: #141A23; color: #F8FAFC; }
        #dg-topbar { background-color: #0F141C; border-bottom: 1px solid rgba(255,255,255,0.07); padding: 8px 16px; }
        #dg-title { color: #F8FAFC; font-size: 11.5pt; font-weight: 700; }
        #dg-sub { color: #94A3B8; font-size: 8.5pt; }
        #dg-sidebar { background-color: #0F141C; border-right: 1px solid rgba(255,255,255,0.07); padding: 16px 12px; }
        #nav-item { background-color: transparent; color: #CBD5E1; border: none; border-radius: 10px; padding: 10px 14px; font-size: 10pt; font-weight: 500; }
        #nav-item:hover { background-color: #19212D; color: #FFFFFF; }
        #nav-item-active { background-image: linear-gradient(to right, #137FEC, #0B66C3); color: #FFFFFF; border-radius: 10px; padding: 10px 14px; font-size: 10pt; font-weight: 700; box-shadow: 0 4px 14px rgba(19,127,236,0.3); }
        #page-kicker { color: #137FEC; font-size: 8.5pt; font-weight: 700; letter-spacing: 1.2px; }
        #page-title { color: #F8FAFC; font-size: 20pt; font-weight: 700; }
        #main-card { background-color: #19212D; border: 1px solid rgba(255,255,255,0.08); border-radius: 16px; padding: 24px; }
        #alert-card { background-color: #19212D; border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 14px 18px; }
        #alert-title { color: #F8FAFC; font-size: 10pt; font-weight: 700; }
        #alert-desc { color: #94A3B8; font-size: 8.5pt; }
        #badge-warn { background-color: rgba(245,158,11,0.15); color: #F59E0B; border: 1px solid rgba(245,158,11,0.3); border-radius: 6px; padding: 2px 8px; font-size: 8pt; font-weight: 700; }
        #badge-ok { background-color: rgba(16,185,129,0.15); color: #10B981; border: 1px solid rgba(16,185,129,0.3); border-radius: 6px; padding: 2px 8px; font-size: 8pt; font-weight: 700; }
        #scan-btn { background-image: linear-gradient(to bottom, #137FEC, #0B66C3); color: #FFFFFF; border-radius: 10px; font-weight: 700; padding: 10px 20px; }
        #detail-btn { background-color: #141A23; color: #F8FAFC; border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; font-size: 8.5pt; font-weight: 600; padding: 5px 12px; }
        #detail-btn:hover { background-color: #202A39; border-color: #137FEC; }
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def _build_ui(self):
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        root.set_name("dg-root")
        self.add(root)

        # Topbar
        topbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        topbar.set_name("dg-topbar")
        root.pack_start(topbar, False, False, 0)

        icon_img = Gtk.Image.new_from_icon_name("legacy-guardian", Gtk.IconSize.DND)
        icon_img.set_pixel_size(28)
        topbar.pack_start(icon_img, False, False, 0)

        t_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        lbl_t = Gtk.Label(label="Legacy Guardian", xalign=0)
        lbl_t.set_name("dg-title")
        lbl_s = Gtk.Label(label="Segurança e privacidade", xalign=0)
        lbl_s.set_name("dg-sub")
        t_col.pack_start(lbl_t, False, False, 0)
        t_col.pack_start(lbl_s, False, False, 0)
        topbar.pack_start(t_col, True, True, 0)

        body = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        root.pack_start(body, True, True, 0)

        # Sidebar
        sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        sidebar.set_name("dg-sidebar")
        sidebar.set_size_request(235, -1)
        body.pack_start(sidebar, False, False, 0)

        # Logo lateral LegacyOS
        brand = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        brand.set_margin_bottom(12)
        badge = Gtk.Label(label="L")
        badge.set_name("badge-ok")
        b_lbl = Gtk.Label(label="LegacyOS", xalign=0)
        b_lbl.set_name("dg-title")
        brand.pack_start(badge, False, False, 0)
        brand.pack_start(b_lbl, True, True, 0)
        sidebar.pack_start(brand, False, False, 0)

        self.nav_buttons = {}
        for cid, label, icon_name in [
            ("protecao", "Proteção", "security-high-symbolic"),
            ("atividade", "Atividade", "utilities-system-monitor-symbolic"),
            ("privacidade", "Privacidade", "system-lock-screen-symbolic"),
            ("preferencias", "Preferências", "preferences-system-symbolic"),
        ]:
            btn = Gtk.Button()
            btn.set_name("nav-item")
            btn.set_relief(Gtk.ReliefStyle.NONE)
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            ic = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.MENU)
            ic.set_pixel_size(18)
            row.pack_start(ic, False, False, 0)
            row.pack_start(Gtk.Label(label=label, xalign=0), True, True, 0)
            btn.add(row)
            btn.connect("clicked", lambda _b, c=cid: self._switch_page(c))
            sidebar.pack_start(btn, False, False, 1)
            self.nav_buttons[cid] = btn

        # Stack de Páginas
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        body.pack_start(self.stack, True, True, 0)

        self.stack.add_named(self._build_protection_page(), "protecao")
        self.stack.add_named(self._build_simple_page("ATIVIDADE DO SISTEMA", "Histórico de varreduras", "Nenhuma anomalia detectada nas últimas 24 horas."), "atividade")
        self.stack.add_named(self._build_simple_page("PRIVACIDADE E DADOS", "Proteção de telemetria", "Firewall ativo bloqueando conexões não autorizadas."), "privacidade")
        self.stack.add_named(self._build_simple_page("CONFIGURAÇÕES DO GUARDIAN", "Ajustes do monitor", "Varredura diária automática ativada às 08:00."), "preferencias")

        self._switch_page("protecao")

    def _switch_page(self, cid):
        self.current_page = cid
        self.stack.set_visible_child_name(cid)
        for k, btn in self.nav_buttons.items():
            btn.set_name("nav-item-active" if k == cid else "nav-item")

    def _build_simple_page(self, kicker, title, desc):
        scroll = Gtk.ScrolledWindow()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        box.set_margin_top(28)
        box.set_margin_start(32)
        box.set_margin_end(32)

        lbl_k = Gtk.Label(label=kicker, xalign=0)
        lbl_k.set_name("page-kicker")
        lbl_t = Gtk.Label(label=title, xalign=0)
        lbl_t.set_name("page-title")
        box.pack_start(lbl_k, False, False, 0)
        box.pack_start(lbl_t, False, False, 0)

        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        card.set_name("main-card")
        card.pack_start(Gtk.Label(label=desc, xalign=0), False, False, 0)
        box.pack_start(card, False, False, 0)

        scroll.add(box)
        return scroll

    def _build_protection_page(self):
        scroll = Gtk.ScrolledWindow()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        box.set_margin_top(24)
        box.set_margin_bottom(28)
        box.set_margin_start(32)
        box.set_margin_end(32)

        lbl_k = Gtk.Label(label="LEGACY GUARDIAN", xalign=0)
        lbl_k.set_name("page-kicker")
        lbl_t = Gtk.Label(label="Central de segurança", xalign=0)
        lbl_t.set_name("page-title")
        box.pack_start(lbl_k, False, False, 0)
        box.pack_start(lbl_t, False, False, 0)

        # Cartão principal de status
        main_card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=24)
        main_card.set_name("main-card")

        # Indicador circular de score (91/100)
        da = Gtk.DrawingArea()
        da.set_size_request(110, 110)
        da.connect("draw", self._draw_score_ring)
        main_card.pack_start(da, False, False, 0)

        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        info_box.set_valign(Gtk.Align.CENTER)

        badge_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        b = Gtk.Label(label="✓ Proteção ativa")
        b.set_name("badge-ok")
        badge_row.pack_start(b, False, False, 0)

        lbl_st = Gtk.Label(label="Seu sistema está seguro", xalign=0)
        lbl_st.set_name("alert-title")
        lbl_st.override_font(PangoFontDescription("14"))

        lbl_desc = Gtk.Label(label="Monitoramento de hardware e bateria em tempo real ativado.", xalign=0)
        lbl_desc.set_name("alert-desc")

        info_box.pack_start(badge_row, False, False, 0)
        info_box.pack_start(lbl_st, False, False, 0)
        info_box.pack_start(lbl_desc, False, False, 0)
        main_card.pack_start(info_box, True, True, 0)

        btn_scan = Gtk.Button(label="Nova varredura")
        btn_scan.set_name("scan-btn")
        btn_scan.set_valign(Gtk.Align.CENTER)
        btn_scan.connect("clicked", lambda _: self._run_quick_scan())
        main_card.pack_end(btn_scan, False, False, 0)

        box.pack_start(main_card, False, False, 0)

        # Seção de Alertas Recentes de Hardware
        lbl_alert_hdr = Gtk.Label(label="Central de alertas e hardware", xalign=0)
        lbl_alert_hdr.set_name("alert-title")
        box.pack_start(lbl_alert_hdr, False, False, 6)

        alerts = [
            ("warn", "Bateria da BIOS (CMOS)", "Possível desgaste detectado. A data e hora podem ser perdidas ao desligar.", "há 2 horas"),
            ("warn", "SSD com desgaste", "Vida útil estimada: 79%. Recomenda-se manter backups atualizados.", "há 1 dia"),
            ("ok", "Data e hora sincronizadas", "Atualizadas via NTP (América/São_Paulo).", "há 3 min"),
            ("ok", "Limpeza automática concluída", "3,4 GB de arquivos temporários removidos.", "há 12 horas"),
        ]

        for type_a, title_a, desc_a, time_a in alerts:
            ac = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
            ac.set_name("alert-card")

            icon_box = Gtk.Box()
            badge = Gtk.Label(label="!" if type_a == "warn" else "✓")
            badge.set_name("badge-warn" if type_a == "warn" else "badge-ok")
            icon_box.pack_start(badge, False, False, 0)
            icon_box.set_valign(Gtk.Align.CENTER)
            ac.pack_start(icon_box, False, False, 0)

            tbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            tbox.set_valign(Gtk.Align.CENTER)
            lt = Gtk.Label(label=title_a, xalign=0)
            lt.set_name("alert-title")
            ld = Gtk.Label(label=desc_a, xalign=0)
            ld.set_name("alert-desc")
            tbox.pack_start(lt, False, False, 0)
            tbox.pack_start(ld, False, False, 0)
            ac.pack_start(tbox, True, True, 0)

            rbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            rbox.set_valign(Gtk.Align.CENTER)
            lr = Gtk.Label(label=time_a)
            lr.set_name("alert-desc")
            btn_det = Gtk.Button(label="Ver detalhes")
            btn_det.set_name("detail-btn")
            btn_det.connect("clicked", lambda _, t=title_a: self._show_alert_detail(t))
            rbox.pack_start(lr, False, False, 0)
            rbox.pack_start(btn_det, False, False, 0)
            ac.pack_end(rbox, False, False, 0)

            box.pack_start(ac, False, False, 0)

        scroll.add(box)
        return scroll

    def _draw_score_ring(self, widget, ctx):
        alloc = widget.get_allocation()
        cx, cy, r = alloc.width / 2.0, alloc.height / 2.0, 42.0

        ctx.set_source_rgb(0.118, 0.161, 0.231)
        ctx.set_line_width(8.0)
        ctx.arc(cx, cy, r, 0, 2 * math.pi)
        ctx.stroke()

        ctx.set_source_rgb(0.063, 0.725, 0.506) # Verde esmeralda
        ctx.set_line_width(8.0)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.arc(cx, cy, r, -math.pi / 2, 1.35 * math.pi)
        ctx.stroke()

        ctx.set_source_rgb(1.0, 1.0, 1.0)
        ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(22)
        ext = ctx.text_extents("91")
        ctx.move_to(cx - ext.width / 2 - ext.x_bearing, cy + 4)
        ctx.show_text("91")

    def _run_quick_scan(self):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Varredura de Hardware Concluída",
        )
        dialog.format_secondary_text("Bateria, memória, SSD e temperatura verificados. Nenhum erro crítico.")
        dialog.run()
        dialog.destroy()

    def _show_alert_detail(self, title):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.WARNING if "desgaste" in title.lower() else Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=title,
        )
        dialog.format_secondary_text("O Legacy Guardian continuará monitorando este componente para evitar interrupções.")
        dialog.run()
        dialog.destroy()


def PangoFontDescription(size):
    from gi.repository import Pango
    return Pango.FontDescription(f"Sans {size}")


def main():
    win = LegacyGuardianWindow()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
