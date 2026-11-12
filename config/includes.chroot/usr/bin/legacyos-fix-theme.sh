#!/bin/bash
# Evita warnings do DBus
export NO_AT_BRIDGE=1
sleep 3

# ==========================================
# 1. FORÇAR A CÓPIA DAS CONFIGURAÇÕES GLOBAIS
# ==========================================
mkdir -p ~/.config/xfce4/xfconf/xfce-perchannel-xml/
cp -f /etc/xdg/xfce4/xfconf/xfce-perchannel-xml/xfce4-panel.xml ~/.config/xfce4/xfconf/xfce-perchannel-xml/ || true
cp -f /etc/xdg/xfce4/xfconf/xfce-perchannel-xml/xsettings.xml ~/.config/xfce4/xfconf/xfce-perchannel-xml/ || true
cp -f /etc/xdg/xfce4/xfconf/xfce-perchannel-xml/xfwm4.xml ~/.config/xfce4/xfconf/xfce-perchannel-xml/ || true

# Copiar os launchers do painel para o usuário
mkdir -p ~/.config/xfce4/panel/launchers/
cp -f /etc/xdg/xfce4/panel/launchers/*.desktop ~/.config/xfce4/panel/launchers/ || true

# ==========================================
# 2. FORÇAR A CÓPIA DA DOCK (PLANK)
# ==========================================
mkdir -p ~/.config/plank/dock1/launchers/
cp -f /etc/skel/.config/plank/dock1/launchers/*.dockitem ~/.config/plank/dock1/launchers/ || true
# Criar a configuração básica do Plank (caso não exista)
mkdir -p ~/.config/plank/dock1/
echo "[PlankDockPreferences]
Position=3
Alignment=2
Theme=LegacyOS-Dock
IconSize=48
LockItems=false
HideMode=0" > ~/.config/plank/dock1/settings

# ==========================================
# 3. APLICAR TEMAS E WALLPAPER
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
# 4. REINICIAR PAINEL E DOCK
# ==========================================
pkill xfce4-panel || true
pkill plank || true
sleep 2

xfce4-panel &
plank --theme=LegacyOS-Dock & 
