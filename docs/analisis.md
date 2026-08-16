# 📊 Análisis de datos — queries SQL y patrones

Esta guía muestra cómo extraer información útil de `data/sismos.db` directamente con SQL.

## Conexión rápida

```bash
sqlite3 /opt/sismos/data/sismos.db
```

## Queries básicas

### Conteo por rango de magnitud

```sql
SELECT
    CASE
        WHEN mag >= 7 THEN '7+'
        WHEN mag >= 6 THEN '6-6.9'
        WHEN mag >= 5 THEN '5-5.9'
        ELSE '4.5-4.9'
    END AS bucket,
    COUNT(*) AS n
FROM events
GROUP BY bucket
ORDER BY bucket DESC;
```

Resultado típico:
```
7+|6
6-6.9|41
5-5.9|460
4.5-4.9|1727
```

### Sismos por mes (para histogramas)

```sql
SELECT
    strftime('%Y-%m', time_ms/1000, 'unixepoch') AS ym,
    COUNT(*) AS n,
    AVG(mag) AS avg_mag,
    MAX(mag) AS max_mag
FROM events
GROUP BY ym
ORDER BY ym;
```

### Top 20 sismos por magnitud

```sql
SELECT mag, place, lat, lon, depth_km,
       datetime(time_ms/1000, 'unixepoch') AS utc_time
FROM events
ORDER BY mag DESC
LIMIT 20;
```

### Sismos por país (geolocalización inversa)

No hay tabla de países — pero podemos filtrar por bbox conocida:

```sql
-- Ecuador
SELECT * FROM events
WHERE lat BETWEEN -7 AND 3 AND lon BETWEEN -82 AND -75
ORDER BY mag DESC LIMIT 20;

-- Perú
SELECT * FROM events
WHERE lat BETWEEN -20 AND 0 AND lon BETWEEN -82 AND -68
ORDER BY mag DESC LIMIT 20;

-- Chile
SELECT * FROM events
WHERE lat BETWEEN -60 AND -15 AND lon BETWEEN -76 AND -65
ORDER BY mag DESC LIMIT 20;

-- Colombia
SELECT * FROM events
WHERE lat BETWEEN -5 AND 13 AND lon BETWEEN -80 AND -65
ORDER BY mag DESC LIMIT 20;
```

### Sismos por profundidad

```sql
-- Someros (<70 km) — asociados a fallas corticales
SELECT COUNT(*) FROM events WHERE depth_km < 70;

-- Profundos (>300 km) — asociados a slab de Nazca
SELECT COUNT(*) FROM events WHERE depth_km > 300;

-- Distribución de profundidad
SELECT
    CASE
        WHEN depth_km < 70 THEN 'somero (0-70 km)'
        WHEN depth_km < 300 THEN 'intermedio (70-300 km)'
        ELSE 'profundo (>300 km)'
    END AS depth_cat,
    COUNT(*) AS n,
    AVG(mag) AS avg_mag
FROM events
GROUP BY depth_cat;
```

---

## Análisis temporales

### Actividad por hora del día (UTC)

¿Hay sesgo temporal en la detección? Generalmente no, pero curiosear:

```sql
SELECT
    strftime('%H', time_ms/1000, 'unixepoch') AS hour_utc,
    COUNT(*) AS n
FROM events
GROUP BY hour_utc
ORDER BY hour_utc;
```

### Comparar mayo 2025 (pico) vs resto

```sql
WITH pico AS (
    SELECT * FROM events
    WHERE time_ms BETWEEN strftime('%s','2025-05-01')*1000
                     AND strftime('%s','2025-06-01')*1000
)
SELECT
    COUNT(*) AS n_pico,
    AVG(mag) AS avg_mag_pico,
    MAX(mag) AS max_mag_pico
FROM pico;
```

### Réplicas (aftershocks) de un evento M6+

```sql
-- Réplicas del M7.4 Colombia (2025-10 algo)
WITH mainshock AS (
    SELECT * FROM events
    WHERE mag >= 7 AND place LIKE '%Colombia%'
    ORDER BY time_ms DESC LIMIT 1
),
replicas AS (
    SELECT e.*
    FROM events e, mainshock m
    WHERE e.time_ms > m.time_ms
      AND e.time_ms < m.time_ms + 30*86400000  -- 30 días después
      AND ABS(e.lat - m.lat) < 1.5
      AND ABS(e.lon - m.lon) < 1.5
)
SELECT COUNT(*) AS replicas_30d, AVG(mag) AS avg_mag_replica
FROM replicas;
```

### Tasa de sismicidad por región y año

