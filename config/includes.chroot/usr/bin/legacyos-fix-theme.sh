#!/bin/bash
export NO_AT_BRIDGE=1
sleep 5

# 1. Copiar configurações do Painel e Tema
mkdir -p ~/.config/xfce4/xfconf/xfce-perchannel-xml/
cp -f /etc/xdg/xfce4/xfconf/xfce-perchannel-xml/*.xml ~/.config/xfce4/xfconf/xfce-perchannel-xml/ || true

# 2. Copiar launchers
mkdir -p ~/.config/xfce4/panel/launchers/
cp -f /etc/xdg/xfce4/panel/launchers/*.desktop ~/.config/xfce4/panel/launchers/ || true

# 3. Configurar a Dock (Plank) - Apenas com os apps que existem
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
rm -f ~/.config/plank/dock1/launchers/*.dockitem

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

# 4. Aplicar Wallpaper e Tema
xfconf-query -c xsettings -p /Net/ThemeName -s "LegacyOS-Theme" || true
xfconf-query -c xsettings -p /Net/IconThemeName -s "LegacyOS-Icons" || true
xfconf-query -c xfwm4 -p /general/theme -s "Arc-Dark" || true

IMAGE="/usr/share/backgrounds/legacyos-wallpaper.jpg"
for monitor in "monitor0" "monitor1" "monitorVirtual-1" "Virtual-1" "monitorVGA-1"; do
    xfconf-query -c xfce4-desktop -p "/backdrop/screen0/$monitor/workspace0/last-image" -s "$IMAGE" --create -t string || true
    xfconf-query -c xfce4-desktop -p "/backdrop/screen0/$monitor/workspace0/image-style" -s 5 --create -t int || true
done

# 5. Reiniciar Painel e Plank
xfce4-panel -r || true
if ! pgrep -x "plank" > /dev/null; then
    plank &
fi
