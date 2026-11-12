#!/bin/bash
CPU_MODEL=$(lscpu | grep "Model name" | awk -F':' '{print $2}' | sed 's/^ *//')
if echo "$CPU_MODEL" | grep -qiE "Atom|Celeron"; then
    sysctl -w vm.swappiness=100 > /dev/null
    sysctl -w vm.vfs_cache_pressure=50 > /dev/null
elif echo "$CPU_MODEL" | grep -qiE "Core 2|Pentium"; then
    sysctl -w vm.swappiness=60 > /dev/null
fi
