#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LEGACYOS WORKSPACE - Espaço de Trabalho Integrado (Terminal + Navegador)
Combina múltiplas abas de terminal VTE à esquerda e navegador WebKit2 à direita
em uma única janela leve e produtiva para o LegacyOS.
"""

import os
import sys
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango

try:
    gi.require_version("Vte", "2.91")
    from gi.repository import Vte
    HAS_VTE = True
except Exception:
    HAS_VTE = False

try:
    gi.require_version("WebKit2", "4.1")
    from gi.repository import WebKit2
    HAS_WEBKIT = True
except Exception:
    try:
        gi.require_version("WebKit2", "4.0")
        from gi.repository import WebKit2
        HAS_WEBKIT = True
    except Exception:
        HAS_WEBKIT = False

APP_ICON_SVG = "/usr/share/pixmaps/legacyos-workspace.svg"

WELCOME_HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Bem-vindo ao LegacyOS</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: 'Geist', 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: radial-gradient(circle at 50% 25%, #FFFFFF 0%, #F1F5F9 100%);
    color: #0F172A;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    padding: 28px 20px;
  }
  .brand {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 22px;
  }
  .brand-badge {
    width: 34px;
    height: 34px;
    border-radius: 9px;
    background: linear-gradient(135deg, #137FEC, #0B66C3);
    color: #FFFFFF;
    font-weight: 800;
    font-size: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 4px 12px rgba(19, 127, 236, 0.28);
  }
  .brand-name {
    font-size: 16px;
    font-weight: 700;
    color: #0F172A;
  }
  .kicker {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1.8px;
    color: #137FEC;
    text-transform: uppercase;
    margin-bottom: 12px;
  }
  h1 {
    font-size: 36px;
    line-height: 1.15;
    font-weight: 800;
    color: #0F172A;
    margin-bottom: 14px;
  }
  h1 span {
    display: block;
    color: #137FEC;
  }
  .subtitle {
    max-width: 440px;
    font-size: 14px;
    line-height: 1.55;
    color: #475569;
    margin-bottom: 26px;
  }
  .cta-btn {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: linear-gradient(180deg, #137FEC, #0B66C3);
    color: #FFFFFF;
    text-decoration: none;
    font-weight: 700;
    font-size: 14px;
    padding: 12px 24px;
    border-radius: 10px;
    box-shadow: 0 8px 20px rgba(19, 127, 236, 0.25);
    transition: transform 0.15s ease;
    cursor: pointer;
    border: none;
  }
  .cta-btn:hover { transform: translateY(-1px); }
  .metrics {
    display: flex;
    justify-content: center;
    gap: 44px;
    margin-top: 44px;
    padding-top: 24px;
    border-top: 1px solid #E2E8F0;
  }
  .metric-val {
    font-size: 20px;
    font-weight: 800;
    color: #0F172A;
  }
  .metric-lbl {
    font-size: 11.5px;
    color: #64748B;
    margin-top: 3px;
  }
  .quick-links {
    margin-top: 24px;
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    justify-content: center;
  }
  .chip {
    background: #FFFFFF;
    border: 1px solid #CBD5E1;
    color: #334155;
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    text-decoration: none;
  }
  .chip:hover {
    border-color: #137FEC;
    color: #137FEC;
  }
</style>
</head>
<body>
  <div class="brand">
    <div class="brand-badge">L</div>
    <div class="brand-name">LegacyOS</div>
  </div>
  <div class="kicker">TECNOLOGIA PARA TODOS</div>
  <h1>Seu computador.<span>Uma nova história.</span></h1>
  <p class="subtitle">
    Moderno, seguro e cuidadosamente projetado para continuar com você.
  </p>
  <a class="cta-btn" href="https://duckduckgo.com">Conheça o LegacyOS &nbsp;&rsaquo;</a>

  <div class="metrics">
    <div>
      <div class="metric-val">1.0</div>
      <div class="metric-lbl">Versão atual</div>
    </div>
    <div>
      <div class="metric-val">5 anos</div>
      <div class="metric-lbl">Suporte estendido</div>
    </div>
    <div>
      <div class="metric-val">100%</div>
      <div class="metric-lbl">Código aberto</div>
    </div>
  </div>

  <div class="quick-links">
    <a class="chip" href="https://duckduckgo.com">Pesquisar na Web</a>
    <a class="chip" href="https://github.com">GitHub</a>
    <a class="chip" href="https://wiki.debian.org">Documentação Debian</a>
  </div>
</body>
</html>
"""


class LegacyWorkspaceWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="Espaço de trabalho — Terminal e Navegador")
        self.set_default_size(1160, 620)
        self.set_size_request(860, 480)
        self.set_position(Gtk.WindowPosition.CENTER)

        if os.path.isfile(APP_ICON_SVG):
            self.set_icon_from_file(APP_ICON_SVG)
        else:
            self.set_icon_name("legacyos-workspace")

        self.term_tabs = []
        self.browser_tabs = []
        self.active_term_idx = 0
        self.active_browser_idx = 0

        self._apply_css()
        self._build_ui()

        self._add_terminal_tab(initial=True)
        self._add_browser_tab(url="legacyos://boas-vindas")

    def _apply_css(self):
        css = b"""
        #ws-root {
            background-color: #141A23;
            color: #F8FAFC;
        }
        #ws-topbar {
            background-color: #0F141C;
            border-bottom: 1px solid rgba(255, 255, 255, 0.07);
            padding: 6px 14px;
        }
        #ws-title {
            color: #F8FAFC;
            font-size: 11.5pt;
            font-weight: 700;
        }
        #ws-subtitle {
            color: #94A3B8;
            font-size: 8.5pt;
        }
        #pane-header {
            background-color: #141A23;
            border-bottom: 1px solid rgba(255, 255, 255, 0.07);
            padding: 5px 10px;
            min-height: 36px;
        }
        #term-subbar {
            background-color: #0B0F16;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            padding: 3px 12px;
        }
        #term-meta {
            color: #64748B;
            font-size: 8pt;
            font-family: "Monospace", monospace;
        }
        #browser-navbar {
            background-color: #141A23;
            border-bottom: 1px solid rgba(255, 255, 255, 0.07);
            padding: 6px 10px;
        }
        #tab-btn {
            background-color: transparent;
            color: #94A3B8;
            border: none;
            border-radius: 8px;
            padding: 4px 10px;
            font-size: 9pt;
            font-weight: 600;
        }
        #tab-btn:hover {
            background-color: #19212D;
            color: #F8FAFC;
        }
        #tab-btn-active {
            background-color: #19212D;
            color: #F8FAFC;
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 8px;
            padding: 4px 10px;
            font-size: 9pt;
            font-weight: 700;
        }
        #icon-btn {
            background-color: transparent;
            color: #94A3B8;
            border: none;
            border-radius: 7px;
            padding: 4px 8px;
            font-weight: 700;
        }
        #icon-btn:hover {
            background-color: #19212D;
            color: #F8FAFC;
        }
        #url-entry {
            background-color: #0B0F16;
            color: #E2E8F0;
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 9px;
            padding: 5px 12px;
            font-size: 9pt;
        }
        #url-entry:focus {
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
        root.set_name("ws-root")
        self.add(root)

        # Cabeçalho superior estilo LegacyOS
        topbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        topbar.set_name("ws-topbar")
        root.pack_start(topbar, False, False, 0)

        icon_img = Gtk.Image.new_from_icon_name("legacyos-workspace", Gtk.IconSize.DND)
        icon_img.set_pixel_size(28)
        topbar.pack_start(icon_img, False, False, 0)

        t_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        lbl_t = Gtk.Label(label="Espaço de trabalho", xalign=0)
        lbl_t.set_name("ws-title")
        lbl_s = Gtk.Label(label="Terminal e Navegador", xalign=0)
        lbl_s.set_name("ws-subtitle")
        t_col.pack_start(lbl_t, False, False, 0)
        t_col.pack_start(lbl_s, False, False, 0)
        topbar.pack_start(t_col, True, True, 0)

        # Divisor horizontal (Terminal à esquerda | Navegador à direita)
        self.paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        self.paned.set_wide_handle(True)
        root.pack_start(self.paned, True, True, 0)

        # ======================================================================
        # PAINEL ESQUERDO: TERMINAL INTEGRADO
        # ======================================================================
        left_pane = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.paned.pack1(left_pane, resize=True, shrink=False)

        term_hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        term_hdr.set_name("pane-header")
        left_pane.pack_start(term_hdr, False, False, 0)

        self.term_tabs_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        term_hdr.pack_start(self.term_tabs_box, False, False, 0)

        btn_new_term = Gtk.Button(label="+")
        btn_new_term.set_name("icon-btn")
        btn_new_term.set_tooltip_text("Nova aba de terminal")
        btn_new_term.connect("clicked", lambda _: self._add_terminal_tab(initial=False))
        term_hdr.pack_start(btn_new_term, False, False, 2)

        subbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        subbar.set_name("term-subbar")
        self.lbl_term_meta = Gtk.Label(label="bash — 80×24", xalign=0)
        self.lbl_term_meta.set_name("term-meta")
        subbar.pack_start(self.lbl_term_meta, True, True, 0)
        left_pane.pack_start(subbar, False, False, 0)

        self.term_stack = Gtk.Stack()
        self.term_stack.set_transition_type(Gtk.StackTransitionType.NONE)
        left_pane.pack_start(self.term_stack, True, True, 0)

        # ======================================================================
        # PAINEL DIREITO: NAVEGADOR INTEGRADO
        # ======================================================================
        right_pane = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.paned.pack2(right_pane, resize=True, shrink=False)

        browser_hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        browser_hdr.set_name("pane-header")
        right_pane.pack_start(browser_hdr, False, False, 0)

        self.browser_tabs_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        browser_hdr.pack_start(self.browser_tabs_box, False, False, 0)

        btn_new_tab = Gtk.Button(label="+")
        btn_new_tab.set_name("icon-btn")
        btn_new_tab.set_tooltip_text("Nova aba do navegador")
        btn_new_tab.connect("clicked", lambda _: self._add_browser_tab("legacyos://boas-vindas"))
        browser_hdr.pack_start(btn_new_tab, False, False, 2)

        navbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        navbar.set_name("browser-navbar")
        right_pane.pack_start(navbar, False, False, 0)

        self.btn_back = Gtk.Button(label="‹")
        self.btn_back.set_name("icon-btn")
        self.btn_back.set_tooltip_text("Voltar")
        self.btn_back.connect("clicked", self._on_browser_back)
        navbar.pack_start(self.btn_back, False, False, 0)

        self.btn_fwd = Gtk.Button(label="›")
        self.btn_fwd.set_name("icon-btn")
        self.btn_fwd.set_tooltip_text("Avançar")
        self.btn_fwd.connect("clicked", self._on_browser_forward)
        navbar.pack_start(self.btn_fwd, False, False, 0)

        self.btn_reload = Gtk.Button(label="↻")
        self.btn_reload.set_name("icon-btn")
        self.btn_reload.set_tooltip_text("Recarregar página")
        self.btn_reload.connect("clicked", self._on_browser_reload)
        navbar.pack_start(self.btn_reload, False, False, 0)

        self.url_entry = Gtk.Entry()
        self.url_entry.set_name("url-entry")
        self.url_entry.set_icon_from_icon_name(Gtk.EntryIconPosition.PRIMARY, "channel-secure-symbolic")
        self.url_entry.set_text("legacyos.org/boas-vindas")
        self.url_entry.connect("activate", self._on_url_activate)
        navbar.pack_start(self.url_entry, True, True, 0)

        btn_home = Gtk.Button(label="⌂")
        btn_home.set_name("icon-btn")
        btn_home.set_tooltip_text("Página inicial do LegacyOS")
        btn_home.connect("clicked", lambda _: self._navigate_current("legacyos://boas-vindas"))
        navbar.pack_end(btn_home, False, False, 0)

        self.browser_stack = Gtk.Stack()
        self.browser_stack.set_transition_type(Gtk.StackTransitionType.NONE)
        right_pane.pack_start(self.browser_stack, True, True, 0)

        # Proporção inicial 42% Terminal / 58% Navegador (idêntico à imagem)
        self.paned.set_position(485)

    # --------------------------------------------------------------------------
    # GERENCIAMENTO DAS ABAS DO TERMINAL
    # --------------------------------------------------------------------------
    def _add_terminal_tab(self, initial=False):
        idx = len(self.term_tabs)
        page_name = f"term-{idx}-{GLib.get_monotonic_time()}"

        if HAS_VTE:
            term = Vte.Terminal()
            term.set_scrollback_lines(5000)
            term.set_audible_bell(False)
            term.set_font(Pango.FontDescription("Monospace 10"))

            bg = Gdk.RGBA()
            bg.parse("#0B0F16")
            fg = Gdk.RGBA()
            fg.parse("#E2E8F0")
            cursor = Gdk.RGBA()
            cursor.parse("#10B981")

            palette = []
            hex_colors = [
                "#0F172A", "#EF4444", "#10B981", "#F59E0B",
                "#137FEC", "#8B5CF6", "#38BDF8", "#CBD5E1",
                "#475569", "#F87171", "#34D399", "#FBBF24",
                "#60A5FA", "#A78BFA", "#7DD3FC", "#F8FAFC",
            ]
            for h in hex_colors:
                c = Gdk.RGBA()
                c.parse(h)
                palette.append(c)

            term.set_colors(fg, bg, palette)
            term.set_color_cursor(cursor)

            shell = os.environ.get("SHELL", "/bin/bash")
            term.spawn_async(
                Vte.PtyFlags.DEFAULT,
                os.path.expanduser("~"),
                [shell],
                None,
                GLib.SpawnFlags.DEFAULT,
                None,
                None,
                -1,
                None,
                None,
            )

            if initial:
                banner = (
                    b"printf '\\033[1;37mLegacyOS Terminal\\033[0m \\033[0;36mv1.0\\033[0m\\r\\n"
                    b"\\033[0;90mEspaco de Trabalho Integrado - Pronto para comandos\\033[0m\\r\\n\\r\\n'\n"
                )
                GLib.timeout_add(250, lambda: (term.feed_child(banner), False)[1])

            term.connect("size-allocate", self._on_term_resize)
            widget = Gtk.ScrolledWindow()
            widget.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
            widget.add(term)
        else:
            term = None
            widget = Gtk.Label(label="Instale gir1.2-vte-2.91 para ativar o terminal embutido.")

        self.term_stack.add_named(widget, page_name)
        widget.show_all()

        title = "Terminal" if idx == 0 else f"Terminal {idx + 1}"
        self.term_tabs.append({"name": page_name, "title": title, "term": term, "widget": widget})
        self._select_terminal_tab(len(self.term_tabs) - 1)

    def _on_term_resize(self, term, _alloc):
        if term:
            cols = term.get_column_count()
            rows = term.get_row_count()
            self.lbl_term_meta.set_text(f"bash — {cols}×{rows}")

    def _select_terminal_tab(self, idx):
        if idx < 0 or idx >= len(self.term_tabs):
            return
        self.active_term_idx = idx
        tab = self.term_tabs[idx]
        self.term_stack.set_visible_child_name(tab["name"])
        if tab["term"]:
            tab["term"].grab_focus()
            self._on_term_resize(tab["term"], None)
        self._refresh_terminal_tab_bar()

    def _close_terminal_tab(self, idx):
        if len(self.term_tabs) <= 1:
            return
        tab = self.term_tabs.pop(idx)
        self.term_stack.remove(tab["widget"])
        new_idx = min(idx, len(self.term_tabs) - 1)
        self._select_terminal_tab(new_idx)

    def _refresh_terminal_tab_bar(self):
        for child in self.term_tabs_box.get_children():
            self.term_tabs_box.remove(child)

        for i, tab in enumerate(self.term_tabs):
            btn = Gtk.Button()
            btn.set_name("tab-btn-active" if i == self.active_term_idx else "tab-btn")
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            row.pack_start(Gtk.Image.new_from_icon_name("utilities-terminal-symbolic", Gtk.IconSize.MENU), False, False, 0)
            row.pack_start(Gtk.Label(label=tab["title"]), False, False, 0)
            if len(self.term_tabs) > 1:
                close_lbl = Gtk.Label(label="×")
                ev = Gtk.EventBox()
                ev.add(close_lbl)
                ev.connect("button-press-event", lambda _w, _e, k=i: self._close_terminal_tab(k))
                row.pack_start(ev, False, False, 2)
            btn.add(row)
            btn.connect("clicked", lambda _b, k=i: self._select_terminal_tab(k))
            self.term_tabs_box.pack_start(btn, False, False, 0)

        self.term_tabs_box.show_all()

    # --------------------------------------------------------------------------
    # GERENCIAMENTO DAS ABAS DO NAVEGADOR INTEGRADO
    # --------------------------------------------------------------------------
    def _add_browser_tab(self, url="legacyos://boas-vindas"):
        idx = len(self.browser_tabs)
        page_name = f"web-{idx}-{GLib.get_monotonic_time()}"

        if HAS_WEBKIT:
            settings = WebKit2.Settings()
            settings.set_enable_javascript(True)
            settings.set_enable_smooth_scrolling(True)
            settings.set_hardware_acceleration_policy(WebKit2.HardwareAccelerationPolicy.ON_DEMAND)

            webview = WebKit2.WebView.new_with_settings(settings)
            webview.connect("notify::title", self._on_webview_title_changed)
            webview.connect("notify::uri", self._on_webview_uri_changed)
            widget = webview
        else:
            webview = None
            widget = Gtk.Label(label="Instale gir1.2-webkit2-4.1 para ativar o navegador embutido.")

        self.browser_stack.add_named(widget, page_name)
        widget.show_all()

        self.browser_tabs.append({
            "name": page_name,
            "title": "Bem-vindo ao LegacyOS",
            "url": url,
            "webview": webview,
            "widget": widget,
        })
        self._select_browser_tab(len(self.browser_tabs) - 1)
        self._load_url_in_tab(len(self.browser_tabs) - 1, url)

    def _load_url_in_tab(self, idx, raw_url):
        tab = self.browser_tabs[idx]
        wv = tab["webview"]
        if not wv:
            return

        clean = raw_url.strip()
        if clean in ("", "legacyos://boas-vindas", "legacyos.org/boas-vindas"):
            tab["url"] = "legacyos.org/boas-vindas"
            tab["title"] = "Bem-vindo ao LegacyOS"
            wv.load_html(WELCOME_HTML, "https://legacyos.org/boas-vindas")
            if idx == self.active_browser_idx:
                self.url_entry.set_text("legacyos.org/boas-vindas")
            self._refresh_browser_tab_bar()
            return

        if "://" not in clean:
            if "." in clean and " " not in clean:
                target = "https://" + clean
            else:
                target = "https://duckduckgo.com/?q=" + GLib.uri_escape_string(clean, None, True)
        else:
            target = clean

        tab["url"] = target
        wv.load_uri(target)

    def _navigate_current(self, url):
        self._load_url_in_tab(self.active_browser_idx, url)

    def _on_url_activate(self, entry):
        self._navigate_current(entry.get_text())

    def _on_browser_back(self, _btn):
        wv = self.browser_tabs[self.active_browser_idx]["webview"]
        if wv and wv.can_go_back():
            wv.go_back()

    def _on_browser_forward(self, _btn):
        wv = self.browser_tabs[self.active_browser_idx]["webview"]
        if wv and wv.can_go_forward():
            wv.go_forward()

    def _on_browser_reload(self, _btn):
        wv = self.browser_tabs[self.active_browser_idx]["webview"]
        if wv:
            wv.reload()

    def _on_webview_title_changed(self, webview, _param):
        for tab in self.browser_tabs:
            if tab["webview"] == webview:
                t = webview.get_title()
                if t:
                    tab["title"] = t[:24]
                break
        self._refresh_browser_tab_bar()

    def _on_webview_uri_changed(self, webview, _param):
        uri = webview.get_uri() or ""
        if uri.startswith("https://legacyos.org/boas-vindas"):
            display_uri = "legacyos.org/boas-vindas"
        else:
            display_uri = uri.replace("https://", "").replace("http://", "")

        for i, tab in enumerate(self.browser_tabs):
            if tab["webview"] == webview:
                tab["url"] = display_uri
                if i == self.active_browser_idx:
                    self.url_entry.set_text(display_uri)
                break

    def _select_browser_tab(self, idx):
        if idx < 0 or idx >= len(self.browser_tabs):
            return
        self.active_browser_idx = idx
        tab = self.browser_tabs[idx]
        self.browser_stack.set_visible_child_name(tab["name"])
        self.url_entry.set_text(tab["url"])
        self._refresh_browser_tab_bar()

    def _close_browser_tab(self, idx):
        if len(self.browser_tabs) <= 1:
            return
        tab = self.browser_tabs.pop(idx)
        self.browser_stack.remove(tab["widget"])
        new_idx = min(idx, len(self.browser_tabs) - 1)
        self._select_browser_tab(new_idx)

    def _refresh_browser_tab_bar(self):
        for child in self.browser_tabs_box.get_children():
            self.browser_tabs_box.remove(child)

        for i, tab in enumerate(self.browser_tabs):
            btn = Gtk.Button()
            btn.set_name("tab-btn-active" if i == self.active_browser_idx else "tab-btn")
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            row.pack_start(Gtk.Image.new_from_icon_name("web-browser-symbolic", Gtk.IconSize.MENU), False, False, 0)
            row.pack_start(Gtk.Label(label=tab["title"]), False, False, 0)
            if len(self.browser_tabs) > 1:
                close_lbl = Gtk.Label(label="×")
                ev = Gtk.EventBox()
                ev.add(close_lbl)
                ev.connect("button-press-event", lambda _w, _e, k=i: self._close_browser_tab(k))
                row.pack_start(ev, False, False, 2)
            btn.add(row)
            btn.connect("clicked", lambda _b, k=i: self._select_browser_tab(k))
            self.browser_tabs_box.pack_start(btn, False, False, 0)

        self.browser_tabs_box.show_all()


def main():
    win = LegacyWorkspaceWindow()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
