#!/bin/bash
# update.sh — Actualización completa: datos + HTML + commit
# Pensado para correr manualmente o en cron

set -e
cd "$(dirname "$0")/.."

echo "=== Actualización $(date) ==="

# 1. Ingerir datos USGS
echo "[1/4] Ingesta USGS..."
python3 build/ingest.py --region sudamerica_ext --years 3 --min-mag 4.5

# 2. (Opcional) Ingerir SST si no está fresco
if [ ! -f "data/sst_pngs/sst_$(date +%Y-%m).png" ]; then
    echo "[2/4] Ingerir SST..."
    python3 build/ingest_sst.py
else
    echo "[2/4] SST ya está al día"
fi

# 3. Regenerar HTML
echo "[3/4] Export HTML..."
python3 build/export_html.py --window 3

# 4. Stats
echo "[4/4] Stats:"
n_events=$(sqlite3 data/sismos.db "SELECT COUNT(*) FROM events" 2>/dev/null)
n_meses=$(ls data/sst_pngs/*.png 2>/dev/null | wc -l)
html_size=$(du -h web/index.html | cut -f1)
echo "  Eventos: $n_events"
echo "  Meses SST: $n_meses"
echo "  HTML size: $html_size"
echo ""

# Si hay git configurado, commit
if [ -d .git ]; then
    git add data/ web/index.html
    if ! git diff --cached --quiet; then
        git commit -m "update $(date +%Y-%m-%d): ${n_events} eventos"
        echo "Commit creado. Push manual con: git push"
    else
        echo "Sin cambios para commitear"
    fi
fi

echo "=== Listo ==="