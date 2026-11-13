#!/bin/bash
# ==============================================================================
# LEGACYOS - SCRIPT DE ESTABILIZAÇÃO VISUAL E ADAPTATIVA (FASE 2)
# Adapta automaticamente painel, dock, menus e janelas para telas 1024x600+
# ==============================================================================

export DISPLAY="${DISPLAY:-:0}"
sleep 2

# ------------------------------------------------------------------------------
# 0. DETECÇÃO DE RESOLUÇÃO DE TELA (MODO COMPACTO PARA NETBOOKS COMO D260)
# ------------------------------------------------------------------------------
SCREEN_HEIGHT=$(xrandr --current 2>/dev/null | awk '/\*/ {split($1, res, "x"); print res[2]; exit}')
SCREEN_HEIGHT="${SCREEN_HEIGHT:-768}"

if [ "$SCREEN_HEIGHT" -le 650 ]; then
    # Perfil Netbook / Tela Legado (ex: Acer Aspire One D260 1024x600)
    PANEL_SIZE=26
    DOCK_ICON_SIZE=34
    DOCK_HIDE_MODE="intelligent"
    WHISKER_WIDTH=500
    WHISKER_HEIGHT=420
    FONT_SIZE="9.5"
else
    # Perfil Padrão (HD / Full HD)
    PANEL_SIZE=30
    DOCK_ICON_SIZE=44
    DOCK_HIDE_MODE="none"
    WHISKER_WIDTH=560
    WHISKER_HEIGHT=500
    FONT_SIZE="10"
fi

# ------------------------------------------------------------------------------
# 1. TEMA GLOBAL, BORDAS DE JANELA, ÍCONES E GERENCIADOR ADAPTATIVO (XFWM4)
# ------------------------------------------------------------------------------
xfconf-query -c xsettings -p /Net/ThemeName -n -t string -s "LegacyOS-Theme"
xfconf-query -c xsettings -p /Net/IconThemeName -n -t string -s "Papirus-Dark"
xfconf-query -c xsettings -p /Gtk/FontName -n -t string -s "Geist ${FONT_SIZE}"
xfconf-query -c xsettings -p /Gtk/DecorationLayout -n -t string -s "menu:minimize,maximize,close"

xfconf-query -c xfwm4 -p /general/theme -n -t string -s "LegacyOS-Theme"
xfconf-query -c xfwm4 -p /general/title_font -n -t string -s "Geist Bold ${FONT_SIZE}"
xfconf-query -c xfwm4 -p /general/use_compositing -n -t bool -s true
xfconf-query -c xfwm4 -p /general/show_dock_shadow -n -t bool -s false

# Permite mover qualquer janela segurando Alt + Clique (vital em telas de 600px)
xfconf-query -c xfwm4 -p /general/easy_click -n -t string -s "Alt"
xfconf-query -c xfwm4 -p /general/placement_mode -n -t string -s "center"
xfconf-query -c xfwm4 -p /general/snap_to_border -n -t bool -s true
xfconf-query -c xfwm4 -p /general/tile_on_move -n -t bool -s true

# ------------------------------------------------------------------------------
# 2. CONSTRUÇÃO DA BARRA SUPERIOR (LEGACYOS, LOCAIS, BANDEJA E RELÓGIO)
# ------------------------------------------------------------------------------
pkill -x xfce4-panel 2>/dev/null || true
sleep 0.5

xfconf-query -c xfce4-panel -p / -r -R 2>/dev/null || true

