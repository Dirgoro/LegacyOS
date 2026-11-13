#!/bin/bash
export NO_AT_BRIDGE=1
sleep 8

# ==========================================
# 1. LIMPEZA TOTAL (Evita bugs de migração)
# ==========================================
xfce4-panel --quit || true
pkill -9 xfce4-panel 2>/dev/null || true
pkill -9 xfconfd 2>/dev/null || true
sleep 2

rm -rf ~/.cache/xfce4/panel/
rm -f ~/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-panel.xml

# ==========================================
# 2. RECONSTRUIR O PAINEL VIA CLI (100% COMPATÍVEL)
# ==========================================
# Criar o painel vazio
xfconf-query -c xfce4-panel -p /panels -n -t int -s 1
xfconf-query -c xfce4-panel -p /panels/panel-1/position -n -t string -s "p=6;x=0;y=0"
xfconf-query -c xfce4-panel -p /panels/panel-1/length -n -t uint -s 100
xfconf-query -c xfce4-panel -p /panels/panel-1/position-locked -n -t bool -s true
xfconf-query -c xfce4-panel -p /panels/panel-1/size -n -t uint -s 32
xfconf-query -c xfce4-panel -p /panels/panel-1/background-style -n -t uint -s 1
xfconf-query -c xfce4-panel -p /panels/panel-1/background-rgba -n -t double -s 0.078 -t double -s 0.113 -t double -s 0.160 -t double -s 0.85

# Plugin 1: Whisker Menu (Logo)
xfconf-query -c xfce4-panel -p /plugins/plugin-1 -n -t string -s "whiskermenu"
xfconf-query -c xfce4-panel -p /plugins/plugin-1/button-icon -n -t string -s "legacyos-logo"
xfconf-query -c xfce4-panel -p /plugins/plugin-1/show-button-title -n -t bool -s true
xfconf-query -c xfce4-panel -p /plugins/plugin-1/button-title -n -t string -s "LegacyOS"

# Plugins 2,3,4: Launchers de texto
xfconf-query -c xfce4-panel -p /plugins/plugin-2 -n -t string -s "launcher"
xfconf-query -c xfce4-panel -p /plugins/plugin-2/items -n -t string -s "aplicativos.desktop"
xfconf-query -c xfce4-panel -p /plugins/plugin-3 -n -t string -s "launcher"
xfconf-query -c xfce4-panel -p /plugins/plugin-3/items -n -t string -s "locais.desktop"
xfconf-query -c xfce4-panel -p /plugins/plugin-4 -n -t string -s "launcher"
xfconf-query -c xfce4-panel -p /plugins/plugin-4/items -n -t string -s "sistema.desktop"

# Plugin 5: Separador (empurra os ícones para a direita)
xfconf-query -c xfce4-panel -p /plugins/plugin-5 -n -t string -s "separator"
xfconf-query -c xfce4-panel -p /plugins/plugin-5/expand -n -t bool -s true

# Plugin 6: Bandeja do Sistema
xfconf-query -c xfce4-panel -p /plugins/plugin-6 -n -t string -s "systray"

# Plugin 7: Relógio
xfconf-query -c xfce4-panel -p /plugins/plugin-7 -n -t string -s "clock"
xfconf-query -c xfce4-panel -p /plugins/plugin-7/digital-format -n -t string -s "%a, %d de %b | %H:%M"

# Plugin 8: Busca
xfconf-query -c xfce4-panel -p /plugins/plugin-8 -n -t string -s "launcher"
xfconf-query -c xfce4-panel -p /plugins/plugin-8/items -n -t string -s "busca.desktop"

# Ligar todos os plugins ao painel
xfconf-query -c xfce4-panel -p /panels/panel-1/plugin-ids -n -t int -s 1 -t int -s 2 -t int -s 3 -t int -s 4 -t int -s 5 -t int -s 6 -t int -s 7 -t int -s 8

# ==========================================
# 3. APLICAR TEMA E WALLPAPER
# ==========================================
xfconf-query -c xsettings -p /Net/ThemeName -s "LegacyOS-Theme" || true
xfconf-query -c xsettings -p /Net/IconThemeName -s "LegacyOS-Icons" || true
xfconf-query -c xfwm4 -p /general/theme -s "Arc-Dark" || true

IMAGE="/usr/share/backgrounds/legacyos-wallpaper.jpg"
for monitor in "monitor0" "monitor1" "monitorVirtual-1" "Virtual-1" "monitorVGA-1"; do
    xfconf-query -c xfce4-desktop -p "/backdrop/screen0/$monitor/workspace0/last-image" -s "$IMAGE" --create -t string || true
    xfconf-query -c xfce4-desktop -p "/backdrop/screen0/$monitor/workspace0/image-style" -s 5 --create -t int || true
done

# ==========================================
# 4. CONFIGURAR E INICIAR PLANK
# ==========================================
mkdir -p ~/.local/share/plank/themes/LegacyOS-Dock/
cat << 'EOF' > ~/.local/share/plank/themes/LegacyOS-Dock/dock.theme
[PlankTheme]
BottomPadding=6
LineWidth=0
TopPadding=6
IconShadowSize=2
IconShadow=1
MaxHeight=70
TopRoundness=24
BottomRoundness=24

[PlankDockTheme]
FillStart=20;29;41;0.85
FillEnd=20;29;41;0.85
EOF

mkdir -p ~/.config/plank/dock1/launchers/
echo "[PlankDockItemPreferences]
Launcher=file:///usr/share/applications/xfce4-terminal.desktop" > ~/.config/plank/dock1/launchers/terminal.dockitem
echo "[PlankDockItemPreferences]
Launcher=file:///usr/share/applications/thunar.desktop" > ~/.config/plank/dock1/launchers/thunar.dockitem
echo "[PlankDockItemPreferences]
Launcher=file:///usr/share/applications/xfce4-appfinder.desktop" > ~/.config/plank/dock1/launchers/appfinder.dockitem

cat << 'EOF' > ~/.config/plank/dock1/settings
[PlankDockPreferences]
Position=3
Alignment=2
Theme=LegacyOS-Dock
IconSize=48
LockItems=false
HideMode=0
ShowDockItem=true
EOF

# ==========================================
# 5. INICIAR PAINEL E PLANK
# ==========================================
sleep 1
xfce4-panel &
sleep 2
pkill plank 2>/dev/null || true
plank &

# 6. Mover ícones da área de trabalho para a direita
sleep 3
/usr/bin/legacyos-move-icons.sh right 2>/dev/null || true
