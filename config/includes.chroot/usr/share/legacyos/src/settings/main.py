#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LEGACYOS SETTINGS - Preferências do Sistema
Interface fiel ao design oficial do LegacyOS (#0F141C / #141A23 / #19212D / #137FEC)
com controles reais integrados ao XFCE, xfwm4, NetworkManager, PulseAudio e Plank.
"""

import os
import sys
import json
import math
import socket
import platform
import subprocess
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk, GLib
import cairo

APP_ICON_SVG = "/usr/share/pixmaps/legacyos-settings.svg"
STATE_FILE = os.path.expanduser("~/.config/legacyos/settings_state.json")


def run_cmd(cmd):
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, text=True)
        return out.strip()
    except Exception:
        return ""


def run_async(cmd):
    try:
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


class ThemePreviewCard(Gtk.Button):
    """Cartão visual com miniatura desenhada em Cairo (Claro, Escuro ou Automático)."""

    def __init__(self, mode, title, selected=False, on_select=None):
        super().__init__()
        self.mode = mode
        self.title = title
        self.selected = selected
        self.on_select = on_select

        self.set_relief(Gtk.ReliefStyle.NONE)
        self.set_can_focus(False)
        self.set_name("theme-card-selected" if selected else "theme-card")

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_margin_top(6)
        box.set_margin_bottom(6)
        box.set_margin_start(8)
        box.set_margin_end(8)

        self.area = Gtk.DrawingArea()
        self.area.set_size_request(86, 52)
        self.area.connect("draw", self._on_draw)
        box.pack_start(self.area, False, False, 0)

        lbl = Gtk.Label(label=title)
        lbl.set_name("theme-card-label")
        box.pack_start(lbl, False, False, 0)

        self.add(box)
        self.connect("clicked", self._handle_click)

    def set_selected(self, state):
        self.selected = state
        self.set_name("theme-card-selected" if state else "theme-card")
        self.area.queue_draw()

    def _handle_click(self, _btn):
        if self.on_select:
            self.on_select(self.mode)

    def _rounded_rect(self, ctx, x, y, w, h, r):
        ctx.new_sub_path()
        ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
        ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
        ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
        ctx.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
        ctx.close_path()

    def _draw_mockup(self, ctx, w, h, dark=True):
        bg = (0.098, 0.129, 0.176) if dark else (0.945, 0.961, 0.976)
        side = (0.059, 0.078, 0.110) if dark else (0.886, 0.910, 0.941)
        card = (0.145, 0.192, 0.259) if dark else (1.0, 1.0, 1.0)

        # Fundo geral
        ctx.set_source_rgb(*bg)
        ctx.rectangle(0, 0, w, h)
        ctx.fill()

        # Sidebar
        ctx.set_source_rgb(*side)
        ctx.rectangle(0, 0, w * 0.28, h)
        ctx.fill()

        # Linhas sidebar
        ctx.set_source_rgba(0.58, 0.64, 0.72, 0.35)
        ctx.rectangle(6, 10, w * 0.16, 4)
        ctx.rectangle(6, 18, w * 0.13, 4)
        ctx.rectangle(6, 26, w * 0.15, 4)
        ctx.fill()

        # Cartões conteúdo
        ctx.set_source_rgb(*card)
        ctx.rectangle(w * 0.34, 9, w * 0.58, 14)
        ctx.rectangle(w * 0.34, 28, w * 0.58, 15)
        ctx.fill()

    def _on_draw(self, widget, ctx):
        alloc = widget.get_allocation()
        w, h = float(alloc.width), float(alloc.height)

        ctx.save()
        self._rounded_rect(ctx, 1, 1, w - 2, h - 2, 7)
        ctx.clip()

        if self.mode == "light":
            self._draw_mockup(ctx, w, h, dark=False)
        elif self.mode == "dark":
            self._draw_mockup(ctx, w, h, dark=True)
        else:
            # Metade clara à esquerda (diagonal), metade escura à direita
            self._draw_mockup(ctx, w, h, dark=True)
            ctx.save()
            ctx.move_to(0, 0)
            ctx.line_to(w * 0.62, 0)
            ctx.line_to(w * 0.38, h)
            ctx.line_to(0, h)
            ctx.close_path()
            ctx.clip()
            self._draw_mockup(ctx, w, h, dark=False)
            ctx.restore()

        ctx.restore()

        # Borda do mockup
        self._rounded_rect(ctx, 1, 1, w - 2, h - 2, 7)
        if self.selected:
            ctx.set_source_rgb(0.075, 0.498, 0.925)
            ctx.set_line_width(1.8)
        else:
            ctx.set_source_rgba(1.0, 1.0, 1.0, 0.14)
            ctx.set_line_width(1.0)
        ctx.stroke()

        # Badge de seleção circular azul no canto superior direito
        if self.selected:
            cx, cy, r = w - 10, 10, 7.5
            ctx.set_source_rgb(0.075, 0.498, 0.925)
            ctx.arc(cx, cy, r, 0, 2 * math.pi)
            ctx.fill()

            ctx.set_source_rgb(1.0, 1.0, 1.0)
            ctx.set_line_width(1.8)
            ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            ctx.set_line_join(cairo.LINE_JOIN_ROUND)
            ctx.move_to(cx - 3.2, cy + 0.2)
            ctx.line_to(cx - 0.8, cy + 2.6)
            ctx.line_to(cx + 3.5, cy - 2.4)
            ctx.stroke()


class LegacySettingsWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="Configurações — Preferências do sistema")
        self.set_default_size(1100, 620)
        self.set_size_request(860, 500)
        self.set_position(Gtk.WindowPosition.CENTER)

        if os.path.isfile(APP_ICON_SVG):
            self.set_icon_from_file(APP_ICON_SVG)
        else:
            self.set_icon_name("legacyos-settings")

        self.state = self._load_state()
        self.nav_buttons = {}
        self.theme_cards = {}
        self.searchable_items = []

        self._apply_css()
        self._build_ui()
        self._select_category("aparencia")

    def _load_state(self):
        default = {
            "theme_mode": "dark",
            "auto_night": True,
            "transparency": True,
            "animations": True,
            "glass_intensity": 72,
            "dnd": False,
            "auto_lock": True,
        }
        try:
            if os.path.isfile(STATE_FILE):
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    default.update(data)
        except Exception:
            pass
        return default

    def _save_state(self):
        try:
            os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.state, f, indent=2)
        except Exception:
            pass

    def _apply_css(self):
        css = b"""
        #st-root {
            background-color: #141A23;
            color: #F8FAFC;
        }
        #st-topbar {
            background-color: #0F141C;
            border-bottom: 1px solid rgba(255, 255, 255, 0.07);
            padding: 8px 16px;
        }
        #st-app-title {
            color: #F8FAFC;
            font-size: 11.5pt;
            font-weight: 700;
        }
        #st-app-sub {
            color: #94A3B8;
            font-size: 8.5pt;
        }
        #st-sidebar {
            background-color: #0F141C;
            border-right: 1px solid rgba(255, 255, 255, 0.07);
            padding: 16px 12px;
        }
        #st-search {
            background-color: #19212D;
            color: #F8FAFC;
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 10px;
            padding: 7px 12px;
            font-size: 9.5pt;
        }
        #st-search:focus {
            border-color: #137FEC;
        }
        #nav-item {
            background-color: transparent;
            color: #CBD5E1;
            border: none;
            border-radius: 10px;
            padding: 9px 14px;
            font-size: 10pt;
            font-weight: 500;
        }
        #nav-item:hover {
            background-color: #19212D;
            color: #FFFFFF;
        }
        #nav-item-active {
            background-image: linear-gradient(to right, #137FEC, #0B66C3);
            color: #FFFFFF;
            border: none;
            border-radius: 10px;
            padding: 9px 14px;
            font-size: 10pt;
            font-weight: 700;
            box-shadow: 0 4px 14px rgba(19, 127, 236, 0.30);
        }
        #page-kicker {
            color: #137FEC;
            font-size: 8.5pt;
            font-weight: 700;
            letter-spacing: 1.2px;
        }
        #page-title {
            color: #F8FAFC;
            font-size: 20pt;
            font-weight: 700;
        }
        #setting-card {
            background-color: #19212D;
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 14px;
            padding: 16px 20px;
        }
        #row-title {
            color: #F8FAFC;
            font-size: 10.5pt;
            font-weight: 600;
        }
        #row-desc {
            color: #94A3B8;
            font-size: 8.8pt;
        }
        #icon-badge {
            background-color: rgba(19, 127, 236, 0.14);
            border: 1px solid rgba(56, 189, 248, 0.25);
            border-radius: 10px;
            padding: 8px;
        }
        #row-divider {
            background-color: rgba(255, 255, 255, 0.06);
            min-height: 1px;
        }
        #theme-card {
            background-color: #141A23;
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            padding: 2px;
        }
        #theme-card:hover {
            border-color: rgba(56, 189, 248, 0.45);
        }
        #theme-card-selected {
            background-color: rgba(19, 127, 236, 0.10);
            border: 1.5px solid #137FEC;
            border-radius: 12px;
            padding: 2px;
        }
        #theme-card-label {
            color: #E2E8F0;
            font-size: 8.5pt;
            font-weight: 600;
        }
        #scale-hint {
            color: #64748B;
            font-size: 8.5pt;
        }
        #action-pill {
            background-color: #141A23;
            color: #F8FAFC;
            border: 1px solid rgba(255, 255, 255, 0.10);
            border-radius: 9px;
            padding: 6px 14px;
            font-weight: 600;
        }
        #action-pill:hover {
            background-color: #202A39;
            border-color: #137FEC;
        }
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

    def _build_ui(self):
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        root.set_name("st-root")
        self.add(root)

        # Barra superior (Idêntica à imagem)
        topbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        topbar.set_name("st-topbar")
        root.pack_start(topbar, False, False, 0)

        icon_img = Gtk.Image.new_from_icon_name("legacyos-settings", Gtk.IconSize.DND)
        icon_img.set_pixel_size(28)
        topbar.pack_start(icon_img, False, False, 0)

        title_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        lbl_t = Gtk.Label(label="Configurações", xalign=0)
        lbl_t.set_name("st-app-title")
        lbl_s = Gtk.Label(label="Preferências do sistema", xalign=0)
        lbl_s.set_name("st-app-sub")
        title_col.pack_start(lbl_t, False, False, 0)
        title_col.pack_start(lbl_s, False, False, 0)
        topbar.pack_start(title_col, True, True, 0)

        # Corpo Principal: Sidebar à esquerda + Conteúdo à direita
        body = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        root.pack_start(body, True, True, 0)

        sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        sidebar.set_name("st-sidebar")
        sidebar.set_size_request(235, -1)
        body.pack_start(sidebar, False, False, 0)

        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_name("st-search")
        self.search_entry.set_placeholder_text("Buscar ajustes")
        self.search_entry.connect("search-changed", self._on_search_changed)
        sidebar.pack_start(self.search_entry, False, False, 6)

        categories = [
            ("aparencia", "Aparência", "video-display-symbolic"),
            ("rede", "Rede e internet", "network-wireless-symbolic"),
            ("som", "Som", "audio-volume-high-symbolic"),
            ("notificacoes", "Notificações", "preferences-system-notifications-symbolic"),
            ("contas", "Contas", "avatar-default-symbolic"),
            ("privacidade", "Privacidade", "system-lock-screen-symbolic"),
            ("sobre", "Sobre", "dialog-information-symbolic"),
        ]

        for cat_id, label, icon_name in categories:
            btn = Gtk.Button()
            btn.set_name("nav-item")
            btn.set_relief(Gtk.ReliefStyle.NONE)
            btn.set_can_focus(False)

            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            ic = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.MENU)
            ic.set_pixel_size(18)
            row.pack_start(ic, False, False, 0)
            row.pack_start(Gtk.Label(label=label, xalign=0), True, True, 0)
            btn.add(row)
            btn.connect("clicked", lambda _b, cid=cat_id: self._select_category(cid))
            sidebar.pack_start(btn, False, False, 1)
            self.nav_buttons[cat_id] = btn

        # Stack de Páginas
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.stack.set_transition_duration(140)
        body.pack_start(self.stack, True, True, 0)

        self.stack.add_named(self._wrap_page("PREFERÊNCIAS DO SISTEMA", "Aparência", self._build_appearance_page()), "aparencia")
        self.stack.add_named(self._wrap_page("CONECTIVIDADE", "Rede e internet", self._build_network_page()), "rede")
        self.stack.add_named(self._wrap_page("ÁUDIO E DISPOSITIVOS", "Som", self._build_sound_page()), "som")
        self.stack.add_named(self._wrap_page("ALERTAS DO SISTEMA", "Notificações", self._build_notifications_page()), "notificacoes")
        self.stack.add_named(self._wrap_page("PERFIL E SEGURANÇA", "Contas", self._build_accounts_page()), "contas")
        self.stack.add_named(self._wrap_page("PROTEÇÃO E BLOQUEIO", "Privacidade", self._build_privacy_page()), "privacidade")
        self.stack.add_named(self._wrap_page("INFORMAÇÕES DO SISTEMA", "Sobre", self._build_about_page()), "sobre")

    def _wrap_page(self, kicker, title, content_widget):
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        container.set_margin_top(24)
        container.set_margin_bottom(28)
        container.set_margin_start(32)
        container.set_margin_end(32)

        hdr_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        lbl_k = Gtk.Label(label=kicker, xalign=0)
        lbl_k.set_name("page-kicker")
        lbl_t = Gtk.Label(label=title, xalign=0)
        lbl_t.set_name("page-title")
        hdr_box.pack_start(lbl_k, False, False, 0)
        hdr_box.pack_start(lbl_t, False, False, 0)

        container.pack_start(hdr_box, False, False, 4)
        container.pack_start(content_widget, False, False, 0)
        scroll.add(container)
        return scroll

    def _make_card(self):
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        card.set_name("setting-card")
        return card

    def _make_switch_row(self, cat_id, icon_name, title, desc, initial_val, callback):
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)

        badge = Gtk.Box()
        badge.set_name("icon-badge")
        ic = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.MENU)
        ic.set_pixel_size(18)
        badge.add(ic)
        row.pack_start(badge, False, False, 0)

        txt = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        lbl_t = Gtk.Label(label=title, xalign=0)
        lbl_t.set_name("row-title")
        lbl_d = Gtk.Label(label=desc, xalign=0)
        lbl_d.set_name("row-desc")
        txt.pack_start(lbl_t, False, False, 0)
        txt.pack_start(lbl_d, False, False, 0)
        row.pack_start(txt, True, True, 0)

        sw = Gtk.Switch()
        sw.set_active(initial_val)
        sw.set_valign(Gtk.Align.CENTER)
        sw.connect("notify::active", lambda s, _p: callback(s.get_active()))
        row.pack_end(sw, False, False, 0)

        self.searchable_items.append((cat_id, f"{title} {desc}".lower()))
        return row

    def _make_divider(self):
        sep = Gtk.Box()
        sep.set_name("row-divider")
        return sep

    # ==========================================================================
    # 1. ABA APARÊNCIA (CORRESPONDENTE EXATO À IMAGEM ANEXADA)
    # ==========================================================================
    def _build_appearance_page(self):
        col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)

        # Cartão 1: Tema do sistema (Claro / Escuro / Automático)
        card_theme = self._make_card()
        row_theme = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)

        txt_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        txt_box.set_valign(Gtk.Align.CENTER)
        lbl_t = Gtk.Label(label="Tema do sistema", xalign=0)
        lbl_t.set_name("row-title")
        lbl_d = Gtk.Label(label="Escolha como as janelas e os controles são exibidos.", xalign=0)
        lbl_d.set_name("row-desc")
        txt_box.pack_start(lbl_t, False, False, 0)
        txt_box.pack_start(lbl_d, False, False, 0)
        row_theme.pack_start(txt_box, True, True, 0)

        cards_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        for mode, label in [("light", "Claro"), ("dark", "Escuro"), ("auto", "Automático")]:
            c = ThemePreviewCard(
                mode=mode,
                title=label,
                selected=(self.state["theme_mode"] == mode),
                on_select=self._on_theme_selected,
            )
            self.theme_cards[mode] = c
            cards_box.pack_start(c, False, False, 0)

        row_theme.pack_end(cards_box, False, False, 0)
        card_theme.pack_start(row_theme, False, False, 0)
        col.pack_start(card_theme, False, False, 0)
        self.searchable_items.append(("aparencia", "tema do sistema claro escuro automatico"))

        # Cartão 2: Switches (Modo noturno automático, Efeitos de transparência, Animações)
        card_sw = self._make_card()
        card_sw.pack_start(
            self._make_switch_row(
                "aparencia",
                "weather-clear-night-symbolic",
                "Modo noturno automático",
                "Ativar o tema escuro após o pôr do sol",
                self.state["auto_night"],
                self._on_toggle_auto_night,
            ),
            False,
            False,
            0,
        )
        card_sw.pack_start(self._make_divider(), False, False, 0)
        card_sw.pack_start(
            self._make_switch_row(
                "aparencia",
                "preferences-desktop-effects-symbolic",
                "Efeitos de transparência",
                "Permitir desfoque em menus, dock e janelas",
                self.state["transparency"],
                self._on_toggle_transparency,
            ),
            False,
            False,
            0,
        )
        card_sw.pack_start(self._make_divider(), False, False, 0)
        card_sw.pack_start(
            self._make_switch_row(
                "aparencia",
                "view-grid-symbolic",
                "Animações da interface",
                "Movimentos suaves ao alternar entre aplicativos",
                self.state["animations"],
                self._on_toggle_animations,
            ),
            False,
            False,
            0,
        )
        col.pack_start(card_sw, False, False, 0)

        # Cartão 3: Intensidade do vidro (Opaco <-> Transparente)
        card_glass = self._make_card()
        row_glass = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)

        g_txt = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        g_t = Gtk.Label(label="Intensidade do vidro", xalign=0)
        g_t.set_name("row-title")
        g_d = Gtk.Label(label="Ajuste a transparência das superfícies.", xalign=0)
        g_d.set_name("row-desc")
        g_txt.pack_start(g_t, False, False, 0)
        g_txt.pack_start(g_d, False, False, 0)
        row_glass.pack_start(g_txt, True, True, 0)

        slider_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        slider_box.set_valign(Gtk.Align.CENTER)
        lbl_opaco = Gtk.Label(label="Opaco")
        lbl_opaco.set_name("scale-hint")
        slider_box.pack_start(lbl_opaco, False, False, 0)

        scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        scale.set_value(self.state["glass_intensity"])
        scale.set_draw_value(False)
        scale.set_size_request(240, -1)
        scale.connect("value-changed", self._on_glass_changed)
        slider_box.pack_start(scale, False, False, 0)

        lbl_transp = Gtk.Label(label="Transparente")
        lbl_transp.set_name("scale-hint")
        slider_box.pack_start(lbl_transp, False, False, 0)

        row_glass.pack_end(slider_box, False, False, 0)
        card_glass.pack_start(row_glass, False, False, 0)
        col.pack_start(card_glass, False, False, 0)
        self.searchable_items.append(("aparencia", "intensidade do vidro opaco transparente"))

        return col

    def _on_theme_selected(self, mode):
        self.state["theme_mode"] = mode
        for m, card in self.theme_cards.items():
            card.set_selected(m == mode)
        self._save_state()

        if mode == "light":
            run_async(["xfconf-query", "-c", "xsettings", "-p", "/Net/ThemeName", "-s", "Adwaita"])
        else:
            run_async(["xfconf-query", "-c", "xsettings", "-p", "/Net/ThemeName", "-s", "LegacyOS-Theme"])

    def _on_toggle_auto_night(self, active):
        self.state["auto_night"] = active
        self._save_state()
        if active:
            self._on_theme_selected("dark")

    def _on_toggle_transparency(self, active):
        self.state["transparency"] = active
        self._save_state()
        val = "true" if active else "false"
        run_async(["xfconf-query", "-c", "xfwm4", "-p", "/general/use_compositing", "-s", val])

    def _on_toggle_animations(self, active):
        self.state["animations"] = active
        self._save_state()
        val = "true" if active else "false"
        run_async(["xfconf-query", "-c", "xsettings", "-p", "/Gtk/EnableAnimations", "-n", "-t", "bool", "-s", val])
        run_async(["gsettings", "set", "net.launchpad.plank.dock.settings:/net/launchpad/plank/docks/dock1/", "zoom-enabled", val])

    def _on_glass_changed(self, scale):
        val = int(scale.get_value())
        self.state["glass_intensity"] = val
        self._save_state()
        # Converte 0..100 (Opaco -> Transparente) em alpha 1.00 .. 0.72 no painel superior
        alpha = round(1.0 - (val / 100.0) * 0.28, 3)
        run_async([
            "xfconf-query", "-c", "xfce4-panel", "-p", "/panels/panel-1/background-rgba",
            "-t", "double", "-s", "0.059",
            "-t", "double", "-s", "0.078",
            "-t", "double", "-s", "0.110",
            "-t", "double", "-s", str(alpha),
        ])

    # ==========================================================================
    # 2. REDE E INTERNET
    # ==========================================================================
    def _build_network_page(self):
        col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        card = self._make_card()

        wifi_state = run_cmd(["nmcli", "radio", "wifi"])
        is_wifi_on = wifi_state != "disabled"

        card.pack_start(
            self._make_switch_row(
                "rede",
                "network-wireless-symbolic",
                "Wi-Fi sem fio",
                "Conectar-se a redes Wi-Fi disponíveis",
                is_wifi_on,
                lambda on: run_async(["nmcli", "radio", "wifi", "on" if on else "off"]),
            ),
            False,
            False,
            0,
        )
        card.pack_start(self._make_divider(), False, False, 0)

        row_nm = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        lbl = Gtk.Label(label="Gerenciar conexões avançadas, VPN e IP estático", xalign=0)
        lbl.set_name("row-desc")
        btn = Gtk.Button(label="Abrir Conexões de Rede")
        btn.set_name("action-pill")
        btn.connect("clicked", lambda _: run_async(["nm-connection-editor"]))
        row_nm.pack_start(lbl, True, True, 0)
        row_nm.pack_end(btn, False, False, 0)
        card.pack_start(row_nm, False, False, 0)

        col.pack_start(card, False, False, 0)
        return col

    # ==========================================================================
    # 3. SOM
    # ==========================================================================
    def _build_sound_page(self):
        col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        card = self._make_card()

        row_vol = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        v_txt = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        lbl_t = Gtk.Label(label="Volume principal de saída", xalign=0)
        lbl_t.set_name("row-title")
        lbl_d = Gtk.Label(label="Ajuste o nível de áudio dos alto-falantes ou fones", xalign=0)
        lbl_d.set_name("row-desc")
        v_txt.pack_start(lbl_t, False, False, 0)
        v_txt.pack_start(lbl_d, False, False, 0)
        row_vol.pack_start(v_txt, True, True, 0)

        vol_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 2)
        vol_scale.set_value(75)
        vol_scale.set_draw_value(False)
        vol_scale.set_size_request(240, -1)
        vol_scale.connect("value-changed", lambda s: run_async(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{int(s.get_value())}%"]))
        row_vol.pack_end(vol_scale, False, False, 0)
        card.pack_start(row_vol, False, False, 0)

        card.pack_start(self._make_divider(), False, False, 0)
        row_mixer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        lbl_m = Gtk.Label(label="Selecionar dispositivos de entrada, microfone e perfis HDMI", xalign=0)
        lbl_m.set_name("row-desc")
        btn_m = Gtk.Button(label="Controle de Volume")
        btn_m.set_name("action-pill")
        btn_m.connect("clicked", lambda _: run_async(["pavucontrol"]))
        row_mixer.pack_start(lbl_m, True, True, 0)
        row_mixer.pack_end(btn_m, False, False, 0)
        card.pack_start(row_mixer, False, False, 0)

        col.pack_start(card, False, False, 0)
        self.searchable_items.append(("som", "volume audio som microfone alto falante"))
        return col

    # ==========================================================================
    # 4. NOTIFICAÇÕES
    # ==========================================================================
    def _build_notifications_page(self):
        col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        card = self._make_card()

        card.pack_start(
            self._make_switch_row(
                "notificacoes",
                "notifications-disabled-symbolic",
                "Modo Não Perturbe",
                "Silenciar avisos flutuantes na área de trabalho",
                self.state["dnd"],
                self._on_toggle_dnd,
            ),
            False,
            False,
            0,
        )
        col.pack_start(card, False, False, 0)
        return col

    def _on_toggle_dnd(self, active):
        self.state["dnd"] = active
        self._save_state()
        val = "true" if active else "false"
        run_async(["xfconf-query", "-c", "xfce4-notifyd", "-p", "/do-not-disturb", "-n", "-t", "bool", "-s", val])

    # ==========================================================================
    # 5. CONTAS
    # ==========================================================================
    def _build_accounts_page(self):
        col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        card = self._make_card()

        user = os.environ.get("USER", "usuario")
        host = socket.gethostname()

        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        avatar = Gtk.Image()
        face_path = os.path.expanduser("~/.face")
        if not os.path.isfile(face_path):
            face_path = "/usr/share/pixmaps/legacyos-avatar.png"
        if os.path.isfile(face_path):
            from gi.repository import GdkPixbuf
            pb = GdkPixbuf.Pixbuf.new_from_file_at_scale(face_path, 48, 48, True)
            avatar.set_from_pixbuf(pb)
        row.pack_start(avatar, False, False, 0)

        info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        lbl_u = Gtk.Label(label=f"{user} ({host})", xalign=0)
        lbl_u.set_name("row-title")
        lbl_r = Gtk.Label(label="Administrador local • Sessão LegacyOS Desktop", xalign=0)
        lbl_r.set_name("row-desc")
        info.pack_start(lbl_u, False, False, 0)
        info.pack_start(lbl_r, False, False, 0)
        row.pack_start(info, True, True, 0)

        card.pack_start(row, False, False, 0)
        col.pack_start(card, False, False, 0)
        self.searchable_items.append(("contas", "usuario conta perfil senha administrador"))
        return col

    # ==========================================================================
    # 6. PRIVACIDADE
    # ==========================================================================
    def _build_privacy_page(self):
        col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        card = self._make_card()

        card.pack_start(
            self._make_switch_row(
                "privacidade",
                "system-lock-screen-symbolic",
                "Bloqueio automático de tela",
                "Exigir senha ao retornar da suspensão",
                self.state["auto_lock"],
                self._on_toggle_lock,
            ),
            False,
            False,
            0,
        )
        col.pack_start(card, False, False, 0)
        return col

    def _on_toggle_lock(self, active):
        self.state["auto_lock"] = active
        self._save_state()
        val = "true" if active else "false"
        run_async(["xfconf-query", "-c", "xfce4-session", "-p", "/shutdown/LockScreen", "-n", "-t", "bool", "-s", val])

    # ==========================================================================
    # 7. SOBRE
    # ==========================================================================
    def _build_about_page(self):
        col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        card = self._make_card()

        cpu = run_cmd(["bash", "-c", "lscpu | awk -F: '/Model name/ {gsub(/^[ \\t]+/, \"\", $2); print $2; exit}'"]) or platform.processor() or "Processador x86_64"
        ram = run_cmd(["bash", "-c", "free -h | awk '/Mem:/ {print $2}'"]) or "2.0 GiB"
        kernel = platform.release()

        specs = [
            ("Sistema operacional", "LegacyOS 1.0 (Base Debian Bookworm Otimizada)"),
            ("Ambiente gráfico", "LegacyOS Desktop (XFCE 4.18 + Compositor Leve)"),
            ("Processador", cpu),
            ("Memória RAM", f"{ram} (com compressão zRAM ativa)"),
            ("Kernel Linux", kernel),
        ]

        for idx, (k, v) in enumerate(specs):
            if idx > 0:
                card.pack_start(self._make_divider(), False, False, 0)
            r = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            lk = Gtk.Label(label=k, xalign=0)
            lk.set_name("row-title")
            lv = Gtk.Label(label=v, xalign=1)
            lv.set_name("row-desc")
            r.pack_start(lk, True, True, 0)
            r.pack_end(lv, False, False, 0)
            card.pack_start(r, False, False, 0)

        col.pack_start(card, False, False, 0)
        self.searchable_items.append(("sobre", "sobre versao hardware memoria ram processador kernel"))
        return col

    # ==========================================================================
    # NAVEGAÇÃO E BUSCA
    # ==========================================================================
    def _select_category(self, cat_id):
        if cat_id not in self.nav_buttons:
            return
        self.stack.set_visible_child_name(cat_id)
        for cid, btn in self.nav_buttons.items():
            btn.set_name("nav-item-active" if cid == cat_id else "nav-item")

    def _on_search_changed(self, entry):
        query = entry.get_text().strip().lower()
        if not query:
            return
        for cat_id, keywords in self.searchable_items:
            if query in keywords:
                self._select_category(cat_id)
                break


def main():
    win = LegacySettingsWindow()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
