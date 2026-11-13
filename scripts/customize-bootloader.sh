#!/bin/bash
# ==============================================================================
# LEGACYOS - PERSONALIZAÇÃO COMPLETA DO BOOTLOADER (SYSLINUX / ISOLINUX / GRUB)
# Copia os templates oficiais do live-build para config/bootloaders e aplica
# fundo Dark Slate (#0B1120), logotipo LegacyOS e as 3 opções de boot
# ==============================================================================

set -e

echo "[LegacyOS Bootloader] Preparando templates em config/bootloaders..."
mkdir -p config/bootloaders

# Copia templates base do sistema caso ainda não existam no projeto
for SUB in isolinux syslinux grub-pc grub-efi; do
    if [ ! -d "config/bootloaders/$SUB" ] && [ -d "/usr/share/live/build/bootloaders/$SUB" ]; then
        cp -r "/usr/share/live/build/bootloaders/$SUB" "config/bootloaders/$SUB"
    fi
done

echo "[LegacyOS Bootloader] Gerando splash screen 640x480..."
SPLASH_PNG="/tmp/legacyos-boot-splash.png"
SVG_LOGO="config/includes.chroot/usr/share/pixmaps/legacyos-logo.svg"

python3 - "$SVG_LOGO" "$SPLASH_PNG" << 'PYEOF'
import os
import sys
import gi
gi.require_version("GdkPixbuf", "2.0")
gi.require_version("Gdk", "3.0")
from gi.repository import GdkPixbuf, Gdk
import cairo

svg_path = sys.argv[1]
out_png = sys.argv[2]

W, H = 640, 480
surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
ctx = cairo.Context(surface)

# Fundo Dark Slate (#0B1120) com brilho radial azul sutil no topo
ctx.set_source_rgb(0.043, 0.067, 0.125)
ctx.rectangle(0, 0, W, H)
ctx.fill()

radial = cairo.RadialGradient(W / 2.0, 90, 10, W / 2.0, 90, 340)
radial.add_color_stop_rgba(0.0, 0.008, 0.518, 0.780, 0.24)
radial.add_color_stop_rgba(1.0, 0.043, 0.067, 0.125, 0.0)
ctx.set_source(radial)
ctx.rectangle(0, 0, W, H)
ctx.fill()

# Logotipo oficial no topo central
if os.path.isfile(svg_path):
    try:
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(svg_path, 66, 66, True)
        Gdk.cairo_set_source_pixbuf(ctx, pixbuf, (W - 66) / 2.0, 30)
        ctx.paint()
    except Exception:
        pass

# Marca LegacyOS abaixo do ícone
ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
ctx.set_font_size(22)
t1, t2 = "Legacy", "OS"
e1 = ctx.text_extents(t1)
e2 = ctx.text_extents(t2)
start_x = (W - (e1.width + e2.width + 2)) / 2.0

ctx.set_source_rgb(0.973, 0.980, 0.988)
ctx.move_to(start_x, 122)
ctx.show_text(t1)

ctx.set_source_rgb(0.055, 0.647, 0.914)
ctx.move_to(start_x + e1.width + 2, 122)
ctx.show_text(t2)

# Subtítulo discreto no rodapé
ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
ctx.set_font_size(11)
sub = "Novas possibilidades para grandes historias"
esub = ctx.text_extents(sub)
ctx.set_source_rgb(0.580, 0.639, 0.722)
ctx.move_to((W - esub.width) / 2.0, 448)
ctx.show_text(sub)

surface.write_to_png(out_png)
PYEOF

# ------------------------------------------------------------------------------
# Aplica tema e entradas de boot no ISOLINUX / SYSLINUX
# ------------------------------------------------------------------------------
for DIR in config/bootloaders/isolinux config/bootloaders/syslinux; do
    if [ -d "$DIR" ]; then
        echo "[LegacyOS Bootloader] Configurando $DIR..."
        rm -f "$DIR/splash.svg"
        cp "$SPLASH_PNG" "$DIR/splash.png"

        cat << 'EOF' > "$DIR/stdmenu.cfg"
menu background splash.png
menu title LegacyOS 1.0 Alpha
menu color border       30;44      #20ffffff #00000000 std
menu color title        1;36;44    #ff38bdf8 #00000000 std
menu color sel          7;37;40    #ffffffff #ff0284c7 all
menu color unsel        37;44      #ffe2e8f0 #00000000 std
menu color help         37;40      #ff94a3b8 #00000000 std
menu color timeout_msg  37;40      #ff94a3b8 #00000000 std
menu color timeout      1;37;40    #ff38bdf8 #00000000 std
menu color msg07        37;40      #ff94a3b8 #00000000 std
menu color tabmsg       31;40      #ff64748b #00000000 std

menu width 74
menu margin 6
menu rows 7
menu tabmsgrow 21
menu cmdlinerow 21
menu endrow 23
menu timeoutrow 20
menu vshift 7
EOF

        cat << 'EOF' > "$DIR/live.cfg.in"
label live-@FLAVOUR@
	menu label ^Iniciar LegacyOS (Modo Live)
	menu default
	linux @LINUX@
	initrd @INITRD@
	append @APPEND_LIVE@

label install-@FLAVOUR@
	menu label ^Instalar o LegacyOS
	linux @LINUX@
	initrd @INITRD@
	append @APPEND_LIVE@ legacyos-install

label live-@FLAVOUR@-failsafe
	menu label LegacyOS (^Modo de Seguranca)
	linux @LINUX@
	initrd @INITRD@
	append @APPEND_LIVE@ memtest noapic noapm nodma nomce nolapic nosmp nosplash vga=788 nomodeset
EOF
    fi
done

# ------------------------------------------------------------------------------
# Aplica tema e entradas de boot no GRUB (UEFI / Hybrid)
# ------------------------------------------------------------------------------
for GDIR in config/bootloaders/grub-pc config/bootloaders/grub-efi; do
    if [ -d "$GDIR" ]; then
        echo "[LegacyOS Bootloader] Configurando $GDIR..."
        rm -f "$GDIR/splash.svg"
        cp "$SPLASH_PNG" "$GDIR/splash.png"

        cat << 'EOF' > "$GDIR/grub.cfg"
set default=0
set timeout=6

insmod all_video
insmod gfxterm
insmod png
terminal_output gfxterm

background_image /boot/grub/splash.png
set color_normal=light-gray/black
set color_highlight=white/cyan

menuentry "Iniciar LegacyOS (Modo Live)" {
	linux	@LINUX_LIVE@ @APPEND_LIVE@
	initrd	@INITRD_LIVE@
}

menuentry "Instalar o LegacyOS" {
	linux	@LINUX_LIVE@ @APPEND_LIVE@ legacyos-install
	initrd	@INITRD_LIVE@
}

menuentry "LegacyOS (Modo de Seguranca)" {
	linux	@LINUX_LIVE@ @APPEND_LIVE@ memtest noapic noapm nodma nomce nolapic nosmp nosplash vga=788 nomodeset
	initrd	@INITRD_LIVE@
}
EOF
    fi
done

rm -f "$SPLASH_PNG"
echo "[LegacyOS Bootloader] Personalização concluída com sucesso."
exit 0
