#!/bin/bash
# ==============================================================================
# LEGACYOS - SCRIPT DE ESTABILIZAÇÃO DE BOOT, PAINEL, WALLPAPER E DOCK
# Base: Debian 13 (Trixie) / XFCE 4.18
# ==============================================================================

# Garante que as variáveis de sessão gráfica estejam disponíveis
export DISPLAY="${DISPLAY:-:0}"

# Aguarda o xfconfd e a sessão XFCE estabilizarem antes de injetar configurações
sleep 2

# ------------------------------------------------------------------------------
# 1. CONSTRUÇÃO SEGURA DO PAINEL SUPERIOR (TOP BAR) VIA XFCONF-QUERY
# ------------------------------------------------------------------------------
# Encerra o painel silenciosamente sem usar 'xfce4-panel -q' (evita erro D-Bus)
pkill -x xfce4-panel 2>/dev/null || true
sleep 0.5

# Limpa o canal do painel para evitar conflitos de tipagem (guint vs gint)
xfconf-query -c xfce4-panel -p / -r -R 2>/dev/null || true

# Cria o Painel 1 (Barra Superior)
xfconf-query -c xfce4-panel -p /panels -n -t int -s 1 --force-array
xfconf-query -c xfce4-panel -p /panels/panel-1/position -n -t string -s "p=6;x=0;y=0"
xfconf-query -c xfce4-panel -p /panels/panel-1/position-locked -n -t bool -s true
xfconf-query -c xfce4-panel -p /panels/panel-1/size -n -t uint -s 30
xfconf-query -c xfce4-panel -p /panels/panel-1/length -n -t double -s 100.0
xfconf-query -c xfce4-panel -p /panels/panel-1/length-adjust -n -t bool -s true
xfconf-query -c xfce4-panel -p /panels/panel-1/background-style -n -t uint -s 1
xfconf-query -c xfce4-panel -p /panels/panel-1/background-rgba -n \
    -t double -s 0.05 -t double -s 0.08 -t double -s 0.13 -t double -s 0.92

# Plugin 1: Menu Principal (LegacyOS / Aplicativos)
xfconf-query -c xfce4-panel -p /plugins/plugin-1 -n -t string -s "applicationsmenu"
xfconf-query -c xfce4-panel -p /plugins/plugin-1/button-title -n -t string -s "LegacyOS"
xfconf-query -c xfce4-panel -p /plugins/plugin-1/show-button-title -n -t bool -s true
xfconf-query -c xfce4-panel -p /plugins/plugin-1/button-icon -n -t string -s "distributor-logo"

# Plugin 2: Menu de Locais (Pastas)
xfconf-query -c xfce4-panel -p /plugins/plugin-2 -n -t string -s "directorymenu"
xfconf-query -c xfce4-panel -p /plugins/plugin-2/base-directory -n -t string -s "$HOME"

# Plugin 3: Separador Expansível (Empurra ícones de status para a direita)
xfconf-query -c xfce4-panel -p /plugins/plugin-3 -n -t string -s "separator"
xfconf-query -c xfce4-panel -p /plugins/plugin-3/expand -n -t bool -s true
xfconf-query -c xfce4-panel -p /plugins/plugin-3/style -n -t uint -s 0

# Plugin 4: Bandeja do Sistema (Wi-Fi / Legacy Guardian)
xfconf-query -c xfce4-panel -p /plugins/plugin-4 -n -t string -s "systray"
xfconf-query -c xfce4-panel -p /plugins/plugin-4/square-icons -n -t bool -s true
xfconf-query -c xfce4-panel -p /plugins/plugin-4/icon-size -n -t int -s 18

# Plugin 5: Controle de Áudio (PulseAudio / PipeWire)
xfconf-query -c xfce4-panel -p /plugins/plugin-5 -n -t string -s "pulseaudio"
xfconf-query -c xfce4-panel -p /plugins/plugin-5/enable-keyboard-shortcuts -n -t bool -s true

# Plugin 6: Gerenciador de Energia / Bateria
xfconf-query -c xfce4-panel -p /plugins/plugin-6 -n -t string -s "power-manager-plugin"

# Plugin 7: Relógio e Data
xfconf-query -c xfce4-panel -p /plugins/plugin-7 -n -t string -s "clock"
xfconf-query -c xfce4-panel -p /plugins/plugin-7/digital-layout -n -t uint -s 3
xfconf-query -c xfce4-panel -p /plugins/plugin-7/digital-time-format -n -t string -s "%a, %d de %b  %H:%M"

