# 🔬 Investigación — fuentes, papers, ideas

Esta guía apunta a fuentes científicas y referencias para profundizar en sismología y oceanografía, especialmente aplicado a la región Sudamérica / Nazca.

## Fuentes de datos (verificadas y activas)

### Sismicidad

| Fuente | Contenido | URL | Licencia |
|---|---|---|---|
| USGS ComCat | Global, tiempo real + histórico | https://earthquake.usgs.gov/data/comcat/ | Público |
| USGS FDSN WS | API programática | https://earthquake.usgs.gov/fdsnws/event/1/ | Público |
| IRIS Wilber 3 | Global, datos de forma de onda | https://ds.iris.edu/wilber3/ | Público |
| ISC GEM | Catálogo global instrumental | https://www.isc.ac.uk/gem/ | Académico |
| PREP / IGEPN | Ecuador regional | https://www.igepn.edu.ec/ | Público |
| CSN Chile | Chile regional | https://www.csn.uchile.cl/ | Público |

### Temperatura oceánica (SST)

| Fuente | Resolución | Frecuencia | URL |
|---|---|---|---|
| NOAA OISST v2.1 | 0.25° | Diario/Mensual | https://psl.noaa.gov/data/gridded/data.noaa.oisst.v2.highres.html |
| NOAA Coral Reef Watch | 5 km | Diario | https://coralreefwatch.noaa.gov/product/5km/ |
| ERA5 (Copernicus) | 0.25° | Horario | https://cds.climate.copernicus.eu/ |
| MUR SST | 0.01° | Diario | https://mur.jpl.nasa.gov/ |

### Placas tectónicas

| Recurso | Contenido | URL |
|---|---|---|
| Bird (2003) | 52 placas, polilíneas | https://github.com/fraxen/tectonicplates |
| NUVEL-1A | Vectores de velocidad relativa | https://www.geol.ucsb.edu/faculty/fueyo/research.html |
| MORVEL56 | Modelo de velocidades globales | https://www.geology.wisc.edu/~daveb/MORVEL/ |

### Batimetría y topografía

| Recurso | Uso | URL |
|---|---|---|
| GEBCO | Batimetría global | https://www.gebco.net/ |
| SRTM 30m | Topografía continental | https://earthexplorer.usgs.gov/ |
| ETOPO1 | Combinado tierra+océano | https://www.ngdc.noaa.gov/mgg/global/ |

---

## Papers seminales (lectura recomendada)

### Sismicidad de subducción

- **Lay & Wallace (1995)** — *Modern Global Seismology* — textbook definitivo
- **Ruff & Kanamori (1980)** — *Seismicity and the subduction process* — clasifica tipos de subducción por tamaño máximo de terremoto
- **Stein & Wysession (2003)** — *An Introduction to Seismology, Earthquakes, and Earth Structure* — excelente intro

### Ecuador y Nazca específicamente

- **Gutscher et al. (1999)** — *Tectonic segmentation of the North Andean margin* — propone segmentation del slab
- **Yepes et al. (2016)** — *A new view of the subduction geometry of Ecuador* — modelo 3D del slab
- **Sallares & Charvis (2003)** — *Structure of the Carnegie Ridge collision zone* — interacción Carnegie Ridge con Sudamerica
- **Collot et al. (2004)** — *The Ecuador convergent margin* — resumen integral

### Slab de Nazca / South American subduction

- **Cisternas et al. (2005)** — *Predecessors of the giant 1960 Chile earthquake* — historia sísmica
- **Moreno et al. (2008)** — *Toward understanding tectonic control on the M8.8 Maule earthquake* — segmentación y locking
- **Hicks et al. (2014)** — *The 2014 M8.1 Iquique earthquake* — secuencia precursors

### Temperatura oceánica y sismicidad

- **Pollitz et al. (1998)** — *Stress transfer by seismic waves* — cómo un terremoto afecta zonas remotas
- **McGuire et al. (2001)** — *The relationship between ocean temperature and seismicity* — correlación SST con sismicidad
- **Gao (2015)** — *Climate-driven sea level variations* — cómo el nivel del mar afecta la carga cortical

### Predicción sísmica (lectura escéptica recomendada)

- **Geller (1997)** — *Earthquake prediction: a critical review* — por qué es muy difícil
- **Hough (2010)** — *Predicting the Unpredictable* — libro sobre pseudo-predicciones

---

## Preguntas de investigación abiertas

Estas son preguntas donde el análisis de este dataset puede contribuir:

### 1. ¿Hay correlación SST-sismicidad en la costa sudamericana?

**Hipótesis**: cambios locales en SST cambian la carga cortical (masa de agua), lo que podría gatillar sismicidad en zonas de acoplamiento fuerte.

**Cómo testearlo**:
1. Promediar SST mensual en celdas costeras (lat -5..-40, lon -82..-70)
2. Calcular anomalía vs climatología
3. Correlacionar con número de sismos M5+ por mes
4. Verificar significancia estadística (test de Student)

**Output esperado**: paper tipo "Correlación SST-sismicidad en el margen sudamericano".

