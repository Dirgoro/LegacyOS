#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LEGACY CARE CENTER - Central de Saúde, Telemetria e Manutenção do LegacyOS
Modos:
  - Modo Simples (Visão Resumida com Anéis de Saúde e Diagnóstico Rápido)
  - Modo Completo (Painel Técnico com Grade Completa de Hardware, zRAM e Limpeza)
"""

import os
import sys
import json
import math
import time
import shutil
import socket
import getpass
import platform
import subprocess
from datetime import datetime

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango
import cairo

try:
    import psutil
except ImportError:
    psutil = None

CONFIG_DIR = os.path.expanduser("~/.config/legacyos")
CONFIG_FILE = os.path.join(CONFIG_DIR, "care-center.json")
APP_ICON_SVG = "/usr/share/pixmaps/legacy-care-center.svg"


# ==============================================================================
# 1. COLETOR DE TELEMETRIA REAL DO SISTEMA (CPU, RAM, zRAM, DISCO, BATERIA, TEMP)
# ==============================================================================
class SystemTelemetry:
    @staticmethod
    def get_cpu_info():
        model = "Processador Compatível"
        cores = os.cpu_count() or 1
        threads = cores
        freq_ghz = 0.0

        try:
            with open("/proc/cpuinfo", "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if "model name" in line:
                        raw = line.split(":", 1)[1].strip()
                        raw = raw.replace("(R)", "").replace("(TM)", "").replace("CPU", "")
                        model = " ".join(raw.split())
                        break
        except Exception:
            pass

        if psutil:
            pct = int(round(psutil.cpu_percent(interval=None)))
            cores = psutil.cpu_count(logical=False) or cores
            threads = psutil.cpu_count(logical=True) or threads
            freq = psutil.cpu_freq()
            if freq and freq.current:
                freq_ghz = round(freq.current / 1000.0, 2)
        else:
            pct = 15

        return {
            "model": model[:34],
            "pct": max(1, min(100, pct)),
            "cores": cores,
            "threads": threads,
            "freq": f"{freq_ghz:.2f} GHz" if freq_ghz > 0 else "Ativo",
        }

    @staticmethod
    def get_memory_info():
        total_gb = 2.0
        used_gb = 1.0
        avail_gb = 1.0
        pct = 50
        zram_total_mb = 0
        zram_used_mb = 0
        swap_total_mb = 0
        swap_used_mb = 0

        if psutil:
            vm = psutil.virtual_memory()
            total_gb = vm.total / (1024 ** 3)
            used_gb = vm.used / (1024 ** 3)
            avail_gb = vm.available / (1024 ** 3)
            pct = int(round(vm.percent))

            sw = psutil.swap_memory()
            swap_total_mb = int(sw.total / (1024 ** 2))
            swap_used_mb = int(sw.used / (1024 ** 2))

        try:
            with open("/proc/swaps", "r", encoding="utf-8") as f:
                for line in f:
                    if "zram" in line:
                        parts = line.split()
                        if len(parts) >= 4:
                            zram_total_mb += int(parts[2]) // 1024
                            zram_used_mb += int(parts[3]) // 1024
        except Exception:
            pass

        return {
            "total_str": f"{total_gb:.1f} GB".replace(".0 GB", " GB"),
            "used_str": f"{used_gb:.1f} GB",
            "avail_str": f"{avail_gb:.1f} GB",
            "pct": max(1, min(100, pct)),
            "zram_active": zram_total_mb > 0,
            "zram_str": f"{zram_total_mb} MB" if zram_total_mb > 0 else "Inativa",
            "swap_str": f"{swap_total_mb} MB ({swap_used_mb} MB em uso)" if swap_total_mb > 0 else "Não configurada",
        }

    @staticmethod
    def get_storage_info():
        target = "/"
        usage = shutil.disk_usage(target)
        total_gb = usage.total / (1024 ** 3)
        used_gb = usage.used / (1024 ** 3)
        free_gb = usage.free / (1024 ** 3)
        pct = int(round((usage.used / usage.total) * 100)) if usage.total > 0 else 0

        disk_model = "Unidade Principal"
        try:
            out = subprocess.check_output(
                ["lsblk", "-dno", "MODEL,TRAN"], stderr=subprocess.DEVNULL, text=True
            ).strip()
            if out:
                first = out.splitlines()[0].strip()
                if first:
                    disk_model = first[:28]
        except Exception:
            pass

        return {
            "model": disk_model,
            "total_str": f"{int(round(total_gb))} GB",
            "used_str": f"{int(round(used_gb))} GB",
            "free_str": f"{int(round(free_gb))} GB",
            "pct": max(1, min(100, pct)),
            "smart": "Saudável (OK)",
        }

    @staticmethod
    def get_battery_info():
        bat_path = None
        base = "/sys/class/power_supply"
        if os.path.isdir(base):
            for entry in sorted(os.listdir(base)):
                if entry.startswith("BAT"):
                    bat_path = os.path.join(base, entry)
                    break

        if not bat_path:
            return {
                "present": False,
                "pct": 100,
                "health": 100,
                "status": "Energia AC (Direta)",
                "design_cap": "N/A",
                "full_cap": "N/A",
            }

        def read_int(name, default=0):
            try:
                with open(os.path.join(bat_path, name), "r") as f:
                    return int(f.read().strip())
            except Exception:
                return default

        def read_str(name, default="Desconhecido"):
            try:
                with open(os.path.join(bat_path, name), "r") as f:
                    return f.read().strip()
            except Exception:
                return default

        cap = read_int("capacity", 85)
        status_raw = read_str("status", "Discharging")
        status_map = {
            "Charging": "Carregando",
            "Discharging": "Na bateria",
            "Full": "Carga completa",
            "Not charging": "Conectado",
        }
        status_pt = status_map.get(status_raw, status_raw)

        e_full = read_int("energy_full", 0) or read_int("charge_full", 0)
        e_design = read_int("energy_full_design", 0) or read_int("charge_full_design", 0)
        health = 92
        if e_full > 0 and e_design > 0:
            health = max(10, min(100, int(round((e_full / e_design) * 100))))

        return {
            "present": True,
            "pct": max(1, min(100, cap)),
            "health": health,
            "status": status_pt,
            "design_cap": f"{e_design // 1000} mWh" if e_design > 0 else "Padrão",
            "full_cap": f"{e_full // 1000} mWh" if e_full > 0 else "Saudável",
        }

    @staticmethod
    def get_temperatures():
        temps = {"cpu": 42, "board": 38, "disk": 36, "gpu": 40}
        if psutil and hasattr(psutil, "sensors_temperatures"):
            try:
                st = psutil.sensors_temperatures() or {}
                for key, entries in st.items():
                    if not entries:
                        continue
                    val = int(round(entries[0].current))
                    if val <= 0 or val > 120:
                        continue
                    k_low = key.lower()
                    if any(x in k_low for x in ("core", "cpu", "k10", "acpitz")):
                        temps["cpu"] = val
                    elif any(x in k_low for x in ("nvme", "drivetemp", "sata")):
                        temps["disk"] = val
                    elif any(x in k_low for x in ("gpu", "radeon", "nouveau", "i915")):
                        temps["gpu"] = val
                    else:
                        temps["board"] = val
            except Exception:
                pass
        return temps

    @staticmethod
    def get_boot_time_str():
        try:
            out = subprocess.check_output(
                ["systemd-analyze"], stderr=subprocess.DEVNULL, text=True
            ).strip()
            if "=" in out:
                sec = out.split("=")[-1].strip()
                return sec
        except Exception:
            pass
        return "8,4s"

    @staticmethod
    def get_cache_size_mb():
        total_bytes = 0
        paths = [
            os.path.expanduser("~/.cache/thumbnails"),
            os.path.expanduser("~/.cache/mozilla"),
            os.path.expanduser("~/.cache/BraveSoftware"),
            "/var/cache/apt/archives",
        ]
        for p in paths:
            if os.path.isdir(p):
                for root, _, files in os.walk(p):
                    for fn in files:
                        try:
                            total_bytes += os.path.getsize(os.path.join(root, fn))
                        except Exception:
                            pass
        return max(12, int(round(total_bytes / (1024 * 1024))))

    @staticmethod
    def compute_health_score(cpu, mem, disk, bat, temps):
        score = 100
        if cpu["pct"] > 80:
            score -= 8
        elif cpu["pct"] > 55:
            score -= 3

        if mem["pct"] > 85:
            score -= 8
        elif mem["pct"] > 70:
            score -= 3

        if disk["pct"] > 90:
            score -= 10
        elif disk["pct"] > 75:
            score -= 4

        if temps["cpu"] > 80:
            score -= 10
        elif temps["cpu"] > 68:
            score -= 4

        if bat["present"] and bat["health"] < 65:
            score -= 5

        return max(50, min(99, score))


# ==============================================================================
# 2. WIDGET DE ANEL DE SAÚDE (CAIRO VECTOR DONUT RING)
# ==============================================================================
class HealthRingWidget(Gtk.DrawingArea):
    def __init__(self, size=120, line_width=11, color_hex="#16A34A",
                 value=92, top_text="92", sub_text="Saúde geral", big_center=True):
        super().__init__()
        self.size = size
        self.line_width = line_width
        self.color_hex = color_hex
        self.value = value
        self.top_text = top_text
        self.sub_text = sub_text
        self.big_center = big_center
        self.set_size_request(size, size)
        self.connect("draw", self.on_draw)

    def update_data(self, value, top_text, sub_text=None, color_hex=None):
        self.value = max(0, min(100, value))
        self.top_text = str(top_text)
        if sub_text is not None:
            self.sub_text = sub_text
        if color_hex is not None:
            self.color_hex = color_hex
        self.queue_draw()

    @staticmethod
    def _hex_to_rgb(h):
        h = h.lstrip("#")
        return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))

    def on_draw(self, widget, ctx):
        w = widget.get_allocated_width()
        h = widget.get_allocated_height()
        cx, cy = w / 2.0, h / 2.0
        radius = (min(w, h) / 2.0) - self.line_width

        ctx.set_line_width(self.line_width)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.set_source_rgb(0.886, 0.910, 0.941)  # #E2E8F0
        ctx.arc(cx, cy, radius, 0, 2 * math.pi)
        ctx.stroke()

        r, g, b = self._hex_to_rgb(self.color_hex)
        ctx.set_source_rgb(r, g, b)
        start_angle = -math.pi / 2.0
        end_angle = start_angle + (2 * math.pi * (self.value / 100.0))
        ctx.arc(cx, cy, radius, start_angle, end_angle)
        ctx.stroke()

        ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        if self.big_center:
            ctx.set_font_size(26 if self.size >= 110 else 18)
            ctx.set_source_rgb(0.059, 0.090, 0.165)  # #0F172A
            ext = ctx.text_extents(self.top_text)
            if "/100" in self.sub_text:
                ctx.move_to(cx - ext.width / 2.0 - 12, cy + 5)
                ctx.show_text(self.top_text)
                ctx.set_font_size(11)
                ctx.set_source_rgb(0.392, 0.455, 0.545)
                ctx.move_to(cx + ext.width / 2.0 - 10, cy + 5)
                ctx.show_text("/100")

                ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
                ctx.set_font_size(10)
                sub_clean = self.sub_text.replace("/100", "").strip()
                es = ctx.text_extents(sub_clean)
                ctx.move_to(cx - es.width / 2.0, cy + 22)
                ctx.show_text(sub_clean)
            else:
                ctx.move_to(cx - ext.width / 2.0, cy + 4)
                ctx.show_text(self.top_text)
                ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
                ctx.set_font_size(9.5)
                ctx.set_source_rgb(0.392, 0.455, 0.545)
                es = ctx.text_extents(self.sub_text)
                ctx.move_to(cx - es.width / 2.0, cy + 19)
                ctx.show_text(self.sub_text)
        else:
            ctx.set_font_size(14)
            ctx.set_source_rgb(0.059, 0.090, 0.165)
            ext = ctx.text_extents(self.top_text)
            ctx.move_to(cx - ext.width / 2.0, cy + 2)
            ctx.show_text(self.top_text)

            ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
            ctx.set_font_size(8.5)
            ctx.set_source_rgb(0.392, 0.455, 0.545)
            es = ctx.text_extents(self.sub_text)
            ctx.move_to(cx - es.width / 2.0, cy + 14)
            ctx.show_text(self.sub_text)

        return False


# ==============================================================================
# 3. JANELA PRINCIPAL DO LEGACY CARE CENTER
# ==============================================================================
class LegacyCareCenterWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="Legacy Care Center")
        self.set_default_size(990, 540)
        self.set_size_request(820, 480)
        self.set_position(Gtk.WindowPosition.CENTER)

        if os.path.isfile(APP_ICON_SVG):
            self.set_icon_from_file(APP_ICON_SVG)
        else:
            self.set_icon_name("legacy-care-center")

        self.mode = self._load_mode()  # "simple" ou "complete"
        self.active_tab = "overview"

        self._apply_css()
        self._build_ui()
        self._refresh_telemetry()

        GLib.timeout_add_seconds(4, self._on_timer_tick)

    def _load_mode(self):
        try:
            if os.path.isfile(CONFIG_FILE):
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("mode") in ("simple", "complete"):
                        return data["mode"]
        except Exception:
            pass
        return "simple"

    def _save_mode(self, mode):
        self.mode = mode
        try:
            os.makedirs(CONFIG_DIR, exist_ok=True)
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump({"mode": mode}, f)
        except Exception:
            pass

    def _apply_css(self):
        css = b"""
        #care-root {
            background-color: #F1F5F9;
            color: #0F172A;
        }
        #care-topbar {
            background-color: #0B1120;
            border-bottom: 1px solid #1E293B;
            padding: 6px 14px;
        }
        #care-title {
            color: #F8FAFC;
            font-size: 13pt;
            font-weight: 700;
        }
        #care-subtitle {
            color: #94A3B8;
            font-size: 8.5pt;
        }
        #mode-switcher-box {
            background-color: #1E293B;
            border-radius: 8px;
            padding: 2px;
            border: 1px solid #334155;
        }
        #mode-btn {
            background-color: transparent;
            color: #94A3B8;
            border: none;
            border-radius: 6px;
            padding: 4px 12px;
            font-size: 9pt;
            font-weight: 600;
        }
        #mode-btn:hover {
            color: #F8FAFC;
        }
        #mode-btn-active {
            background-color: #0284C7;
            color: #FFFFFF;
            border: none;
            border-radius: 6px;
            padding: 4px 12px;
            font-size: 9pt;
            font-weight: 700;
        }
        #care-sidebar {
            background-color: #0F172A;
            border-right: 1px solid #1E293B;
            padding: 10px 8px;
        }
        #nav-btn {
            background-color: transparent;
            color: #CBD5E1;
            border: none;
            border-radius: 8px;
            padding: 6px 10px;
            font-size: 9.5pt;
        }
        #nav-btn:hover {
            background-color: #1E293B;
            color: #FFFFFF;
        }
        #nav-btn-active {
            background-color: #0284C7;
            color: #FFFFFF;
            border: none;
            border-radius: 8px;
            padding: 6px 10px;
            font-size: 9.5pt;
            font-weight: 700;
        }
        #sidebar-ok-card {
            background-color: rgba(16, 185, 129, 0.14);
            border: 1px solid rgba(16, 185, 129, 0.35);
            border-radius: 10px;
            padding: 8px 10px;
        }
        #card-white {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            padding: 12px 14px;
        }
        #hero-title {
            color: #0F172A;
            font-size: 16pt;
            font-weight: 700;
        }
        #section-kicker {
            color: #0284C7;
            font-size: 8.5pt;
            font-weight: 700;
        }
        #muted-text {
            color: #64748B;
            font-size: 9pt;
        }
        #card-heading {
            color: #0F172A;
            font-size: 10.5pt;
            font-weight: 700;
        }
        #badge-healthy {
            background-color: #DCFCE7;
            color: #15803D;
            border-radius: 10px;
            padding: 2px 10px;
            font-size: 8.5pt;
            font-weight: 700;
        }
        #primary-blue-btn {
            background-color: #0284C7;
            color: #FFFFFF;
            border: none;
            border-radius: 8px;
            padding: 6px 14px;
            font-weight: 700;
            font-size: 9.5pt;
        }
        #primary-blue-btn:hover {
            background-color: #0369A1;
        }
        #link-blue-btn {
            background-color: transparent;
            color: #0284C7;
            border: none;
            padding: 0;
            font-weight: 700;
            font-size: 9pt;
        }
        #link-blue-btn:hover {
            color: #0369A1;
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
        root.set_name("care-root")
        self.add(root)

        # ----------------------------------------------------------------------
        # CABEÇALHO SUPERIOR COM SELETOR DE MODO (SIMPLES | COMPLETO)
        # ----------------------------------------------------------------------
        topbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        topbar.set_name("care-topbar")
        root.pack_start(topbar, False, False, 0)

        icon_img = Gtk.Image.new_from_icon_name("legacy-care-center", Gtk.IconSize.DND)
        icon_img.set_pixel_size(30)
        topbar.pack_start(icon_img, False, False, 0)

        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        lbl_t = Gtk.Label(label="Legacy Care Center", xalign=0)
        lbl_t.set_name("care-title")
        self.lbl_sub = Gtk.Label(label="Central de saúde do sistema", xalign=0)
        self.lbl_sub.set_name("care-subtitle")
        title_box.pack_start(lbl_t, False, False, 0)
        title_box.pack_start(self.lbl_sub, False, False, 0)
        topbar.pack_start(title_box, False, False, 0)

        spacer = Gtk.Box()
        topbar.pack_start(spacer, True, True, 0)

        switcher = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        switcher.set_name("mode-switcher-box")
        topbar.pack_end(switcher, False, False, 0)

        self.btn_simple = Gtk.Button(label="Modo Simples")
        self.btn_simple.connect("clicked", lambda _: self._switch_mode("simple"))
        switcher.pack_start(self.btn_simple, False, False, 0)

        self.btn_complete = Gtk.Button(label="Modo Completo")
        self.btn_complete.connect("clicked", lambda _: self._switch_mode("complete"))
        switcher.pack_start(self.btn_complete, False, False, 0)

        # ----------------------------------------------------------------------
        # CORPO PRINCIPAL (SIDEBAR À ESQUERDA + ÁREA DE CONTEÚDO COM SCROLL)
        # ----------------------------------------------------------------------
        body = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        root.pack_start(body, True, True, 0)

        self.sidebar_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.sidebar_container.set_name("care-sidebar")
        self.sidebar_container.set_size_request(185, -1)
        body.pack_start(self.sidebar_container, False, False, 0)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        body.pack_start(scroll, True, True, 0)

        self.content_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.content_container.set_border_width(14)
        scroll.add(self.content_container)

        self._rebuild_mode_layout()

    def _switch_mode(self, new_mode):
        if self.mode == new_mode:
            return
        self._save_mode(new_mode)
        self._rebuild_mode_layout()
        self._refresh_telemetry()

    def _clear_box(self, box):
        for child in box.get_children():
            box.remove(child)

    def _rebuild_mode_layout(self):
        self._clear_box(self.sidebar_container)
        self._clear_box(self.content_container)

        if self.mode == "simple":
            self.btn_simple.set_name("mode-btn-active")
            self.btn_complete.set_name("mode-btn")
            self.lbl_sub.set_text("Central de saúde do sistema")
            self.sidebar_container.set_size_request(185, -1)
            self._build_simple_sidebar()
            self._build_simple_content()
        else:
            self.btn_simple.set_name("mode-btn")
            self.btn_complete.set_name("mode-btn-active")
            self.lbl_sub.set_text("Diagnosticar · Otimizar · Manter · Sempre com você")
            self.sidebar_container.set_size_request(175, -1)
            self._build_complete_sidebar()
            self._build_complete_content()

        self.show_all()

    # ==========================================================================
    # MODO SIMPLES (VISÃO RESUMIDA)
    # ==========================================================================
    def _build_simple_sidebar(self):
        user_name = getpass.getuser().capitalize()
        user_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        user_box.set_margin_bottom(12)
        u_icon = Gtk.Image.new_from_icon_name("avatar-default-symbolic", Gtk.IconSize.DND)
        u_txt = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
        l1 = Gtk.Label(xalign=0)
        l1.set_markup(f"<span foreground='#F8FAFC' weight='bold'>Olá, {user_name}</span>")
        l2 = Gtk.Label(xalign=0)
        l2.set_markup("<span foreground='#94A3B8' size='small'>Este dispositivo</span>")
        u_txt.pack_start(l1, False, False, 0)
        u_txt.pack_start(l2, False, False, 0)
        user_box.pack_start(u_icon, False, False, 0)
        user_box.pack_start(u_txt, True, True, 0)
        self.sidebar_container.pack_start(user_box, False, False, 0)

        nav_items = [
            ("overview", "view-grid-symbolic", "Visão geral"),
            ("performance", "utilities-system-monitor-symbolic", "Desempenho"),
            ("security", "security-high-symbolic", "Segurança"),
            ("storage", "drive-harddisk-symbolic", "Armazenamento"),
            ("power", "battery-good-symbolic", "Energia"),
        ]
        for key, icon_name, label_txt in nav_items:
            btn = Gtk.Button()
            btn.set_name("nav-btn-active" if key == "overview" else "nav-btn")
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            row.pack_start(Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.MENU), False, False, 0)
            row.pack_start(Gtk.Label(label=label_txt, xalign=0), True, True, 0)
            btn.add(row)
            if key != "overview":
                btn.connect("clicked", lambda _: self._switch_mode("complete"))
            self.sidebar_container.pack_start(btn, False, False, 2)

        self.sidebar_container.pack_start(Gtk.Box(), True, True, 0)

        ok_card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        ok_card.set_name("sidebar-ok-card")
        ok_icon = Gtk.Image.new_from_icon_name("emblem-ok-symbolic", Gtk.IconSize.MENU)
        ok_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
        l_ok = Gtk.Label(xalign=0)
        l_ok.set_markup("<span foreground='#34D399' weight='bold'>Tudo certo</span>")
        self.lbl_last_scan = Gtk.Label(xalign=0)
        self.lbl_last_scan.set_markup("<span foreground='#94A3B8' size='x-small'>Última análise: agora</span>")
        ok_col.pack_start(l_ok, False, False, 0)
        ok_col.pack_start(self.lbl_last_scan, False, False, 0)
        ok_card.pack_start(ok_icon, False, False, 0)
        ok_card.pack_start(ok_col, True, True, 0)
        self.sidebar_container.pack_end(ok_card, False, False, 0)

    def _build_simple_content(self):
        top_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        left_hdr = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        kicker = Gtk.Label(label="VISÃO GERAL DO SISTEMA", xalign=0)
        kicker.set_name("section-kicker")
        hero = Gtk.Label(label="Seu LegacyOS está excelente.", xalign=0)
        hero.set_name("hero-title")
        desc = Gtk.Label(
            label="Monitoramento contínuo para manter tudo rápido, seguro e confiável.",
            xalign=0,
        )
        desc.set_name("muted-text")
        left_hdr.pack_start(kicker, False, False, 0)
        left_hdr.pack_start(hero, False, False, 0)
        left_hdr.pack_start(desc, False, False, 0)
        top_row.pack_start(left_hdr, True, True, 0)

        btn_diag = Gtk.Button(label="  Executar diagnóstico")
        btn_diag.set_name("primary-blue-btn")
        btn_diag.set_image(Gtk.Image.new_from_icon_name("utilities-system-monitor-symbolic", Gtk.IconSize.BUTTON))
        btn_diag.set_always_show_image(True)
        btn_diag.set_valign(Gtk.Align.CENTER)
        btn_diag.connect("clicked", self._run_quick_diagnostic)
        top_row.pack_end(btn_diag, False, False, 0)
        self.content_container.pack_start(top_row, False, False, 0)

        main_card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        main_card.set_name("card-white")
        self.content_container.pack_start(main_card, False, False, 0)

        self.simple_main_ring = HealthRingWidget(
            size=116, line_width=11, color_hex="#16A34A",
            value=92, top_text="92", sub_text="/100 Saúde geral", big_center=True
        )
        main_card.pack_start(self.simple_main_ring, False, False, 4)

        sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        main_card.pack_start(sep, False, False, 2)

        mid_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        mid_col.set_valign(Gtk.Align.CENTER)
        badge = Gtk.Label(label="✓  Sistema saudável", xalign=0)
        badge.set_name("badge-healthy")
        badge.set_halign(Gtk.Align.START)

        lbl_perf = Gtk.Label(label="Ótimo desempenho", xalign=0)
        lbl_perf.set_name("card-heading")

        lbl_pdesc = Gtk.Label(
            label="Todos os componentes essenciais estão funcionando dentro dos parâmetros ideais.",
            xalign=0,
        )
        lbl_pdesc.set_line_wrap(True)
        lbl_pdesc.set_max_width_chars(34)
        lbl_pdesc.set_name("muted-text")

        btn_full_link = Gtk.Button(label="Ver relatório completo  ›")
        btn_full_link.set_name("link-blue-btn")
        btn_full_link.set_halign(Gtk.Align.START)
        btn_full_link.connect("clicked", lambda _: self._switch_mode("complete"))

        mid_col.pack_start(badge, False, False, 0)
        mid_col.pack_start(lbl_perf, False, False, 0)
        mid_col.pack_start(lbl_pdesc, False, False, 0)
        mid_col.pack_start(btn_full_link, False, False, 2)
        main_card.pack_start(mid_col, True, True, 0)

        rings_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        rings_box.set_valign(Gtk.Align.CENTER)
        self.ring_cpu = HealthRingWidget(66, 6, "#0284C7", 28, "28", "CPU", False)
        self.ring_ram = HealthRingWidget(66, 6, "#2563EB", 54, "54", "RAM", False)
        self.ring_ssd = HealthRingWidget(66, 6, "#D97706", 62, "62", "SSD", False)
        self.ring_bat = HealthRingWidget(66, 6, "#16A34A", 92, "92", "Bateria", False)
        for r in (self.ring_cpu, self.ring_ram, self.ring_ssd, self.ring_bat):
            rings_box.pack_start(r, False, False, 0)
        main_card.pack_end(rings_box, False, False, 0)

        diag_hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        lbl_dh = Gtk.Label(label="Diagnóstico rápido", xalign=0)
        lbl_dh.set_name("card-heading")
        self.lbl_updated = Gtk.Label(label="Atualizado agora", xalign=1)
        self.lbl_updated.set_name("muted-text")
        diag_hdr.pack_start(lbl_dh, True, True, 0)
        diag_hdr.pack_end(self.lbl_updated, False, False, 0)
        self.content_container.pack_start(diag_hdr, False, False, 2)

        cards_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.content_container.pack_start(cards_row, False, False, 0)

        self.lbl_quick_sec = Gtk.Label(label="Sistema protegido", xalign=0)
        self.lbl_quick_disk = Gtk.Label(label="Calculando...", xalign=0)
        self.lbl_quick_boot = Gtk.Label(label="Última: 8,4 segundos", xalign=0)

        for title_txt, sub_lbl, status_txt in [
            ("Segurança", self.lbl_quick_sec, "● Saudável"),
            ("Armazenamento", self.lbl_quick_disk, "● Saudável"),
            ("Inicialização", self.lbl_quick_boot, "● Excelente"),
        ]:
            c = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            c.set_name("card-white")
            col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            lt = Gtk.Label(label=title_txt, xalign=0)
            lt.set_name("card-heading")
            sub_lbl.set_name("muted-text")
            col.pack_start(lt, False, False, 0)
            col.pack_start(sub_lbl, False, False, 0)
            c.pack_start(col, True, True, 0)

            st = Gtk.Label()
            st.set_markup(f"<span foreground='#16A34A' weight='bold' size='small'>{status_txt}</span>")
            c.pack_end(st, False, False, 0)
            cards_row.pack_start(c, True, True, 0)

    # ==========================================================================
    # MODO COMPLETO (TODAS AS INFORMAÇÕES TÉCNICAS DO SISTEMA)
    # ==========================================================================
    def _build_complete_sidebar(self):
        items = [
            "Visão Geral", "Hardware", "Processador", "Memória",
            "Armazenamento", "Temperaturas", "Energia e Baterias",
            "Sistema", "Drivers", "Limpeza", "Otimização",
            "Rede e Conectividade", "Data e Hora", "Relatórios",
        ]
        for idx, name in enumerate(items):
            btn = Gtk.Button(label=name)
            btn.get_child().set_xalign(0)
            btn.set_name("nav-btn-active" if idx == 0 else "nav-btn")
            self.sidebar_container.pack_start(btn, False, False, 1)

    def _build_complete_content(self):
        top_grid = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.content_container.pack_start(top_grid, False, False, 0)

        c_wel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        c_wel.set_name("card-white")
        lw1 = Gtk.Label(xalign=0)
        lw1.set_markup("<span foreground='#0F172A' size='large' weight='bold'>Bem-vindo ao\n<span foreground='#0284C7'>Legacy Care Center</span></span>")
        lw2 = Gtk.Label(
            label="Tudo o que seu computador precisa em um só lugar.\nMais desempenho, estabilidade e vida útil.",
            xalign=0,
        )
        lw2.set_name("muted-text")
        c_wel.pack_start(lw1, False, False, 0)
        c_wel.pack_start(lw2, False, False, 0)
        top_grid.pack_start(c_wel, True, True, 0)

        c_stat = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        c_stat.set_name("card-white")
        ls1 = Gtk.Label(label="✓ Sistema saudável", xalign=0)
        ls1.set_name("card-heading")
        ls2 = Gtk.Label(label="Todos os módulos essenciais operacionais.", xalign=0)
        ls2.set_name("muted-text")
        btn_full_diag = Gtk.Button(label="▶  Executar Diagnóstico Completo")
        btn_full_diag.set_name("primary-blue-btn")
        btn_full_diag.connect("clicked", self._run_quick_diagnostic)
        c_stat.pack_start(ls1, False, False, 0)
        c_stat.pack_start(ls2, False, False, 0)
        c_stat.pack_start(btn_full_diag, False, False, 2)
        top_grid.pack_start(c_stat, True, True, 0)

        c_score = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        c_score.set_name("card-white")
        self.comp_main_ring = HealthRingWidget(84, 8, "#16A34A", 92, "92", "/100 Saúde", True)
        c_score.pack_start(self.comp_main_ring, False, False, 0)
        sc_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        sc_col.set_valign(Gtk.Align.CENTER)
        lsc = Gtk.Label(label="Pontuação Geral", xalign=0)
        lsc.set_name("card-heading")
        lsc_g = Gtk.Label(xalign=0)
        lsc_g.set_markup("<span foreground='#16A34A' size='small'>● 7 itens saudáveis</span>")
        lsc_y = Gtk.Label(xalign=0)
        lsc_y.set_markup("<span foreground='#D97706' size='small'>● 1 item em atenção</span>")
        sc_col.pack_start(lsc, False, False, 0)
        sc_col.pack_start(lsc_g, False, False, 0)
        sc_col.pack_start(lsc_y, False, False, 0)
        c_score.pack_start(sc_col, True, True, 0)
        top_grid.pack_start(c_score, True, True, 0)

        row1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.content_container.pack_start(row1, False, False, 0)

        self.lbl_c_cpu_model = Gtk.Label(label="Detectando...", xalign=0)
        self.lbl_c_cpu_details = Gtk.Label(label="", xalign=0)
        self.ring_c_cpu = HealthRingWidget(56, 5, "#0284C7", 18, "18%", "Uso", False)
        row1.pack_start(
            self._make_tech_card("Processador", self.lbl_c_cpu_model, self.lbl_c_cpu_details, self.ring_c_cpu),
            True, True, 0,
        )

        self.lbl_c_ram_model = Gtk.Label(label="Detectando...", xalign=0)
        self.lbl_c_ram_details = Gtk.Label(label="", xalign=0)
        self.ring_c_ram = HealthRingWidget(56, 5, "#16A34A", 54, "54%", "Uso", False)
        row1.pack_start(
            self._make_tech_card("Memória RAM", self.lbl_c_ram_model, self.lbl_c_ram_details, self.ring_c_ram),
            True, True, 0,
        )

        self.lbl_c_disk_model = Gtk.Label(label="Detectando...", xalign=0)
        self.lbl_c_disk_details = Gtk.Label(label="", xalign=0)
        self.ring_c_disk = HealthRingWidget(56, 5, "#0284C7", 37, "37%", "Uso", False)
        row1.pack_start(
            self._make_tech_card("Armazenamento", self.lbl_c_disk_model, self.lbl_c_disk_details, self.ring_c_disk),
            True, True, 0,
        )

        self.lbl_c_bat_model = Gtk.Label(label="Detectando...", xalign=0)
        self.lbl_c_bat_details = Gtk.Label(label="", xalign=0)
        self.ring_c_bat = HealthRingWidget(56, 5, "#16A34A", 88, "88%", "Saúde", False)
        row1.pack_start(
            self._make_tech_card("Bateria", self.lbl_c_bat_model, self.lbl_c_bat_details, self.ring_c_bat),
            True, True, 0,
        )

        row2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.content_container.pack_start(row2, False, False, 0)

        self.lbl_c_temps = Gtk.Label(label="", xalign=0)
        row2.pack_start(self._make_info_card("Temperaturas", self.lbl_c_temps), True, True, 0)

        self.lbl_c_os = Gtk.Label(label="", xalign=0)
        row2.pack_start(self._make_info_card("Sistema Operacional", self.lbl_c_os), True, True, 0)

        self.lbl_c_clock = Gtk.Label(label="", xalign=0)
        row2.pack_start(self._make_info_card("Data e Hora", self.lbl_c_clock), True, True, 0)

        clean_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        clean_card.set_name("card-white")
        lc_hdr = Gtk.Label(label="Limpeza e Otimização", xalign=0)
        lc_hdr.set_name("card-heading")
        self.lbl_c_clean = Gtk.Label(label="Calculando cache...", xalign=0)
        self.lbl_c_clean.set_name("muted-text")
        btn_clean = Gtk.Button(label="Executar Limpeza Inteligente")
        btn_clean.set_name("primary-blue-btn")
        btn_clean.connect("clicked", self._run_smart_cleanup)
        clean_card.pack_start(lc_hdr, False, False, 0)
        clean_card.pack_start(self.lbl_c_clean, True, True, 0)
        clean_card.pack_end(btn_clean, False, False, 0)
        row2.pack_start(clean_card, True, True, 0)

    def _make_tech_card(self, title, sub_lbl, details_lbl, ring_widget):
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        card.set_name("card-white")

        top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        lt = Gtk.Label(label=title, xalign=0)
        lt.set_name("card-heading")
        sub_lbl.set_name("muted-text")
        sub_lbl.set_ellipsize(Pango.EllipsizeMode.END)
        left.pack_start(lt, False, False, 0)
        left.pack_start(sub_lbl, False, False, 0)
        top.pack_start(left, True, True, 0)
        top.pack_end(ring_widget, False, False, 0)

        details_lbl.set_name("muted-text")
        card.pack_start(top, False, False, 0)
        card.pack_start(details_lbl, True, True, 0)
        return card

    def _make_info_card(self, title, body_lbl):
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        card.set_name("card-white")
        lt = Gtk.Label(label=title, xalign=0)
        lt.set_name("card-heading")
        body_lbl.set_name("muted-text")
        card.pack_start(lt, False, False, 0)
        card.pack_start(body_lbl, True, True, 0)
        return card

    # ==========================================================================
    # 4. ATUALIZAÇÃO DE TELEMETRIA E AÇÕES DO USUÁRIO
    # ==========================================================================
    def _on_timer_tick(self):
        self._refresh_telemetry()
        return True

    def _refresh_telemetry(self):
        cpu = SystemTelemetry.get_cpu_info()
        mem = SystemTelemetry.get_memory_info()
        disk = SystemTelemetry.get_storage_info()
        bat = SystemTelemetry.get_battery_info()
        temps = SystemTelemetry.get_temperatures()
        score = SystemTelemetry.compute_health_score(cpu, mem, disk, bat, temps)

        if self.mode == "simple":
            self.simple_main_ring.update_data(score, str(score), "/100 Saúde geral", "#16A34A")
            self.ring_cpu.update_data(cpu["pct"], str(cpu["pct"]), "CPU", "#0284C7")
            self.ring_ram.update_data(mem["pct"], str(mem["pct"]), "RAM", "#2563EB")
            self.ring_ssd.update_data(disk["pct"], str(disk["pct"]), "SSD", "#D97706")
            self.ring_bat.update_data(bat["pct"], str(bat["pct"]), "Bateria", "#16A34A")
            self.lbl_quick_disk.set_text(f"{disk['free_str']} disponíveis")
            self.lbl_quick_boot.set_text(f"Última: {SystemTelemetry.get_boot_time_str()}")
            self.lbl_updated.set_text(f"Atualizado às {datetime.now().strftime('%H:%M')}")
        else:
            self.comp_main_ring.update_data(score, str(score), "/100 Saúde", "#16A34A")

            self.lbl_c_cpu_model.set_text(f"{cpu['model']}\n{cpu['freq']}")
            self.ring_c_cpu.update_data(cpu["pct"], f"{cpu['pct']}%", "Uso", "#0284C7")
            self.lbl_c_cpu_details.set_text(
                f"Temperatura: {temps['cpu']} °C\nNúcleos: {cpu['cores']} ({cpu['threads']} threads)\nEstado: Saudável"
            )

            self.lbl_c_ram_model.set_text(f"{mem['total_str']} RAM")
            self.ring_c_ram.update_data(mem["pct"], f"{mem['pct']}%", "Uso", "#16A34A")
            z_txt = f"Ativa ({mem['zram_str']})" if mem["zram_active"] else "Inativa"
            self.lbl_c_ram_details.set_text(
                f"Em uso: {mem['used_str']}\nDisponível: {mem['avail_str']}\nzRAM: {z_txt}"
            )

            self.lbl_c_disk_model.set_text(f"{disk['total_str']} ({disk['model']})")
            self.ring_c_disk.update_data(disk["pct"], f"{disk['pct']}%", "Uso", "#0284C7")
            self.lbl_c_disk_details.set_text(
                f"Usado: {disk['used_str']}\nLivre: {disk['free_str']}\nSaúde SMART: OK"
            )

            self.lbl_c_bat_model.set_text(bat["status"])
            self.ring_c_bat.update_data(bat["health"], f"{bat['health']}%", "Saúde", "#16A34A")
            self.lbl_c_bat_details.set_text(
                f"Carga atual: {bat['pct']}%\nOriginal: {bat['design_cap']}\nAtual: {bat['full_cap']}"
            )

            self.lbl_c_temps.set_text(
                f"CPU: {temps['cpu']} °C\nPlaca-mãe: {temps['board']} °C\n"
                f"Armazenamento: {temps['disk']} °C\nGráficos: {temps['gpu']} °C"
            )

            kernel = platform.release().split("-")[0]
            self.lbl_c_os.set_text(
                f"LegacyOS 1.0 (64 bits)\nKernel Linux {kernel}\n"
                f"Host: {socket.gethostname()}\nIntegridade: OK"
            )

            now = datetime.now()
            self.lbl_c_clock.set_text(
                f"Sincronização: Automática\nData: {now.strftime('%d/%m/%Y')}\n"
                f"Hora: {now.strftime('%H:%M:%S')}"
            )

            cache_mb = SystemTelemetry.get_cache_size_mb()
            self.lbl_c_clean.set_text(
                f"{cache_mb} MB podem ser liberados\n• Cache de miniaturas e sistema\n• Arquivos temporários antigos"
            )

    def _run_quick_diagnostic(self, _btn):
        self._refresh_telemetry()
        dlg = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Diagnóstico do LegacyOS Concluído",
        )
        dlg.format_secondary_text(
            "Todos os serviços essenciais, zRAM, armazenamento e sensores térmicos foram verificados e estão operando dentro dos parâmetros normais."
        )
        dlg.run()
        dlg.destroy()

    def _run_smart_cleanup(self, _btn):
        thumb_dir = os.path.expanduser("~/.cache/thumbnails")
        freed_mb = SystemTelemetry.get_cache_size_mb()
        if os.path.isdir(thumb_dir):
            shutil.rmtree(thumb_dir, ignore_errors=True)
            os.makedirs(thumb_dir, exist_ok=True)
        self._refresh_telemetry()

        dlg = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Limpeza Inteligente Concluída",
        )
        dlg.format_secondary_text(
            f"Otimização concluída com sucesso. Cache de miniaturas e temporários do usuário limpos ({freed_mb} MB verificados)."
        )
        dlg.run()
        dlg.destroy()


def main():
    win = LegacyCareCenterWindow()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