xfconf-query -c xfce4-panel -p /panels -n -t int -s 1 --force-array
xfconf-query -c xfce4-panel -p /panels/panel-1/position -n -t string -s "p=6;x=0;y=0"
xfconf-query -c xfce4-panel -p /panels/panel-1/position-locked -n -t bool -s true
xfconf-query -c xfce4-panel -p /panels/panel-1/size -n -t uint -s "$PANEL_SIZE"
xfconf-query -c xfce4-panel -p /panels/panel-1/length -n -t double -s 100.0
xfconf-query -c xfce4-panel -p /panels/panel-1/length-adjust -n -t bool -s true
xfconf-query -c xfce4-panel -p /panels/panel-1/background-style -n -t uint -s 1
xfconf-query -c xfce4-panel -p /panels/panel-1/background-rgba -n \
    -t double -s 0.043 -t double -s 0.067 -t double -s 0.125 -t double -s 0.94

# Plugin 1: Menu Principal (Whisker Menu com dimensões adaptativas)
xfconf-query -c xfce4-panel -p /plugins/plugin-1 -n -t string -s "whiskermenu"
xfconf-query -c xfce4-panel -p /plugins/plugin-1/button-title -n -t string -s "LegacyOS"
xfconf-query -c xfce4-panel -p /plugins/plugin-1/show-button-title -n -t bool -s true
xfconf-query -c xfce4-panel -p /plugins/plugin-1/show-button-icon -n -t bool -s true
xfconf-query -c xfce4-panel -p /plugins/plugin-1/button-icon -n -t string -s "distributor-logo"
xfconf-query -c xfce4-panel -p /plugins/plugin-1/menu-width -n -t int -s "$WHISKER_WIDTH"
xfconf-query -c xfce4-panel -p /plugins/plugin-1/menu-height -n -t int -s "$WHISKER_HEIGHT"

# Plugin 2: Menu de Locais (Pastas)
xfconf-query -c xfce4-panel -p /plugins/plugin-2 -n -t string -s "directorymenu"
xfconf-query -c xfce4-panel -p /plugins/plugin-2/base-directory -n -t string -s "$HOME"

# Plugin 3: Separador Expansível
xfconf-query -c xfce4-panel -p /plugins/plugin-3 -n -t string -s "separator"
xfconf-query -c xfce4-panel -p /plugins/plugin-3/expand -n -t bool -s true
xfconf-query -c xfce4-panel -p /plugins/plugin-3/style -n -t uint -s 0

# Plugin 4: Bandeja do Sistema (Wi-Fi / Legacy Guardian)
xfconf-query -c xfce4-panel -p /plugins/plugin-4 -n -t string -s "systray"
xfconf-query -c xfce4-panel -p /plugins/plugin-4/square-icons -n -t bool -s true
xfconf-query -c xfce4-panel -p /plugins/plugin-4/icon-size -n -t int -s 16

# Plugin 5: Controle de Áudio
xfconf-query -c xfce4-panel -p /plugins/plugin-5 -n -t string -s "pulseaudio"
xfconf-query -c xfce4-panel -p /plugins/plugin-5/enable-keyboard-shortcuts -n -t bool -s true

# Plugin 6: Gerenciador de Energia / Bateria
xfconf-query -c xfce4-panel -p /plugins/plugin-6 -n -t string -s "power-manager-plugin"

# Plugin 7: Relógio e Data
xfconf-query -c xfce4-panel -p /plugins/plugin-7 -n -t string -s "clock"
xfconf-query -c xfce4-panel -p /plugins/plugin-7/digital-layout -n -t uint -s 3
xfconf-query -c xfce4-panel -p /plugins/plugin-7/digital-time-format -n -t string -s "%a, %d de %b  %H:%M"

# Plugin 8: Menu de Sistema / Sessão
xfconf-query -c xfce4-panel -p /plugins/plugin-8 -n -t string -s "actions"
xfconf-query -c xfce4-panel -p /plugins/plugin-8/appearance -n -t uint -s 0

xfconf-query -c xfce4-panel -p /panels/panel-1/plugin-ids -n \
    -t int -s 1 -t int -s 2 -t int -s 3 -t int -s 4 \
    -t int -s 5 -t int -s 6 -t int -s 7 -t int -s 8 --force-array

