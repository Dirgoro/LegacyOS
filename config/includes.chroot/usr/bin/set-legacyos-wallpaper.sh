#!/bin/bash

# Espera o xfdesktop carregar completamente
sleep 5

IMAGE="/usr/share/backgrounds/legacyos-wallpaper.jpg"

# 1. Tenta aplicar em qualquer monitor que já tenha o propriedade 'last-image'
for prop in $(xfconf-query -c xfce4-desktop -l | grep last-image); do
    xfconf-query -c xfce4-desktop -p "$prop" -s "$IMAGE"
    style_prop=$(echo "$prop" | sed 's/last-image/image-style/')
    xfconf-query -c xfce4-desktop -p "$style_prop" -s 5
done

# 2. Força a criação da propriedade para os nomes de monitores mais comuns em VMs
for monitor in "monitor0" "monitorVirtual-1" "Virtual-1" "monitor1"; do
    xfconf-query -c xfce4-desktop -p "/backdrop/screen0/$monitor/workspace0/last-image" -s "$IMAGE" --create -t string
    xfconf-query -c xfce4-desktop -p "/backdrop/screen0/$monitor/workspace0/image-style" -s 5 --create -t int
done
