#!/bin/bash
# ==============================================================================
# LEGACYOS - SCRIPT DE ESTABILIZAÇÃO VISUAL, ÍCONE DE INSTALAÇÃO E SESSÃO
# ==============================================================================

export DISPLAY="${DISPLAY:-:0}"

# ------------------------------------------------------------------------------
# 0. MANTÉM A CORTINA DE CARREGAMENTO ATIVA ATÉ O DESKTOP ESTAR 100% PRONTO
# ------------------------------------------------------------------------------
LOCK_FILE="/tmp/legacyos-splash.lock"
SPLASH_SCRIPT="/usr/share/legacyos/src/login-splash/main.py"

touch "$LOCK_FILE"
trap 'rm -f "$LOCK_FILE"' EXIT

if [ -f "$SPLASH_SCRIPT" ] && ! pgrep -f "login-splash/main.py" >/dev/null; then
    python3 "$SPLASH_SCRIPT" >/dev/null 2>&1 &
fi

sleep 1.2

# Corrige caminho absoluto do tema Qt5/Qt6 para o usuário ativo
for QT_VER in qt5ct qt6ct; do
    QT_CONF="$HOME/.config/${QT_VER}/${QT_VER}.conf"
    if [ -f "$QT_CONF" ]; then
        sed -i "s|/etc/skel/.config/${QT_VER}|$HOME/.config/${QT_VER}|g" "$QT_CONF"
    fi
done

# ------------------------------------------------------------------------------
# 1. DETECÇÃO DE RESOLUÇÃO DE TELA (MODO COMPACTO PARA NETBOOKS COMO D260)
# ------------------------------------------------------------------------------
SCREEN_HEIGHT=$(xrandr --current 2>/dev/null | awk '/\*/ {split($1, res, "x"); print res[2]; exit}')
SCREEN_HEIGHT="${SCREEN_HEIGHT:-768}"

if [ "$SCREEN_HEIGHT" -le 650 ]; then
    PANEL_SIZE=26
    DOCK_ICON_SIZE=34
    DOCK_HIDE_MODE="intelligent"
    WHISKER_WIDTH=500
    WHISKER_HEIGHT=420
    FONT_SIZE="9.5"
else
    PANEL_SIZE=30
    DOCK_ICON_SIZE=44
    DOCK_HIDE_MODE="none"
    WHISKER_WIDTH=560
    WHISKER_HEIGHT=500
    FONT_SIZE="10"
fi

# ------------------------------------------------------------------------------
# 2. TEMA GLOBAL, BORDAS DE JANELA, ÍCONES E GERENCIADOR ADAPTATIVO (XFWM4)
# ------------------------------------------------------------------------------
xfconf-query -c xsettings -p /Net/ThemeName -n -t string -s "LegacyOS-Theme"
xfconf-query -c xsettings -p /Net/IconThemeName -n -t string -s "Papirus-Dark"
xfconf-query -c xsettings -p /Gtk/FontName -n -t string -s "Geist ${FONT_SIZE}"
xfconf-query -c xsettings -p /Gtk/DecorationLayout -n -t string -s "menu:minimize,maximize,close"

xfconf-query -c xfwm4 -p /general/theme -n -t string -s "LegacyOS-Theme"
xfconf-query -c xfwm4 -p /general/title_font -n -t string -s "Geist Bold ${FONT_SIZE}"
xfconf-query -c xfwm4 -p /general/use_compositing -n -t bool -s true
xfconf-query -c xfwm4 -p /general/show_dock_shadow -n -t bool -s false

xfconf-query -c xfwm4 -p /general/easy_click -n -t string -s "Alt"
xfconf-query -c xfwm4 -p /general/placement_mode -n -t string -s "center"
xfconf-query -c xfwm4 -p /general/snap_to_border -n -t bool -s true
xfconf-query -c xfwm4 -p /general/tile_on_move -n -t bool -s true

# ------------------------------------------------------------------------------
# 3. CONSTRUÇÃO DA BARRA SUPERIOR (SOMENTE SÍMBOLO LEGACYOS, LOCAIS, BANDEJA E RELÓGIO)
# ------------------------------------------------------------------------------
pkill -x xfce4-panel 2>/dev/null || true
sleep 0.4

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