```sql
SELECT
    CASE
        WHEN lat < -15 AND lon < -68 THEN 'Chile/Argentina'
        WHEN lat < 0 AND lon < -68 THEN 'Perú/Bolivia'
        WHEN lat < 13 AND lon < -68 THEN 'Colombia/Ecuador'
        ELSE 'Otro'
    END AS region,
    strftime('%Y', time_ms/1000, 'unixepoch') AS year,
    COUNT(*) AS n,
    AVG(mag) AS avg_mag
FROM events
GROUP BY region, year
ORDER BY region, year;
```

---

## Análisis espacial (sin PostGIS)

### Sismos cerca de un punto (radio X km)

Fórmula del cuadrado delimitador (aproximación rápida):

```sql
-- Eventos dentro de 200 km de Quito (-0.18, -78.47)
WITH quieto AS (SELECT -0.18 AS lat, -78.47 AS lon)
SELECT e.*,
       (6371 * 2 * ASIN(SQRT(
            POWER(SIN(RADIANS(e.lat - q.lat)/2), 2) +
            COS(RADIANS(q.lat)) * COS(RADIANS(e.lat)) *
            POWER(SIN(RADIANS(e.lon - q.lon)/2), 2)
       ))) AS dist_km
FROM events e, quieto q
WHERE e.lat BETWEEN q.lat - 2 AND q.lat + 2
  AND e.lon BETWEEN q.lon - 2 AND q.lon + 2
HAVING dist_km < 200
ORDER BY dist_km;
```

### Densidad por grilla 1° × 1°

```sql
SELECT
    CAST(lat AS INT) AS lat_grid,
    CAST(lon AS INT) AS lon_grid,
    COUNT(*) AS n,
    AVG(mag) AS avg_mag
FROM events
GROUP BY lat_grid, lon_grid
HAVING n > 5
ORDER BY n DESC
LIMIT 20;
```

Esto te da los "hotspots" — zonas con más actividad.

---

## Exportar resultados

### A CSV (para Excel/Python/pandas)

```bash
sqlite3 -header -csv /opt/sismos/data/sismos.db \
  "SELECT * FROM events WHERE mag >= 6 ORDER BY time_ms" \
  > sismos_m6.csv
```

### A JSON

```bash
sqlite3 /opt/sismos/data/sismos.db \
  "SELECT json_object('id',id,'t',time_ms,'m',mag,'lat',lat,'lon',lon,'d',depth_km)
   FROM events LIMIT 100"
```

### Plotear con Python

```python
import sqlite3, pandas as pd, matplotlib.pyplot as plt

conn = sqlite3.connect('/opt/sismos/data/sismos.db')
df = pd.read_sql("SELECT * FROM events", conn)

# Distribución por mes
df['month'] = pd.to_datetime(df['time_ms'], unit='ms').dt.to_period('M')
df.groupby('month').size().plot(kind='bar', figsize=(12,4))
plt.title('Sismos por mes'); plt.show()
```

---

## Estadísticas curiosas para reportar

### Magnitud media por año

```sql
SELECT
    strftime('%Y', time_ms/1000, 'unixepoch') AS year,
    AVG(mag) AS avg,
    MIN(mag) AS min,
    MAX(mag) AS max,
    COUNT(*) AS n
FROM events
GROUP BY year;
```

### ¿Hay clustering temporal? (b-value de Gutenberg-Richter)

Relación entre frecuencia y magnitud:
```
log10(N) = a - b * M
```
donde `b ≈ 1` es típico. Para calcularlo:

```sql
WITH bins AS (
    SELECT
        CAST(mag AS INT) AS m_int,
        COUNT(*) AS n
    FROM events
    WHERE mag >= 4.5
    GROUP BY m_int
)
SELECT m_int, n, LOG10(n) AS log_n FROM bins ORDER BY m_int;
```

Si la pendiente (regresión lineal de `log_n` vs `m_int`) está cerca de -1, el catálogo es completo.

### Productividad sísmica por grado cuadrado

Para comparar productividad entre zonas (interesante para investigación):

```sql
WITH zonas AS (
    SELECT
        CAST(lat+90 AS INT)*360 + CAST(lon+180 AS INT) AS cell_id,
        lat, lon, mag
    FROM events
)
SELECT cell_id, COUNT(*) AS n, AVG(mag) AS avg_mag
FROM zonas
GROUP BY cell_id
ORDER BY n DESC
LIMIT 30;
```

---

## Recursos para profundizar

- **Python `obspy`** — librería sismológica completa (taup, fase picking, etc.)
- **USGS ComCat API** — `https://earthquake.usgs.gov/fdsnws/` (documentación completa)
- **Catálogo PREP Ecuador** — Instituto Geofísico Escuela Politécnica Nacional
- **IRIS** — Incorporated Research Institutions for Seismology (datos globales de banda ancha)