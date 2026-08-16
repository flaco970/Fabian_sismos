# 🔧 Cómo mejorar / escalar el proyecto

Esta guía documenta cómo crecer el proyecto en distintas dimensiones: más datos, más regiones, más features, mejor performance.

## Sumario rápido

| Si querés... | Hacé esto |
|---|---|
| Más años de historia | `python3 ingest.py --years 10` |
| Mundial completo | `python3 ingest.py --region mundial --years 5` |
| Filtrar por magnitud mínima | `python3 ingest.py --min-mag 5.5` |
| Solo Nazca subducción | `python3 ingest.py --region nazca_subduction` |
| Más resolución SST | Editar `ingest_sst.py` → `LAT_STEP=2, LON_STEP=2` |
| Agregar placa Antártica | Ver "Placas adicionales" abajo |
| Clustering de sismos | Ver "Leaflet.markercluster" abajo |
| Alertas en tiempo real | Ver "Push notifications" abajo |
| Cachear tiles del navegador | Service Worker (offline mode) |

---

## 1. Crecer el dataset sísmico

### Cambio simple: más años

```bash
# 10 años de historia en lugar de 3
python3 build/ingest.py --region sudamerica_ext --years 10 --min-mag 4.5
```

Performance: 10 años × 700/año = ~7000 eventos → DB 2 MB → queries <5 ms. OK.

### Mundial, sin filtro geográfico

```bash
# Mundial, 5 años, M5+ (filtra los pequeños globales)
python3 build/ingest.py --region mundial --years 5 --min-mag 5.0
```

Cuidado: mundial × 5 años × M5+ = ~80,000 eventos. HTML pesa ~25 MB. **No sirve para el iPhone directo** — necesitarás fragmentar.

### Solución para HTML grande: paginación por año

Modificar `export_html.py` para generar **un HTML por año**:

```python
# build/export_year.py
import argparse
from pathlib import Path
import sys; sys.path.insert(0, str(Path(__file__).parent))
from export_html import build_html  # refactorizar a función pura

if __name__ == "__main__":
    for year in [2023, 2024, 2025, 2026]:
        # Filtrar por año y regenerar
        ...
```

Más simple: agregar un índice HTML con `<select>` que cargue cada año en un iframe.

---

## 2. Mejorar la SST

### Más resolución

Por defecto bajamos **1 punto cada 1°** (step=4 en el grid de 0.25°). Para más detalle:

```python
# En build/ingest_sst.py
LAT_STEP, LON_STEP = 2, 2   # 1 punto cada 0.5° → 182×121 = 22,000 puntos/mes
```

PNG resultante ~30 KB c/u, total ~1.1 MB para 37 meses. Aceptable.

### SST en tiempo real (NOAA Coral Reef Watch)

NOAA publica **SST diaria** vía WMS:

```
https://coralreefwatch.noaa.gov/erddap/griddap/NOAA_DHW.png?sst%5B...%5D
```

Cambiar `ingest_sst.py` para bajar el último día en vez del último mes.

### Anomalías (calor fuera de lo normal)

Comparar contra el promedio 1982-2010. Útil para sismicidad inducida (estudios muestran correlación).

```python
# build/ingest_sst_anomaly.py
# 1. Bajar climatología 1982-2010 promedio mensual
# 2. Por cada mes del rango: anomaly = sst - climatology[month]
# 3. Renderizar con paleta divergente (azul=frío, rojo=cálido)
```

---

## 3. Placas tectónicas

### Placas micro (no incluidas por defecto)

Bird (2003) tiene 52 placas, no solo las mayores. Para ver todas las microplacas (Nazca, Cocos, Juan de Fuca, Philippine, etc.):

```python
# En export_html.py — load_plates() ya baja todas, solo cambiá el style
style: {color: '#ff6b35', weight: 1.0, opacity: 0.6}  # más sutil
```

### Placas con nombre en tooltip

Ya están. Cada polyline tiene `properties.name` con formato `Nazca/South American`.

### Velocidad relativa de placas (animación)

Hay datasets (NUVEL-1A, MORVEL56) con velocidades relativas. Para visualizar:

1. Tabla con vectores de velocidad por placa
2. Renderizar flechas (arrows) sobre el mapa
3. Animar con `setInterval` (1 cm/año es lentísimo → acelerar 1e6× para ver)

---

## 4. Features del frontend

### Clustering de sismos (cuando hay muchos)

Si pasás de **1000 sismos visibles simultáneos**, agregar:

```html
<!-- Después del Leaflet JS -->
<script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
```