# Plugin 1: Menu Principal (Somente o símbolo do LegacyOS, sem texto)
xfconf-query -c xfce4-panel -p /plugins/plugin-1 -n -t string -s "whiskermenu"
xfconf-query -c xfce4-panel -p /plugins/plugin-1/button-title -n -t string -s ""
xfconf-query -c xfce4-panel -p /plugins/plugin-1/show-button-title -n -t bool -s false
xfconf-query -c xfce4-panel -p /plugins/plugin-1/show-button-icon -n -t bool -s true
xfconf-query -c xfce4-panel -p /plugins/plugin-1/button-icon -n -t string -s "/usr/share/pixmaps/legacyos-logo.svg"
xfconf-query -c xfce4-panel -p /plugins/plugin-1/menu-width -n -t int -s "$WHISKER_WIDTH"
xfconf-query -c xfce4-panel -p /plugins/plugin-1/menu-height -n -t int -s "$WHISKER_HEIGHT"
xfconf-query -c xfce4-panel -p /plugins/plugin-1/display-command-settings -n -t bool -s true
xfconf-query -c xfce4-panel -p /plugins/plugin-1/display-command-lockscreen -n -t bool -s true
xfconf-query -c xfce4-panel -p /plugins/plugin-1/display-command-switchuser -n -t bool -s true
xfconf-query -c xfce4-panel -p /plugins/plugin-1/display-command-logoutuser -n -t bool -s true
xfconf-query -c xfce4-panel -p /plugins/plugin-1/display-command-restart -n -t bool -s true
xfconf-query -c xfce4-panel -p /plugins/plugin-1/display-command-shutdown -n -t bool -s true
xfconf-query -c xfce4-panel -p /plugins/plugin-1/display-command-suspend -n -t bool -s true

# Plugin 2: Menu de Locais
xfconf-query -c xfce4-panel -p /plugins/plugin-2 -n -t string -s "directorymenu"
xfconf-query -c xfce4-panel -p /plugins/plugin-2/base-directory -n -t string -s "$HOME"

# Plugin 3: Separador Expansível
xfconf-query -c xfce4-panel -p /plugins/plugin-3 -n -t string -s "separator"
xfconf-query -c xfce4-panel -p /plugins/plugin-3/expand -n -t bool -s true
xfconf-query -c xfce4-panel -p /plugins/plugin-3/style -n -t uint -s 0

# Plugin 4: Bandeja do Sistema
xfconf-query -c xfce4-panel -p /plugins/plugin-4 -n -t string -s "systray"
xfconf-query -c xfce4-panel -p /plugins/plugin-4/square-icons -n -t bool -s true
xfconf-query -c xfce4-panel -p /plugins/plugin-4/icon-size -n -t int -s 16

# Plugin 5: Controle de Áudio
xfconf-query -c xfce4-panel -p /plugins/plugin-5 -n -t string -s "pulseaudio"
xfconf-query -c xfce4-panel -p /plugins/plugin-5/enable-keyboard-shortcuts -n -t bool -s true

# Plugin 6: Gerenciador de Energia / Bateria
xfconf-query -c xfce4-panel -p /plugins/plugin-6 -n -t string -s "power-manager-plugin"

# Plugin 7: Relógio e Data (Final da barra superior, sem o nome do usuário)
xfconf-query -c xfce4-panel -p /plugins/plugin-7 -n -t string -s "clock"
xfconf-query -c xfce4-panel -p /plugins/plugin-7/digital-layout -n -t uint -s 3
xfconf-query -c xfce4-panel -p /plugins/plugin-7/digital-time-format -n -t string -s "%a, %d de %b  %H:%M"

xfconf-query -c xfce4-panel -p /panels/panel-1/plugin-ids -n \
    -t int -s 1 -t int -s 2 -t int -s 3 -t int -s 4 \
    -t int -s 5 -t int -s 6 -t int -s 7 --force-array

nohup xfce4-panel >/dev/null 2>&1 &

# ------------------------------------------------------------------------------
# 4. APLICAÇÃO DO PAPEL DE PAREDE OFICIAL
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
    sleep 1.0
else
    xfdesktop --reload 2>/dev/null || true
fi

# ------------------------------------------------------------------------------
# 5. ÍCONE DE INSTALAÇÃO NA ÁREA DE TRABALHO (APENAS LEGACYOS EM MODO LIVE)
# ------------------------------------------------------------------------------
xdg-user-dirs-update 2>/dev/null || true
XDG_DESKTOP="$(xdg-user-dir DESKTOP 2>/dev/null || echo "$HOME/Desktop")"
mkdir -p "$HOME/Desktop" "$XDG_DESKTOP"

xfconf-query -c xfce4-desktop -p /desktop-icons/file-icons/show-home -n -t bool -s true
xfconf-query -c xfce4-desktop -p /desktop-icons/file-icons/show-filesystem -n -t bool -s true
xfconf-query -c xfce4-desktop -p /desktop-icons/file-icons/show-trash -n -t bool -s true

