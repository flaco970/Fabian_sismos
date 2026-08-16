#!/usr/bin/env python3
"""
export_html.py — Genera el HTML estático a partir de:
  - SQLite (data/sismos.db)
  - SST monthly PNGs (data/sst_pngs/)
  - Polígono Ecuador (data/ecuador.geojson)
  - Bordes de placa Bird 2003 (descarga si falta)

Salida: web/index.html (single-file con todo embebido)

Uso:
    python3 export_html.py
    python3 export_html.py --window 3   # ventana móvil en meses
"""
import argparse, sqlite3, json, urllib.request, ssl
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
DB   = ROOT/"data/sismos.db"
WEB  = ROOT/"web/index.html"

LEAFLET_DIR = ROOT/"build/leaflet_embebido"

def load_leaflet():
    return ((LEAFLET_DIR/"leaflet.css").read_text(),
            (LEAFLET_DIR/"leaflet.js").read_text())

def load_plates():
    p = ROOT/"data/plates.geojson"
    if not p.exists():
        print(f"  Descargando Bird 2003...")
        ctx = ssl.create_default_context()
        url = "https://raw.githubusercontent.com/fraxen/tectonicplates/master/GeoJSON/PB2002_boundaries.json"
        req = urllib.request.Request(url, headers={"User-Agent":"Fabian-sismos/1.0"})
        with urllib.request.urlopen(req, context=ctx, timeout=60) as r:
            raw = json.loads(r.read())
        # Simplificar (cada 5 puntos)
        feats = []
        for f in raw["features"]:
            g = f["geometry"]; pa = f["properties"]["PlateA"]; pb = f["properties"]["PlateB"]
            name = f"{pa}/{pb}"
            if g["type"] == "MultiLineString":
                lines = []
                for line in g["coordinates"]:
                    decim = line[::5]
                    if decim[-1] != line[-1]: decim.append(line[-1])
                    if len(decim) >= 2: lines.append(decim)
                if lines:
                    feats.append({"type":"Feature","properties":{"name":name},"geometry":{"type":"MultiLineString","coordinates":lines}})
            else:
                decim = g["coordinates"][::5]
                if decim[-1] != g["coordinates"][-1]: decim.append(g["coordinates"][-1])
                if len(decim) >= 2:
                    feats.append({"type":"Feature","properties":{"name":name},"geometry":{"type":"LineString","coordinates":decim}})
        out = {"type":"FeatureCollection","features":feats}
        with open(p, "w") as f: json.dump(out, f)
    return json.loads(p.read_text())

def load_sst_manifest():
    p = ROOT/"data/sst_manifest.json"
    if not p.exists():
        return {}
    return json.loads(p.read_text())

def load_sst_pngs():
    """SST deshabilitado — retorna dict vacío."""
    return {}


def load_events(db_path):
    conn = sqlite3.connect(str(db_path))
    cur = conn.execute("SELECT id,time_ms,mag,place,lat,lon,depth_km,url FROM events ORDER BY time_ms")
    rows = cur.fetchall()
    conn.close()
    events = []
    for r in rows:
        events.append({
            "id": r[0], "t": r[1], "m": round(r[2],1),
            "p": (r[3] or "")[:60],
            "lat": round(r[4],3), "lon": round(r[5],3),
            "d": round(r[6],1), "u": r[7] or "",
        })
    return events

def load_ecuador():
    return json.loads((ROOT/"data/ecuador.geojson").read_text())

def month_stops(events):
    seen = set(); out = []
    for e in events:
        ym = datetime.utcfromtimestamp(e["t"]/1000).strftime("%Y-%m")
        if ym not in seen: seen.add(ym); out.append(ym)
    return sorted(out)

