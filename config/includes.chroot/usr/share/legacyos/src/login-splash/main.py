#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LegacyOS Login Splash Screen
Exibe cortina de inicialização em tela cheia enquanto o desktop é preparado.
Consome 0 MB de RAM após o carregamento (encerra automaticamente ao concluir).
"""

import math
import os
import time
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib  # noqa: E402
import cairo  # noqa: E402


LOCK_FILE = "/tmp/legacyos-splash.lock"
LOGO_PATH = "/usr/share/pixmaps/legacyos-logo.svg"
FLAG_DIR = os.path.expanduser("~/.config/legacyos")
FIRST_LOGIN_FLAG = os.path.join(FLAG_DIR, ".first_login_done")

MIN_DISPLAY_SECONDS = 4.2
MAX_TIMEOUT_SECONDS = 14.0


def resolve_boot_messages():
    """Define a mensagem principal conforme seja o primeiro login ou subsequente."""
    is_first_login = not os.path.exists(FIRST_LOGIN_FLAG)
    if is_first_login:
        try:
            os.makedirs(FLAG_DIR, exist_ok=True)
            with open(FIRST_LOGIN_FLAG, "w", encoding="utf-8") as flag_file:
                flag_file.write(f"initialized={int(time.time())}\n")
        except OSError:
            pass
        return (
            "Seu equipamento ganhando nova vida...",
            "Otimizando desempenho, memória e interface para você",
        )

    return (
        "Iniciando o sistema LegacyOS...",
        "Preparando sua área de trabalho",
    )


class LegacyLoginSplash(Gtk.Window):
    def __init__(self):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)

        self.primary_msg, self.secondary_msg = resolve_boot_messages()
        self.start_time = time.monotonic()
        self.progress_value = 0.08
        self.fading_out = False
        self.opacity_level = 1.0

        # Configuração de janela em tela cheia acima de painéis e docks
        self.set_title("LegacyOS Startup")
        self.set_decorated(False)
        self.set_keep_above(True)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_type_hint(Gdk.WindowTypeHint.SPLASHSCREEN)

        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual is not None and screen.is_composited():
            self.set_visual(visual)
        self.set_app_paintable(True)

        display = Gdk.Display.get_default()
        monitor = display.get_primary_monitor() if display else None
        if monitor:
            geom = monitor.get_geometry()
            self.screen_w = geom.width
            self.screen_h = geom.height
            self.move(geom.x, geom.y)
        else:
            self.screen_w = screen.get_width()
            self.screen_h = screen.get_height()

        self.set_default_size(self.screen_w, self.screen_h)
        self.fullscreen()

        self.is_compact = self.screen_h <= 650
        logo_size = 92 if self.is_compact else 118
        self.logo_pixbuf = None
        if os.path.isfile(LOGO_PATH):
            try:
                self.logo_pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                    LOGO_PATH, logo_size, logo_size, True
                )
            except Exception:
                self.logo_pixbuf = None

        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.connect("draw", self.on_draw)
        self.add(self.drawing_area)

        GLib.timeout_add(33, self.on_tick)

    def _draw_fallback_logo(self, ctx, cx, cy, size):
        half = size / 2.0
        x0 = cx - half + 10
        y0 = cy - half + 8
        w = size - 20
        h = size - 16

        ctx.save()
        grad_v = cairo.LinearGradient(x0, y0, x0, y0 + h)
        grad_v.add_color_stop_rgb(0.0, 0.22, 0.74, 0.97)
        grad_v.add_color_stop_rgb(1.0, 0.01, 0.52, 0.78)
        ctx.set_source(grad_v)
        ctx.rectangle(x0, y0, w * 0.34, h)
        ctx.fill()

        grad_h = cairo.LinearGradient(x0, y0 + h, x0 + w, y0 + h)
        grad_h.add_color_stop_rgb(0.0, 0.58, 0.64, 0.72)
        grad_h.add_color_stop_rgb(1.0, 0.97, 0.98, 0.99)
        ctx.set_source(grad_h)
        ctx.rectangle(x0, y0 + h * 0.72, w, h * 0.28)
        ctx.fill()
        ctx.restore()

    def on_draw(self, widget, ctx):
        width = widget.get_allocated_width()
        height = widget.get_allocated_height()
        cx = width / 2.0
        cy = height / 2.0

        # 1. Fundo Dark Slate (#0B1120) com brilho radial central sutil
        ctx.set_source_rgb(0.043, 0.067, 0.125)
        ctx.rectangle(0, 0, width, height)
        ctx.fill()

        radial = cairo.RadialGradient(cx, cy - 30, 10, cx, cy - 30, max(width, height) * 0.55)
        radial.add_color_stop_rgba(0.0, 0.008, 0.518, 0.780, 0.16)
        radial.add_color_stop_rgba(0.6, 0.059, 0.090, 0.165, 0.06)
        radial.add_color_stop_rgba(1.0, 0.043, 0.067, 0.125, 0.0)
        ctx.set_source(radial)
        ctx.rectangle(0, 0, width, height)
        ctx.fill()

        # 2. Logotipo Central do LegacyOS
        offset_y = -68 if self.is_compact else -84
        if self.logo_pixbuf is not None:
            pw = self.logo_pixbuf.get_width()
            ph = self.logo_pixbuf.get_height()
            Gdk.cairo_set_source_pixbuf(ctx, self.logo_pixbuf, cx - pw / 2.0, cy + offset_y - ph / 2.0)
            ctx.paint()
        else:
            self._draw_fallback_logo(ctx, cx, cy + offset_y, 96)

        # 3. Marca "LegacyOS"
        brand_y = cy + (2 if self.is_compact else 8)
        ctx.select_font_face("Geist", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(24 if self.is_compact else 30)

        legacy_text = "Legacy"
        os_text = "OS"
        ext_legacy = ctx.text_extents(legacy_text)
        ext_os = ctx.text_extents(os_text)
        total_brand_w = ext_legacy.width + ext_os.width + 2
        start_brand_x = cx - total_brand_w / 2.0

        ctx.set_source_rgb(0.973, 0.980, 0.988)
        ctx.move_to(start_brand_x, brand_y)
        ctx.show_text(legacy_text)

        ctx.set_source_rgb(0.055, 0.647, 0.914)
        ctx.move_to(start_brand_x + ext_legacy.width + 2, brand_y)
        ctx.show_text(os_text)

        # 4. Barra de progresso animada minimalista
        bar_w = 240 if self.is_compact else 290
        bar_h = 4
        bar_x = cx - bar_w / 2.0
        bar_y = brand_y + (24 if self.is_compact else 30)
        radius = bar_h / 2.0

        ctx.set_source_rgba(1.0, 1.0, 1.0, 0.12)
        self._rounded_rect(ctx, bar_x, bar_y, bar_w, bar_h, radius)
        ctx.fill()

        fill_w = max(16.0, bar_w * min(1.0, self.progress_value))
        grad_bar = cairo.LinearGradient(bar_x, bar_y, bar_x + fill_w, bar_y)
        grad_bar.add_color_stop_rgb(0.0, 0.008, 0.518, 0.780)
        grad_bar.add_color_stop_rgb(1.0, 0.220, 0.741, 0.973)
        ctx.set_source(grad_bar)
        self._rounded_rect(ctx, bar_x, bar_y, fill_w, bar_h, radius)
        ctx.fill()

        # 5. Frase principal dinâmica
        msg_y = bar_y + (32 if self.is_compact else 38)
        ctx.select_font_face("Geist", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(14 if self.is_compact else 16)
        ext_msg = ctx.text_extents(self.primary_msg)
        ctx.set_source_rgb(0.945, 0.961, 0.976)
        ctx.move_to(cx - ext_msg.width / 2.0, msg_y)
        ctx.show_text(self.primary_msg)

        # 6. Subtítulo discreto
        sub_y = msg_y + (22 if self.is_compact else 25)
        ctx.select_font_face("Geist", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        ctx.set_font_size(11 if self.is_compact else 12)
        ext_sub = ctx.text_extents(self.secondary_msg)
        ctx.set_source_rgb(0.580, 0.639, 0.722)
        ctx.move_to(cx - ext_sub.width / 2.0, sub_y)
        ctx.show_text(self.secondary_msg)

        return False

    @staticmethod
    def _rounded_rect(ctx, x, y, w, h, r):
        ctx.new_sub_path()
        ctx.arc(x + w - r, y + r, r, -math.pi / 2.0, 0)
        ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2.0)
        ctx.arc(x + r, y + h - r, r, math.pi / 2.0, math.pi)
        ctx.arc(x + r, y + r, r, math.pi, 3.0 * math.pi / 2.0)
        ctx.close_path()

    def on_tick(self):
        # Mantém a janela no topo caso o painel ou a dock recém-iniciados tentem sobrepor
        if not self.fading_out:
            self.present()

        elapsed = time.monotonic() - self.start_time
        lock_exists = os.path.exists(LOCK_FILE)

        if lock_exists and elapsed < MAX_TIMEOUT_SECONDS:
            target = min(0.92, 0.12 + (elapsed / 5.5) * 0.80)
            self.progress_value += (target - self.progress_value) * 0.15
            self.drawing_area.queue_draw()
            return True

        self.progress_value += (1.0 - self.progress_value) * 0.35

        if elapsed >= MIN_DISPLAY_SECONDS and self.progress_value >= 0.98:
            self.fading_out = True

        if self.fading_out:
            self.opacity_level -= 0.12
            if self.opacity_level <= 0.0:
                Gtk.main_quit()
                return False
            self.set_opacity(max(0.0, self.opacity_level))

        self.drawing_area.queue_draw()
        return True


def main():
    win = LegacyLoginSplash()
    win.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