```javascript
// Reemplazar L.geoJSON(...) por L.markerClusterGroup
const cluster = L.markerClusterGroup({...});
const markers = [];
for (const e of EVENTS) {
    const m = L.marker([e.lat, e.lon]); // no circleMarker
    cluster.addLayer(m);
}
map.addLayer(cluster);
```

Pero **NO usar CDN** porque el webview de Telegram lo bloquea. Mejor descargar `leaflet.markercluster.js` a `build/leaflet_embebido/` y embeberlo igual que Leaflet.

### Heatmap (densidad)

```html
<script src="leaflet-heatmap.js"></script>
```

Mejor para visualizar zonas de alta actividad sin ver cada punto individual.

### Popup mejorado: imagen del epicentro

Para M5+: cross-reference con **fotos satelitales** vía Mapbox Static API (necesita token, gratis hasta 100k/mes).

---

## 5. Backend upgrades

### Cron job de actualización

```bash
# /etc/cron.d/sismos-update
0 4 * * 1  root  cd /opt/sismos && python3 build/ingest.py --region sudamerica_ext --years 3 && python3 build/export_html.py && git -C /opt/sismos add -A && git commit -m "weekly update" && git push
```

Cada lunes a las 4 AM: actualiza USGS → regenera HTML → push a GitHub → Cloudflare Pages redesploy automático.

### BDD más grande

Si pasás de **1M eventos** (50+ años mundial M2.5+):

- SQLite aguanta con índices espaciales (R-tree module)
- O migrar a PostgreSQL/PostGIS:
  ```sql
  CREATE EXTENSION postgis;
  CREATE TABLE events (..., geom GEOMETRY(Point, 4326));
  CREATE INDEX events_geom ON events USING GIST(geom);
  ```
  Queries espaciales 100× más rápidas que `lat BETWEEN x AND y`.

### Caché de tiles

Si el HTML recibe tráfico repetido desde las mismas zonas, cachear tiles CartoDB localmente:

```bash
# Tile server local con mbtiles o tilestache
pip install tilestache
```

---

## 6. Visualizaciones adicionales

### Sección transversal (cross-section)

Para visualizar el ángulo de subducción de Nazca bajo Sudamérica:

```javascript
// Línea perpendicular a la costa en latitud X
// Plotear profundidad vs distancia → ver el slab de Nazca
```

### Películas animadas

Exportar secuencia de PNGs por mes (ya los tenés en `sst_pngs/`) → concatenar con `ffmpeg`:

```bash
ffmpeg -framerate 2 -pattern_type glob -i 'sst_*.png' -c:v libx264 sst_movie.mp4
```

### Comparación con magnitud sismos histórica

Cruzar con catálogo PREP (Prevención Sísmica) de Ecuador si está disponible públicamente.

---

## 7. Internacionalización

El HTML está hardcoded en español. Para multi-idioma:

```javascript
const i18n = {
  es: {play: "▶", sismos: "sismos", ...},
  en: {play: "▶", sismos: "earthquakes", ...}
};
document.documentElement.lang = 'es';
```

---

## 8. Testing

No hay tests todavía. Para agregar:

```python
# tests/test_ingest.py
def test_ingest_returns_events():
    ...
def test_event_count_matches_usgs():
    ...
```

---

## 9. Performance benchmarks

Estado actual (3 años, M4.5+ Sudamérica extendida):

| Métrica | Valor |
|---|---|
| Eventos en DB | 2232 |
| Tamaño SQLite | 700 KB |
| Tamaño HTML | 1 MB |
| Query "todos los eventos" | 0.5 ms |
| Query "eventos Ecuador bbox" | 0.0 ms |
| Render inicial (Chrome desktop) | 1.2 s |
| Render inicial (Safari iPhone) | 2.5 s |
| Cambio de mes en slider | <100 ms |

Para proyectar crecimiento:

| Escenario | DB | HTML | Render iPhone |
|---|---|---|---|
| 10 años | 2 MB | 3 MB | 5 s |
| 30 años | 5 MB | 8 MB | 12 s (lento) |
| Mundial 5 años M5+ | 12 MB | 20 MB | NO FUNCIONA |

**Límite práctico para el iPhone**: ~3 MB HTML, ~5000 eventos visibles.

---

## 10. Próximos pasos sugeridos (roadmap)

- [ ] Clustering con Leaflet.markercluster (cuando crezca)
- [ ] SST anomaly vs climatología
- [ ] Sección transversal del slab de Nazca
- [ ] Comparación con sismicidad histórica PREP Ecuador
- [ ] API REST para consultar `sismos.db` directamente
- [ ] WebSocket para sismos en tiempo real
- [ ] Machine learning: predicción simple de réplicas
- [ ] App nativa iOS/Android con el HTML empaquetado (Capacitor)