# Plugin 8: Menu de Sistema / Sessão (Encerrar, Bloquear)
xfconf-query -c xfce4-panel -p /plugins/plugin-8 -n -t string -s "actions"
xfconf-query -c xfce4-panel -p /plugins/plugin-8/appearance -n -t uint -s 0

# Vincula todos os plugins ao Painel 1 na ordem exata
xfconf-query -c xfce4-panel -p /panels/panel-1/plugin-ids -n \
    -t int -s 1 -t int -s 2 -t int -s 3 -t int -s 4 \
    -t int -s 5 -t int -s 6 -t int -s 7 -t int -s 8 --force-array

# Inicia o painel em segundo plano
nohup xfce4-panel >/dev/null 2>&1 &

# ------------------------------------------------------------------------------
# 2. APLICAÇÃO DINÂMICA DO PAPEL DE PAREDE (CORRIGE TELA PRETA EM VMs)
# ------------------------------------------------------------------------------
WALLPAPER=""
for DIR in "/usr/share/backgrounds/legacyos" "/usr/share/backgrounds"; do
    if [ -d "$DIR" ]; then
        FOUND=$(find "$DIR" -maxdepth 2 -type f \( -iname "*legacy*" -o -iname "*wallpaper*" -o -iname "*.jpg" -o -iname "*.png" \) ! -iname "*xfce*" | head -n 1)
        if [ -n "$FOUND" ]; then
            WALLPAPER="$FOUND"
            break
        fi
    fi
done

if [ -n "$WALLPAPER" ]; then
    # Coleta monitores ativos via xrandr e inclui fallbacks comuns de VMs
    DETECTED_MONITORS=$(xrandr --query 2>/dev/null | awk '/ connected/{print "monitor"$1}')
    ALL_MONITORS=$(echo -e "${DETECTED_MONITORS}\nmonitor0\nmonitorVirtual-1\nmonitorVirtual1\nmonitorVGA-1\nmonitorVGA1\nmonitorHDMI-1\nmonitoreDP-1" | sort -u)

    for MON in $ALL_MONITORS; do
        [ -z "$MON" ] && continue
        xfconf-query -c xfce4-desktop -p "/backdrop/screen0/${MON}/workspace0/color-style" -n -t int -s 0
        xfconf-query -c xfce4-desktop -p "/backdrop/screen0/${MON}/workspace0/image-style" -n -t int -s 5
        xfconf-query -c xfce4-desktop -p "/backdrop/screen0/${MON}/workspace0/last-image" -n -t string -s "$WALLPAPER"
    done
fi

# Garante que o xfdesktop esteja ativo e recarregado
if ! pgrep -x xfdesktop >/dev/null; then
    nohup xfdesktop >/dev/null 2>&1 &
    sleep 1
else
    xfdesktop --reload 2>/dev/null || true
fi

# ------------------------------------------------------------------------------
# 3. TEMA GTK E DOCK (PLANK)
# ------------------------------------------------------------------------------
xfconf-query -c xsettings -p /Net/ThemeName -n -t string -s "LegacyOS-Theme" 2>/dev/null || true
xfconf-query -c xfwm4 -p /general/theme -n -t string -s "LegacyOS-Theme" 2>/dev/null || true

if [ -d "/usr/share/plank/themes/LegacyOS-Dock" ]; then
    gsettings set net.launchpad.plank.dock.settings:/net/launchpad/plank/docks/dock1/ theme 'LegacyOS-Dock' 2>/dev/null || true
fi
gsettings set net.launchpad.plank.dock.settings:/net/launchpad/plank/docks/dock1/ icon-size 44 2>/dev/null || true
gsettings set net.launchpad.plank.dock.settings:/net/launchpad/plank/docks/dock1/ zoom-enabled true 2>/dev/null || true

if ! pgrep -x plank >/dev/null; then
    nohup plank >/dev/null 2>&1 &
fi

# ------------------------------------------------------------------------------
# 4. ALINHAMENTO DOS ÍCONES DA ÁREA DE TRABALHO
# ------------------------------------------------------------------------------
if [ -x "/usr/bin/legacyos-move-icons.sh" ]; then
    sleep 1
    /usr/bin/legacyos-move-icons.sh >/dev/null 2>&1 &
fi

exit 0