def build_html(window=3):
    print(f"=== EXPORT HTML ===")
    print(f"  Window: {window} meses")
    
    events = load_events(DB)
    print(f"  Eventos cargados: {len(events)}")
    
    months = month_stops(events)
    print(f"  Meses: {len(months)}")
    
    by_month = {ym:[] for ym in months}
    for i, e in enumerate(events):
        ym = datetime.utcfromtimestamp(e["t"]/1000).strftime("%Y-%m")
        by_month[ym].append(i)
    
    plates = load_plates()
    print(f"  Placas: {len(plates['features'])}")
    
    ecuador = load_ecuador()
    sst_manifest = load_sst_manifest()
    sst_pngs = load_sst_pngs()
    print(f"  SST PNGs embebidos: {len(sst_pngs)}")
    
    leaflet_css, leaflet_js = load_leaflet()
    
    data_blob = json.dumps({
        "months": months, "events": events, "by_month": by_month,
        "sst_bounds": [[-60.0, 0.0], [60.0, 360.0]],  # GLOBAL: todo el mundo en 0..360
        "sst_pngs": sst_pngs,
    })
    
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>Sismicidad Sudamérica — SST mensual</title>
<style>
{leaflet_css}
html,body{{margin:0;padding:0;height:100%;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:#0b0d12;color:#e8eaed;overflow:hidden}}
#map{{position:absolute;top:0;left:0;right:0;bottom:140px;width:100%}}
#timeline{{position:absolute;bottom:0;left:0;right:0;height:140px;background:rgba(15,18,28,.96);border-top:1px solid #2a2f3a;z-index:1000;padding:10px 16px 14px;box-sizing:border-box}}
.info{{position:absolute;top:10px;right:10px;z-index:1000;background:rgba(15,18,28,.92);color:#e8eaed;
      padding:12px 14px;border-radius:8px;max-width:240px;border:1px solid #2a2f3a;
      backdrop-filter:blur(8px);font-size:12px;line-height:1.5}}
.info h3{{margin:0 0 6px;font-size:13px;color:#4cc9f0;display:flex;justify-content:space-between;align-items:center}}
#closeBtn{{background:none;border:1px solid #2a2f3a;color:#9aa0a6;width:22px;height:22px;border-radius:50%;cursor:pointer;font-size:11px;line-height:1;padding:0}}
#closeBtn:hover{{background:#2a2f3a;color:#fff}}
#openBtn{{display:none;position:absolute;top:10px;right:10px;z-index:1000;background:rgba(15,18,28,.92);
         border:1px solid #2a2f3a;color:#4cc9f0;padding:8px 12px;border-radius:8px;cursor:pointer;font-size:11px}}
.info.collapsed{{display:none}}
.info .leg-item{{display:flex;align-items:center;gap:7px;margin:2px 0}}
.leg-dot{{width:11px;height:11px;border-radius:50%;border:1px solid #000;flex-shrink:0}}
.leg-line{{width:18px;height:2px;background:#ff6b35;flex-shrink:0}}
.popup-title{{font-weight:600;color:#4cc9f0;margin-bottom:4px;font-size:13px}}
.popup-meta{{color:#9aa0a6;font-size:11px;margin-top:4px}}
.leaflet-popup-content{{margin:10px 14px;font-size:12px;line-height:1.4}}
.leaflet-container{{background:#0b0d12}}
.plate-tooltip{{background:#1a1d27;color:#e8eaed;border:1px solid #2a2f3a;font-size:11px}}
.plate-tooltip:before{{border-top-color:#2a2f3a}}
.tl-row{{display:flex;align-items:center;gap:10px;margin-top:6px}}
#playBtn{{background:#4cc9f0;color:#0b0d12;border:none;width:36px;height:36px;border-radius:50%;font-size:14px;cursor:pointer;flex-shrink:0;font-weight:700}}
#playBtn:hover{{background:#7dd5f5}}
#monthLabel{{font-size:13px;color:#e8eaed;min-width:90px;font-weight:600}}
#monthCount{{font-size:11px;color:#9aa0a6;min-width:110px;text-align:right}}
#slider{{flex:1;-webkit-appearance:none;appearance:none;height:8px;background:#2a2f3a;border-radius:4px;outline:none}}
#slider::-webkit-slider-thumb{{-webkit-appearance:none;width:20px;height:20px;background:#4cc9f0;border-radius:50%;cursor:pointer;border:2px solid #0b0d12}}
#slider::-moz-range-thumb{{width:20px;height:20px;background:#4cc9f0;border-radius:50%;cursor:pointer;border:2px solid #0b0d12}}
#hist{{display:flex;align-items:flex-end;height:38px;gap:1px;margin-top:6px;overflow:hidden}}
.hist-bar{{flex:1;background:#4cc9f0;opacity:0.3;min-width:2px;border-radius:1px 1px 0 0}}
.hist-bar.in-window{{opacity:0.85;background:#7dd5f5}}
.hist-bar.active{{opacity:1;background:#ff9100}}
#windowNote{{font-size:10px;color:#9aa0a6;margin-top:4px;text-align:center}}
.toggles{{display:flex;gap:8px;margin-top:6px;font-size:10px;color:#9aa0a6}}
.toggles label{{display:flex;align-items:center;gap:4px;cursor:pointer}}
.sst-legend{{margin-top:6px;font-size:10px;color:#9aa0a6;border-top:1px solid #2a2f3a;padding-top:6px}}
.sst-bar{{height:8px;border-radius:2px;background:linear-gradient(to right, rgb(10,10,100) 0%, rgb(10,80,200) 20%, rgb(10,180,220) 35%, rgb(50,230,100) 50%, rgb(240,230,50) 65%, rgb(255,150,30) 80%, rgb(255,30,30) 100%);margin:3px 0 1px}}
.sst-labels{{display:flex;justify-content:space-between;font-size:9px;color:#9aa0a6}}
</style>
</head>
<body>
<div id="map"></div>

<div class="info" id="infoBox">
  <h3>🌎 Sudamérica · {len(events)} sismos <button id="closeBtn" aria-label="Cerrar">×</button></h3>
  <div style="color:#9aa0a6;margin-bottom:8px;font-size:10px">
    USGS M4.5+ · {len(months)} meses · Placas Bird (2003)[2]<br>
    SST NOAA OISST v2 [3]</div>
  <div class="leg-item"><span class="leg-dot" style="background:#ff1744"></span>M ≥ 7.0</div>
  <div class="leg-item"><span class="leg-dot" style="background:#ff9100"></span>M 6.0–6.9</div>
  <div class="leg-item"><span class="leg-dot" style="background:#ffc400"></span>M 5.0–5.9</div>
  <div class="leg-item"><span class="leg-dot" style="background:#4cc9f0"></span>M 4.5–4.9</div>
  <div class="leg-item"><span class="leg-line"></span>Límite placa</div>
  <div class="leg-item"><span class="leg-dot" style="background:#00ff88"></span>Ecuador</div>
  <div class="toggles">
    <label><input type="checkbox" id="togEC" checked> Ecuador</label>
  </div>
  <div style="margin-top:6px;color:#666;font-size:9px;font-style:italic">
    SST experimental — deshabilitado
  </div>
</div>

<button id="openBtn">📊 Leyenda</button>

<div id="timeline">
  <div class="tl-row">
    <button id="playBtn" aria-label="Play">▶</button>
    <span id="monthLabel">—</span>
    <input type="range" id="slider" min="0" max="{len(months)-1}" value="{len(months)-1}" step="1">
    <span id="monthCount">0 sismos</span>
  </div>
  <div id="hist"></div>
  <div id="windowNote">Ventana móvil: {window} meses · arrastrá el slider para navegar</div>
</div>

<script>
{leaflet_js}
</script>
<script>
const DATA = {data_blob};
const WINDOW = {window};
const PLATES = {json.dumps(plates)};
const ECUADOR = {json.dumps(ecuador)};

const MONTHS = DATA.months;
const EVENTS = DATA.events;
const BY_MONTH = DATA.by_month;
const SST_PNGS = DATA.sst_pngs;
const SST_BOUNDS = DATA.sst_bounds;

const SA_BOUNDS = L.latLngBounds([[-60, -90], [30, -30]]);
const map = L.map('map',{{worldCopyJump:true,minZoom:2,maxZoom:8,zoomControl:true}})
  .fitBounds(SA_BOUNDS, {{padding:[20,20]}});

L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png',{{
  attribution:'© OSM · © CARTO', subdomains:'abcd', maxZoom:19
}}).addTo(map);

// Placas
L.geoJSON(PLATES, {{
  style:{{color:'#ff6b35',weight:1.2,opacity:0.7}},
  onEachFeature:(f,l)=>l.bindTooltip(f.properties.name,{{sticky:true,className:'plate-tooltip'}})
}}).addTo(map);

// Ecuador destacado
const ecuadorLayer = L.geoJSON(ECUADOR, {{
  style:{{color:'#00ff88',weight:2.5,fillColor:'#00ff88',fillOpacity:0.15,opacity:1}},
  onEachFeature:(f,l)=>l.bindTooltip(f.properties.name,{{sticky:true,className:'plate-tooltip'}})
}}).addTo(map);

// SST desactivado por default — código preservado para futuro
let sstLayer = null;
function setSSTLayer(ym) {{
  if (sstLayer) {{ map.removeLayer(sstLayer); sstLayer = null; }}
  // SST desactivado por default. Activar con: window.togSSTEnabled = true
  if (!window.togSSTEnabled) return;
  const url = SST_PNGS[ym];
  if (url) {{
    sstLayer = L.imageOverlay(url, SST_BOUNDS, {{opacity:0.65,interactive:false}});
    sstLayer.addTo(map);
  }}
}}

function colorFor(m){{
  if(m>=7) return '#ff1744';
  if(m>=6) return '#ff9100';
  if(m>=5) return '#ffc400';
  return '#4cc9f0';
}}
function radiusFor(m){{
  if(m>=7) return 13;
  if(m>=6) return 10;
  if(m>=5) return 7;
  return 4;
}}

const markers = MONTHS.map(() => []);
for (const ym of MONTHS) {{
  for (const idx of (BY_MONTH[ym] || [])) {{
    const e = EVENTS[idx];
    const m = L.circleMarker([e.lat, e.lon], {{
      radius: radiusFor(e.m),
      fillColor: colorFor(e.m),
      color:'#000', weight:1, fillOpacity:0.85
    }});
    const t = new Date(e.t);
    m.bindPopup(
      `<div class="popup-title">M ${{e.m.toFixed(1)}} — ${{e.p||'N/A'}}</div>
       <div>📅 ${{t.toUTCString()}}</div>
       <div>📍 ${{e.lat.toFixed(2)}}°, ${{e.lon.toFixed(2)}}°</div>
       <div>⬇ Prof: ${{e.d.toFixed(1)}} km</div>
       <div class="popup-meta"><a href="${{e.u}}" target="_blank" style="color:#4cc9f0">USGS →</a></div>`
    );
    m.addTo(map);
    markers[MONTHS.indexOf(ym)].push(m);
  }}
}}

// Histograma
const histDiv = document.getElementById('hist');
const counts = MONTHS.map(ym => (BY_MONTH[ym]||[]).length);
const maxCount = Math.max(...counts, 1);
const bars = {{}};
MONTHS.forEach((ym,i) => {{
  const b = document.createElement('div');
  b.className = 'hist-bar';
  b.style.height = (counts[i]/maxCount*100) + '%';
  b.title = `${{ym}}: ${{counts[i]}} sismos`;
  histDiv.appendChild(b);
  bars[ym] = b;
}});

// Controles
const slider = document.getElementById('slider');
const monthLabel = document.getElementById('monthLabel');
const monthCount = document.getElementById('monthCount');
const playBtn = document.getElementById('playBtn');
const togSST = document.getElementById('togSST');
const togEC  = document.getElementById('togEC');

let currentIdx = MONTHS.length - 1;
let playing = false;
let playTimer = null;

function updateSlider(idx) {{
  currentIdx = idx;
  const ym = MONTHS[idx];
  monthLabel.textContent = ym;

  const start = Math.max(0, idx - (WINDOW - 1));
  const windowMonths = new Set(MONTHS.slice(start, idx + 1));
  let windowCount = 0;
  for (const m of windowMonths) windowCount += (BY_MONTH[m]||[]).length;
  monthCount.textContent = `${{windowCount}} en ventana`;

  for (let i = 0; i < MONTHS.length; i++) {{
    const inWin = windowMonths.has(MONTHS[i]);
    for (const m of markers[i]) {{
      if (inWin) {{ if (!map.hasLayer(m)) m.addTo(map); }}
      else       {{ if (map.hasLayer(m))  map.removeLayer(m); }}
    }}
  }}
  for (const k in bars) {{
    const inWin = windowMonths.has(k);
    const isActive = (k === ym);
    bars[k].classList.toggle('in-window', inWin && !isActive);
    bars[k].classList.toggle('active', isActive);
  }}
  
  // SST: solo el mes activo
  if (togSST.checked) setSSTLayer(ym);
}}

slider.addEventListener('input', e => updateSlider(parseInt(e.target.value)));

playBtn.addEventListener('click', () => {{
  if (playing) {{
    clearInterval(playTimer); playing = false;
    playBtn.textContent = '▶';
  }} else {{
    if (currentIdx >= MONTHS.length - 1) slider.value = 0;
    playing = true;
    playBtn.textContent = '⏸';
    playTimer = setInterval(() => {{
      const idx = parseInt(slider.value);
      if (idx >= MONTHS.length - 1) {{
        clearInterval(playTimer); playing = false;
        playBtn.textContent = '▶';
        return;
      }}
      slider.value = idx + 1;
      updateSlider(idx + 1);
    }}, 700);
  }}
}});

// SST deshabilitado por default (experimental). Para activar:
//   window.togSSTEnabled = true; updateSlider(currentIdx);
// (descomentar el bloque siguiente si querés el checkbox de SST de vuelta)
/*
togSST.addEventListener('change', () => {{
  window.togSSTEnabled = togSST.checked;
  if (togSST.checked) setSSTLayer(MONTHS[currentIdx]);
  else if (sstLayer) {{ map.removeLayer(sstLayer); sstLayer = null; }}
}});
*/
togEC.addEventListener('change', () => {{
  if (togEC.checked) {{
    map.addLayer(ecuadorLayer);
    // Feedback: pulse breve
    ecuadorLayer.eachLayer(l => {{
      if (l.setStyle) {{
        l.setStyle({{fillOpacity: 0.4, weight: 4}});
        setTimeout(() => l.setStyle({{fillOpacity: 0.15, weight: 2.5}}), 400);
      }}
    }});
    // Centrar Ecuador en el mapa
    map.fitBounds(ecuadorLayer.getBounds(), {{padding:[80,80], maxZoom:6, animate:true, duration:1.5}});
  }} else {{
    map.removeLayer(ecuadorLayer);
  }}
}});

// Leyenda colapsable
const infoBox = document.getElementById('infoBox');
document.getElementById('closeBtn').addEventListener('click', () => {{
  infoBox.classList.add('collapsed');
  document.getElementById('openBtn').style.display = 'block';
}});
document.getElementById('openBtn').addEventListener('click', () => {{
  infoBox.classList.remove('collapsed');
  document.getElementById('openBtn').style.display = 'none';
}});

updateSlider(MONTHS.length - 1);
</script>
</body>
</html>
"""
    WEB.parent.mkdir(exist_ok=True)
    WEB.write_text(html)
    sz = WEB.stat().st_size
    print(f"\n✓ {WEB} · {sz/1024:.1f} KB")
    return sz

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--window", type=int, default=3)
    args = p.parse_args()
    build_html(args.window)