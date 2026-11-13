#!/bin/bash
# ==============================================================================
# LEGACYOS - PROVISIONAMENTO AUTOMÁTICO DE SWAP NO SSD (2 GB)
# Cria /swapfile apenas quando o sistema está instalado em disco real
# ==============================================================================

SWAPFILE="/swapfile"
SWAP_SIZE_MB=2048

# 1. Aborta se estiver rodando em modo LiveCD/LiveUSB (evita consumir RAM)
if grep -q "boot=live" /proc/cmdline || mount | grep -q " on / type overlay"; then
    exit 0
fi

# 2. Aborta se o swapfile já existir e estiver configurado
if [ -f "$SWAPFILE" ]; then
    swapon --show | grep -q "$SWAPFILE" || swapon -p 10 "$SWAPFILE"
    exit 0
fi

# 3. Verifica se há pelo menos 6 GB livres na partição raiz antes de alocar 2 GB
FREE_MB=$(df -m / | awk 'NR==2 {print $4}')
if [ "$FREE_MB" -lt 6144 ]; then
    exit 0
fi

# 4. Cria e ativa o swapfile com prioridade 10 (abaixo da zRAM)
dd if=/dev/zero of="$SWAPFILE" bs=1M count="$SWAP_SIZE_MB" status=none
chmod 600 "$SWAPFILE"
mkswap "$SWAPFILE" >/dev/null 2>&1
swapon -p 10 "$SWAPFILE"

# 5. Registra no /etc/fstab para persistir nos próximos boots
if ! grep -q "$SWAPFILE" /etc/fstab; then
    echo "$SWAPFILE none swap sw,pri=10 0 0" >> /etc/fstab
fi

exit 0
