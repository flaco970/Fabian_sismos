#!/bin/bash
# traffic_monitor.sh — Monitorea tráfico del túnel/servidor
# Uso: bash traffic_monitor.sh [--continuous] [--interval 60]

INTERVAL=${INTERVAL:-60}
CONTINUOUS=""
if [ "$1" == "--continuous" ]; then
    CONTINUOUS="yes"
fi

log_file="/var/log/sismos_traffic.log"
mkdir -p "$(dirname "$log_file")"

# Detectar puerto del http.server local
PORT=$(ss -tlnp 2>/dev/null | grep ":8765" | head -1 | grep -oP 'pid=\K[0-9]+' | head -1)
if [ -z "$PORT" ]; then
    PORT=$(netstat -tlnp 2>/dev/null | grep ":8765" | head -1 | awk '{print $7}' | cut -d/ -f1)
fi

if [ -z "$PORT" ]; then
    echo "⚠ No se encontró http.server activo en :8765"
    exit 1
fi

echo "=== Monitoreo de tráfico (puerto 8765, PID $PORT) ==="
echo "Intervalo: ${INTERVAL}s"
echo "Log: $log_file"
echo ""

while true; do
    # Stats de red del proceso
    net=$(cat /proc/$PORT/net/tcp 2>/dev/null)
    
    # Conexiones activas al puerto
    active=$(ss -tn state established "( sport = :8765 or dport = :8765 )" 2>/dev/null | wc -l)
    
    # Bytes transmitidos (acumulado desde start)
    bytes_out=$(cat /proc/$PORT/net/dev 2>/dev/null | grep -v lo | head -1 | awk '{print $10}')
    
    # HTTP server access (si redirigimos a un log)
    requests_per_min=$(wc -l < "$log_file" 2>/dev/null || echo 0)
    
    # CPU/RAM del proceso
    cpu_mem=$(ps -p $PORT -o %cpu,%mem,rss --no-headers 2>/dev/null)
    
    timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    echo "[$timestamp] active_conns=$active, cpu_mem=$cpu_mem, log_lines=$requests_per_min" | tee -a "$log_file"
    
    # Alerta si hay >50 conexiones simultáneas
    if [ "$active" -gt 50 ] 2>/dev/null; then
        echo "⚠ ALERTA: $active conexiones activas (>50)" | tee -a "$log_file"
        # Aquí podrías enviar un Telegram message
    fi
    
    [ -n "$CONTINUOUS" ] || break
    sleep "$INTERVAL"
done

echo ""
echo "=== Stats Cloudflare (si tienes cuenta) ==="
echo "Si quieres tráfico exacto, conecta el dominio custom y revisa:"
echo "  https://dash.cloudflare.com → Analytics → fabian-sismos.pages.dev"