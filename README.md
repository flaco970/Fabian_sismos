# 🌎 Fabian_sismos

Mapa interactivo de sismicidad en **Sudamérica** con **temperatura oceánica mensual** sincronizada por slider temporal.

![Stack](https://img.shields.io/badge/Python-3.11+-blue) ![SQLite](https://img.shields.io/badge/Storage-SQLite-green) ![License](https://img.shields.io/badge/Data-USGS%20%2B%20NOAA-lightgrey)

## ¿Qué hace?

Visualiza **2232 sismos M4.5+** de los últimos 3 años en Sudamérica extendida sobre un mapa interactivo con:

- 🟠 Bordes de **placas tectónicas** (Bird 2003)
- 🟢 **Ecuador continental + Galápagos** destacados
- 🌡 **Temperatura superficial del océano** mensual (NOAA OISST v2)
- 🎬 **Slider temporal** con ventana móvil de 3 meses
- ▶ Botón play para reproducir la evolución mes a mes
- 📊 Histograma de actividad mensual

## Demo

URL fija: `https://fabian-sismos.pages.dev` *(próximamente — ver [Deploy](#deploy))*

## Arquitectura

```
┌─────────────────────────────────────────────────────────┐
│  VPS (srv1469580)                                       │
│  ┌──────────┐    ┌──────────┐    ┌─────────────────┐   │
│  │ ingest.py│ →  │ sismos.db│ ←  │  export_html.py │   │
│  │ (USGS)   │    │ (SQLite) │    │  (renderer)     │   │
│  └──────────┘    └────┬─────┘    └────────┬────────┘   │
│                       │                   │             │
│                       ↓                   ↓             │
│                ┌─────────────┐     ┌────────────┐      │
│                │ events      │     │ sst_pngs/  │      │
│                │ ingest_log  │     │ (37 meses) │      │
│                │ meta        │     │            │      │
│                └─────────────┘     └────────────┘      │
│                       │                   │             │
│                       └─────────┬─────────┘             │
│                                 ↓                       │
│                          ┌──────────────┐               │
│                          │ web/         │               │
│                          │ index.html   │               │
│                          │ (~1 MB)      │               │
│                          └──────┬───────┘               │
└─────────────────────────────────┼───────────────────────┘
                                  ↓
                          ┌──────────────┐
                          │ Cloudflare   │
                          │ Pages (CDN)  │
                          └──────┬───────┘
                                 ↓
                          👥 Usuarios
```

## Estructura

```
Fabian_sismos/
├── data/
│   ├── sismos.db              # SQLite: 2232 eventos + log + meta
│   ├── sst_pngs/              # 37 PNGs mensuales (NOAA OISST)
│   ├── sst_manifest.json      # metadata de los PNGs
│   ├── sst_monthly.json       # raw data SST en JSON
│   ├── ecuador.geojson        # polígono Ecuador + Galápagos
│   └── plates.geojson         # bordes de placa Bird 2003
├── build/
│   ├── ingest.py              # USGS → SQLite
│   ├── export_html.py         # SQLite + SST → HTML
│   ├── leaflet_embebido/      # Leaflet 1.9.4 CSS+JS (163 KB)
│   └── ingest_sst.py          # NOAA OISST → PNGs (manual)
├── web/
│   └── index.html             # HTML generado (~1 MB single-file)
├── docs/
│   ├── upgrade.md             # cómo crecer (más tiempo, más región)
│   ├── analisis.md            # queries SQL útiles, patrones
│   └── investigacion.md       # fuentes científicas, referencias
├── scripts/
│   ├── update.sh              # cron de actualización
│   └── traffic_monitor.sh     # monitoreo de uso
└── README.md                  # este archivo
```

## Quick start

### Requisitos

- Python 3.11+
- Pillow (`pip install Pillow`)
- Conexión a internet (USGS + NOAA)

### 1. Ingerir datos sísmicos

```bash
cd /opt/sismos
python3 build/ingest.py --region sudamerica_ext --years 3 --min-mag 4.5
```

Regiones disponibles: `sudamerica_ext`, `sudamerica`, `ecuador`, `nazca_subduction`, `andes`, `mundial`.

### 2. (Opcional) Actualizar SST

```bash
python3 build/ingest_sst.py  # solo si necesitas refrescar los PNGs mensuales
```

### 3. Regenerar HTML

```bash
python3 build/export_html.py --window 3
# → web/index.html
```

### 4. Servir localmente

```bash
cd web && python3 -m http.server 8765
# → http://localhost:8765/
```

## Deploy

Ver [docs/deploy.md](docs/deploy.md) — Cloudflare Pages con URL fija + dominio custom opcional.

## Contribuir / Mejorar

Ver [docs/upgrade.md](docs/upgrade.md) — cómo agregar features (alertas, clusters, más placas, etc.).

## Análisis de datos

Ver [docs/analisis.md](docs/analisis.md) — queries SQL, gráficos, comparaciones temporales.

## Investigación

Ver [docs/investigacion.md](docs/investigacion.md) — fuentes científicas, papers, datos adicionales.

## Licencia

Datos:
- USGS earthquakes: dominio público (USGS)
- NOAA OISST: dominio público (NOAA)
- Bird 2003 plates: académico, citar como Bird (2003)

Código: MIT.

## Fuentes

[1] USGS Earthquake Hazards Program — https://earthquake.usgs.gov
[2] Bird (2003) — An updated digital model of plate boundaries
[3] NOAA OISST v2.1 — https://psl.noaa.gov/data/gridded/data.noaa.oisst.v2.highres.html