### 2. ¿Cuál es el patrón espacio-temporal del slab de Nazca?

**Hipótesis**: la geometría 3D del slab influye en la distribución de profundidades focales.

**Cómo testearlo**:
1. Plotear todos los sismos con depth_km > 100 km en cross-section
2. Visualizar con código de colores por latitud
3. Comparar con modelos publicados (Slab2, Slab1.0)

**Output**: visualización tipo mapa de calor 2D latitud vs profundidad.

### 3. ¿Cuál es el patrón de réplicas (aftershocks) por evento M7+?

**Hipótesis**: secuencias de réplicas siguen leyes de potencia (Omori law: n(t) ∝ t^(-1)).

**Cómo testearlo**:
1. Para cada M7+ en el catálogo, contar réplicas en 1, 7, 30 días
2. Ajustar ley de Omori
3. Comparar p-values entre regiones (Nazca vs Cocos)

### 4. ¿Hay migración espacial de sismicidad?

**Hipótesis**: clusters sísmicos pueden migrar a lo largo de la falla en semanas/meses.

**Cómo testearlo**:
1. Para cada evento M5+, buscar réplicas en radio 100 km, 30 días
2. Calcular el "centro de masa" del cluster
3. Ver si migra sistemáticamente

### 5. ¿Influye El Niño/La Niña en sismicidad costera?

**Hipótesis**: cambios en SST del Pacífico este (ENSO) modifican presión atmosférica y carga oceánica.

**Cómo testearlo**:
1. Bajar serie temporal MEI (Multivariate ENSO Index)
2. Correlacionar con sismicidad costera mensual
3. Comparar eventos El Niño fuertes vs La Niña

**Dato curioso**: estudio de 2017 (Wu et al.) encontró correlación ENSO-sismicidad en Indonesia.

---

## Datasets complementarios que podrían agregarse

### Gravedad (GRACE)

Cambios de masa cortical afectan el estrés. Disponible:
- NASA GRACE / GRACE-FO: https://grace.jpl.nasa.gov/

### Nivel del mar

- NASA Sea Level Change: https://sealevel.nasa.gov/

### Presión atmosférica

- ERA5 (Copernicus): incluye presión a nivel del mar

### Marea

- FES2014 (Finite Element Solution tides): https://www.aviso.altimetry.fr/

### Precipitación

- GPM (Global Precipitation Measurement): https://gpm.nasa.gov/

### Anomalías gravitacionales

- EGM2008: https://earth-info.nga.mil/

---

## Herramientas computacionales recomendadas

| Herramienta | Uso | URL |
|---|---|---|
| ObsPy | Sismología en Python | https://obspy.org/ |
| GMT | Mapeo geológico | https://www.generic-mapping-tools.org/ |
| QGIS | GIS desktop | https://qgis.org/ |
| PyGMT | Interfaz Python para GMT | https://www.pygmt.org/ |
| TauP | Tiempos de viaje de fases sísmicas | https://github.com/crotwell/TauP |
| Madagascar | Procesamiento sísmico | https://reproducibility.org/ |

---

## Comunidades y grupos

- **IRIS Education & Outreach** — https://www.iris.edu/hq/inclass
- **Seismological Society of America (SSA)** — https://www.seismosoc.org/
- **AGU Geodesy section** — https://www.agu.org/
- **American Geophysical Union (AGU)** — https://www.agu.org/
- **Latin American and Caribbean Seismological Commission** — workshop series

---

## Ideas de proyectos derivados

1. **App de sismicidad histórica de Ecuador** (focus IGEPN): usar el catálogo USGS + integrar con datos del IGEPN cuando estén disponibles
2. **Visualización 3D del slab de Nazca**: plotear sismos profundos en 3D con Three.js
3. **Comparación Sudamérica vs Centroamérica** (Cocos plate subduction): interesante por la diferencia de acoplamiento
4. **Análisis de sismicidad inducida por embalses** en zonas andinas
5. **Estudio de sismicidad en Galápagos** (punto caliente + dorsal) — zona volcánica activa
6. **Análisis de tsunami risk** usando el catálogo de eventos M7+ cerca de la fosa

---

## Recursos en español

- **Instituto Geofísico EPN (Ecuador)** — http://www.igepn.edu.ec/
- **CSN Universidad de Chile** — https://www.csn.uchile.cl/
- **Servicio Geológico Colombiano** — https://www.sgc.gov.co/
- **Instituto Geológico Minero Metalúrgico de Perú (INGEMMET)** — https://www.ingemmet.gob.pe/
- **Red Nacional de Vigilancia Volcánica (Chile)** — https://www.sernageomin.cl/

---

## Cómo citar este proyecto

Si usás los datos generados por este proyecto en una publicación:

```
Sismicidad Sudamérica [dataset]. Generated 2026-08-16.
USGS Earthquake Catalog (https://earthquake.usgs.gov/).
NOAA OISST v2.1 (https://psl.noaa.gov/).
Bird (2003) plate boundaries (https://github.com/fraxen/tectonicplates).
```