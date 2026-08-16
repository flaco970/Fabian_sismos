#!/bin/bash
# push_to_github.sh — Ejecutar después de crear el repo en github.com/new
# Uso: bash push_to_github.sh <TOKEN>

if [ -z "$1" ]; then
    echo "Uso: bash push_to_github.sh <GITHUB_TOKEN>"
    exit 1
fi

cd /opt/sismos

# Si el repo no existe, crearlo via API
TOKEN=$1
echo "Creando repo Fabian_sismos..."
curl -s -X POST https://api.github.com/user/repos \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/vnd.github+json" \
  -d '{"name":"Fabian_sismos","description":"Mapa sismicidad Sudamérica + SST mensual NOAA OISST + Ecuador destacado","private":false,"auto_init":false}' | head -20

# Configurar remote HTTPS con token
git remote set-url origin https://x-access-token:$TOKEN@github.com/flaco970/Fabian_sismos.git
git push -u origin main
echo "✓ Push completo: https://github.com/flaco970/Fabian_sismos"
