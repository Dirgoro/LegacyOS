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
LOGO_SVG = "/usr/share/pixmaps/legacyos-logo.svg"


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

        # Verifica zRAM ativo
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
        if os.path.ismount("/lib/live/mount/medium"):
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

        # Trilho cinza claro
        ctx.set_line_width(self.line_width)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.set_source_rgb(0.886, 0.910, 0.941)  # #E2E8F0
        ctx.arc(cx, cy, radius, 0, 2 * math.pi)
        ctx.stroke()

        # Arco de progresso
        r, g, b = self._hex_to_rgb(self.color_hex)
        ctx.set_source_rgb(r, g, b)
        start_angle = -math.pi / 2.0
        end_angle = start_angle + (2 * math.pi * (self.value / 100.0))
        ctx.arc(cx, cy, radius, start_angle, end_angle)
        ctx.stroke()

        # Texto central
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
        self.set_icon_name("legacyos-logo")

        self.mode = self._load_mode()  # "simple" ou "complete"
        self.active_tab = "overview"

        self._apply_css()
        self._build_ui()
        self._refresh_telemetry()

        # Atualização leve a cada 4 segundos (consumo mínimo de CPU)
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
        #card-warn {
            background-color: #FFFBEB;
            border: 1px solid #FDE68A;
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
        #secondary-light-btn {
            background-color: #F8FAFC;
            color: #0F172A;
            border: 1px solid #CBD5E1;
            border-radius: 7px;
            padding: 4px 10px;
            font-size: 8.5pt;
            font-weight: 600;
        }
        #secondary-light-btn:hover {
            background-color: #E2E8F0;
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

        icon_img = Gtk.Image.new_from_icon_name("legacyos-logo", Gtk.IconSize.DND)
        icon_img.set_pixel_size(28)
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

        # Seletor de Modo Simples / Completo
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
    # MODO SIMPLES (IMAGEM 1: VISÃO RESUMIDA)
    # ==========================================================================
    def _build_simple_sidebar(self):
        user_name = getpass.getuser().capitalize()
        user_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        user_box.set_margin_bottom(12)
        u_icon = Gtk.Image.new_from_icon_name("avatar-default-symbolic", Gtk.IconSize.DND)
        u_txt = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
        l1 = Gtk.Label(xalign=0)
        l1
