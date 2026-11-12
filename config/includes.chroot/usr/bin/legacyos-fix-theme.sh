#!/bin/bash
sleep 5

# 1. Aplicar Tema GTK e Ícones
xfconf-query -c xsettings -p /Net/ThemeName -s "LegacyOS-Theme" || true
xfconf-query -c xsettings -p /Net/IconThemeName -s "LegacyOS-Icons" || true

# 2. Aplicar Tema das Janelas (XFWM4)
xfconf-query -c xfwm4 -p /general/theme -s "Arc-Dark" || true

# 3. Aplicar Papel de Parede (Varrendo todos os monitores)
IMAGE="/usr/share/backgrounds/legacyos-wallpaper.jpg"
for prop in $(xfconf-query -c xfce4-desktop -l | grep last-image); do
    xfconf-query -c xfce4-desktop -p "$prop" -s "$IMAGE"
    style_prop=$(echo "$prop" | sed 's/last-image/image-style/')
    xfconf-query -c xfce4-desktop -p "$style_prop" -s 5
done

# 4. Matar o Plank padrão e reiniciar com o Tema Customizado
pkill plank || true
sleep 1
plank --theme=LegacyOS-Dock & 

# 5. Matar o Painel padrão e reiniciar para carregar o nosso xfce4-panel.xml
pkill xfce4-panel || true
sleep 1
xfce4-panel &