for TARGET_DIR in "$HOME/Desktop" "$XDG_DESKTOP"; do
    [ -d "$TARGET_DIR" ] || continue
    rm -f "$TARGET_DIR"/*debian*.desktop "$TARGET_DIR"/calamares.desktop

    if grep -q "boot=live" /proc/cmdline; then
        INSTALL_SRC="/usr/share/applications/legacyos-installer.desktop"
        INSTALL_DST="$TARGET_DIR/instalar-legacyos.desktop"
        if [ -f "$INSTALL_SRC" ]; then
            cp "$INSTALL_SRC" "$INSTALL_DST"
            chmod 755 "$INSTALL_DST"
            CHECKSUM=$(sha256sum "$INSTALL_DST" | awk '{print $1}')
            gio set "$INSTALL_DST" metadata::xfce-exe-checksum "$CHECKSUM" 2>/dev/null || true
        fi
    else
        rm -f "$TARGET_DIR/instalar-legacyos.desktop"
    fi
done

xfdesktop --reload 2>/dev/null || true

# ------------------------------------------------------------------------------
# 6. CONFIGURAÇÃO E INICIALIZAÇÃO COMPLETA DA DOCK (PLANK)
# ------------------------------------------------------------------------------
CONFIG_DIR="$HOME/.config/legacyos"
DOCK_FLAG="$CONFIG_DIR/.dock_initialized_v3"
DOCK_DIR="$HOME/.config/plank/dock1/launchers"

mkdir -p "$CONFIG_DIR" "$DOCK_DIR"

if [ ! -f "$DOCK_FLAG" ]; then
    pkill -x plank 2>/dev/null || true
    sleep 0.4
    rm -f "$DOCK_DIR"/*.dockitem

    IDX=1
    for APP in \
        legacyos-settings.desktop \
        legacyos-apps.desktop \
        legacy-care-center.desktop \
        brave-browser.desktop \
        firefox-esr.desktop \
        onlyoffice-desktopeditors.desktop \
        thunar.desktop \
        xfce4-terminal.desktop; do
        if [ -f "/usr/share/applications/${APP}" ]; then
            PREFIX=$(printf "%02d" "$IDX")
            echo "[PlankDockItemPreferences]" > "${DOCK_DIR}/${PREFIX}-${APP%.desktop}.dockitem"
            echo "Launcher=file:///usr/share/applications/${APP}" >> "${DOCK_DIR}/${PREFIX}-${APP%.desktop}.dockitem"
            IDX=$((IDX + 1))
        fi
    done

    touch "$DOCK_FLAG"
fi

gsettings set net.launchpad.plank.dock.settings:/net/launchpad/plank/docks/dock1/ theme 'LegacyOS-Dock' 2>/dev/null || true
gsettings set net.launchpad.plank.dock.settings:/net/launchpad/plank/docks/dock1/ position 'bottom' 2>/dev/null || true
gsettings set net.launchpad.plank.dock.settings:/net/launchpad/plank/docks/dock1/ alignment 'center' 2>/dev/null || true
gsettings set net.launchpad.plank.dock.settings:/net/launchpad/plank/docks/dock1/ items-alignment 'center' 2>/dev/null || true
gsettings set net.launchpad.plank.dock.settings:/net/launchpad/plank/docks/dock1/ icon-size "$DOCK_ICON_SIZE" 2>/dev/null || true
gsettings set net.launchpad.plank.dock.settings:/net/launchpad/plank/docks/dock1/ hide-mode "$DOCK_HIDE_MODE" 2>/dev/null || true
gsettings set net.launchpad.plank.dock.settings:/net/launchpad/plank/docks/dock1/ zoom-enabled true 2>/dev/null || true

if ! pgrep -x plank >/dev/null; then
    nohup plank >/dev/null 2>&1 &
fi

# ------------------------------------------------------------------------------
# 7. INICIA GUARDIÃO DE TAMANHO DE JANELAS PARA TELAS 1024x600
# ------------------------------------------------------------------------------
if [ -x "/usr/local/bin/legacyos-window-fit" ] && ! pgrep -f "legacyos-window-fit" >/dev/null; then
    nohup /usr/local/bin/legacyos-window-fit --daemon >/dev/null 2>&1 &
fi

# ------------------------------------------------------------------------------
# 8. SINCRONIZAÇÃO FINAL: AGUARDA PAINEL, DESKTOP E DOCK RENDERIZAREM
# ------------------------------------------------------------------------------
if [ -x "/usr/bin/legacyos-move-icons.sh" ]; then
    sleep 0.6
    /usr/bin/legacyos-move-icons.sh >/dev/null 2>&1 || true
fi

for i in $(seq 1 15); do
    if pgrep -x xfce4-panel >/dev/null && pgrep -x xfdesktop >/dev/null && pgrep -x plank >/dev/null; then
        break
    fi
    sleep 0.3
done

# Aguarda renderização completa do wallpaper e ícones antes de revelar o desktop
sleep 2.2
rm -f "$LOCK_FILE"

if grep -qw "legacyos-install" /proc/cmdline && [ -x "/usr/local/bin/legacyos-installer" ]; then
    sleep 0.6
    /usr/local/bin/legacyos-installer >/dev/null 2>&1 &
fi

exit 0