nohup xfce4-panel >/dev/null 2>&1 &

# ------------------------------------------------------------------------------
# 3. APLICAÇÃO DO PAPEL DE PAREDE OFICIAL (/usr/share/backgrounds/legacyos-wallpaper.jpg)
# ------------------------------------------------------------------------------
WALLPAPER="/usr/share/backgrounds/legacyos-wallpaper.jpg"

if [ -f "$WALLPAPER" ]; then
    DETECTED_MONITORS=$(xrandr --query 2>/dev/null | awk '/ connected/{print "monitor"$1}')
    ALL_MONITORS=$(echo -e "${DETECTED_MONITORS}\nmonitor0\nmonitorVirtual-1\nmonitorVirtual1\nmonitorVGA-1\nmonitorVGA1\nmonitorHDMI-1\nmonitoreDP-1" | sort -u)

    for MON in $ALL_MONITORS; do
        [ -z "$MON" ] && continue
        xfconf-query -c xfce4-desktop -p "/backdrop/screen0/${MON}/workspace0/color-style" -n -t int -s 0
        xfconf-query -c xfce4-desktop -p "/backdrop/screen0/${MON}/workspace0/image-style" -n -t int -s 5
        xfconf-query -c xfce4-desktop -p "/backdrop/screen0/${MON}/workspace0/last-image" -n -t string -s "$WALLPAPER"
    done
fi

if ! pgrep -x xfdesktop >/dev/null; then
    nohup xfdesktop >/dev/null 2>&1 &
    sleep 1
else
    xfdesktop --reload 2>/dev/null || true
fi

# ------------------------------------------------------------------------------
# 4. CONFIGURAÇÃO E INICIALIZAÇÃO ADAPTATIVA DA DOCK (PLANK)
# ------------------------------------------------------------------------------
DOCK_DIR="$HOME/.config/plank/dock1/launchers"
mkdir -p "$DOCK_DIR"

if [ -z "$(ls -A "$DOCK_DIR" 2>/dev/null)" ]; then
    for APP in \
        legacy-care-center.desktop \
        brave-browser.desktop \
        firefox-esr.desktop \
        onlyoffice-desktopeditors.desktop \
        thunar.desktop \
        xfce4-terminal.desktop \
        xfce-settings-manager.desktop; do
        if [ -f "/usr/share/applications/${APP}" ]; then
            echo "[PlankDockItemPreferences]" > "${DOCK_DIR}/${APP%.desktop}.dockitem"
            echo "Launcher=file:///usr/share/applications/${APP}" >> "${DOCK_DIR}/${APP%.desktop}.dockitem"
        fi
    done
fi

if [ -d "/usr/share/plank/themes/LegacyOS-Dock" ]; then
    gsettings set net.launchpad.plank.dock.settings:/net/launchpad/plank/docks/dock1/ theme 'LegacyOS-Dock' 2>/dev/null || true
fi
gsettings set net.launchpad.plank.dock.settings:/net/launchpad/plank/docks/dock1/ icon-size "$DOCK_ICON_SIZE" 2>/dev/null || true
gsettings set net.launchpad.plank.dock.settings:/net/launchpad/plank/docks/dock1/ hide-mode "$DOCK_HIDE_MODE" 2>/dev/null || true
gsettings set net.launchpad.plank.dock.settings:/net/launchpad/plank/docks/dock1/ zoom-enabled true 2>/dev/null || true

if ! pgrep -x plank >/dev/null; then
    nohup plank >/dev/null 2>&1 &
fi

# ------------------------------------------------------------------------------
# 5. ALINHAMENTO DOS ÍCONES DA ÁREA DE TRABALHO
# ------------------------------------------------------------------------------
if [ -x "/usr/bin/legacyos-move-icons.sh" ]; then
    sleep 1
    /usr/bin/legacyos-move-icons.sh >/dev/null 2>&1 &
fi

exit 0
