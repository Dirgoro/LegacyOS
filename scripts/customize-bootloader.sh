#!/bin/bash
# ==============================================================================
# LEGACYOS - PERSONALIZAÇÃO COMPLETA DO BOOTLOADER (SYSLINUX / ISOLINUX / GRUB)
# ==============================================================================

set -e

echo "[LegacyOS Bootloader] Preparando templates em config/bootloaders..."
mkdir -p config/bootloaders

for SUB in isolinux syslinux grub-pc grub-efi; do
    if [ ! -d "config/bootloaders/$SUB" ] && [ -d "/usr/share/live/build/bootloaders/$SUB" ]; then
        cp -r "/usr/share/live/build/bootloaders/$SUB" "config/bootloaders/$SUB"
    fi
done

echo "[LegacyOS Bootloader] Gerando splash screen 640x480..."
SPLASH_PNG="/tmp/legacyos-boot-splash.png"

python3 - "$SPLASH_PNG" << 'PYEOF'
import sys
import cairo

out_png = sys.argv[1]

W, H = 640, 480
surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
ctx = cairo.Context(surface)

# 1. Fundo Dark Slate (#0B1120) com brilho radial azul sutil no topo
ctx.set_source_rgb(0.043, 0.067, 0.125)
ctx.rectangle(0, 0, W, H)
ctx.fill()

radial = cairo.RadialGradient(W / 2.0, 88, 10, W / 2.0, 88, 340)
radial.add_color_stop_rgba(0.0, 0.008, 0.518, 0.780, 0.24)
radial.add_color_stop_rgba(1.0, 0.043, 0.067, 0.125, 0.0)
ctx.set_source(radial)
ctx.rectangle(0, 0, W, H)
ctx.fill()

# 2. Logotipo vetorial oficial do LegacyOS
ctx.save()
scale = 0.68
logo_w = 100.0 * scale
ctx.translate((W - logo_w) / 2.0, 26.0)
ctx.scale(scale, scale)

grad_v = cairo.LinearGradient(65, 5, 20, 95)
grad_v.add_color_stop_rgb(0.0, 0.878, 0.949, 0.996)
grad_v.add_color_stop_rgb(0.35, 0.220, 0.741, 0.973)
grad_v.add_color_stop_rgb(0.72, 0.008, 0.518, 0.780)
grad_v.add_color_stop_rgb(1.0, 0.000, 0.278, 0.671)
ctx.set_source(grad_v)
ctx.move_to(18, 92)
ctx.line_to(18, 42)
ctx.curve_to(18, 24, 30, 12, 46, 8)
ctx.line_to(46, 68)
ctx.curve_to(34, 73, 24, 81, 18, 92)
ctx.close_path()
ctx.fill()

grad_h = cairo.LinearGradient(10, 90, 92, 55)
grad_h.add_color_stop_rgb(0.0, 0.392, 0.455, 0.545)
grad_h.add_color_stop_rgb(0.35, 0.796, 0.835, 0.882)
grad_h.add_color_stop_rgb(0.75, 0.945, 0.961, 0.976)
grad_h.add_color_stop_rgb(1.0, 1.000, 1.000, 1.000)
ctx.set_source(grad_h)
ctx.move_to(18, 92)
ctx.curve_to(26, 75, 38, 66, 56, 66)
ctx.line_to(92, 66)
ctx.curve_to(88, 82, 76, 92, 58, 92)
ctx.line_to(18, 92)
ctx.close_path()
ctx.fill()
ctx.restore()

# 3. Marca LegacyOS abaixo do ícone
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

# 4. Subtítulo discreto acima das instruções de tecla (sem sobreposição)
ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
ctx.set_font_size(11)
sub = "Novas possibilidades para grandes historias"
esub = ctx.text_extents(sub)
ctx.set_source_rgb(0.580, 0.639, 0.722)
ctx.move_to((W - esub.width) / 2.0, 388)
ctx.show_text(sub)

surface.write_to_png(out_png)
PYEOF

for DIR in config/bootloaders/isolinux config/bootloaders/syslinux; do
    if [ -d "$DIR" ]; then
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
menu rows 6
menu tabmsgrow 22
menu cmdlinerow 22
menu endrow 24
menu timeoutrow 21
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

for GDIR in config/bootloaders/grub-pc config/bootloaders/grub-efi; do
    if [ -d "$GDIR" ]; then
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
exit 0
