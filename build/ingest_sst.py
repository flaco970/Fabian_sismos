#!/usr/bin/env python3
"""
ingest_sst.py — Baja SST mensual NOAA OISST v2.1 para Sudamérica extendida
y genera PNGs georreferenciados en data/sst_pngs/.

Fuente: https://psl.noaa.gov/thredds/dodsC/Datasets/noaa.oisst.v2.highres/sst.mon.mean.nc
Resolución: 0.25° nativo, muestreamos cada 1° para SVG liviano
Cobertura: ago 2023 → hoy

Uso:
    python3 ingest_sst.py             # últimos 37 meses (3 años)
    python3 ingest_sst.py --years 5   # 5 años
"""
import argparse, urllib.request, ssl, json, re, time as tt
from pathlib import Path
from datetime import datetime, timedelta

ROOT = Path(__file__).parent.parent
OUT_RAW = ROOT/"data/sst_monthly.json"
OUT_PNG_DIR = ROOT/"data/sst_pngs"
OUT_MANIFEST = ROOT/"data/sst_manifest.json"

# Bounds Sudamérica extendida
LAT_MIN, LAT_MAX = -60.0, 30.0
LON_MIN_DEG, LON_MAX_DEG = -90.0, -30.0

# Índices grid 0.25°: lat 0..720, lon 0..1440
def idx_for(v, vmin, step): return int((v - vmin) / step)

LAT_IDX_MIN = idx_for(LAT_MIN, -90.0, 0.25)
LAT_IDX_MAX = idx_for(LAT_MAX, -90.0, 0.25)
LON_IDX_MIN = idx_for(LON_MIN_DEG + 360, 0.0, 0.25)
LON_IDX_MAX = idx_for(LON_MAX_DEG + 360, 0.0, 0.25)

FLOAT_RE = re.compile(r"^-?\d+\.\d+(?:[eE][-+]?\d+)?$|^-?\d+[eE][-+]?\d+$")

def parse_dap(text):
    out = {}
    for name in ("lat", "lon"):
        m = re.search(rf"^{name}\s*\[\d+\]\s*\n([\s\S]+?)(?=^\w+\[\d+\]|^\w+\.\w+\[)",
                      text, re.MULTILINE)
        if m:
            out[name] = [float(x) for x in re.split(r'[,\s]+', m.group(1).strip()) if x]
    m = re.search(r"^sst\.sst\[\d+\]\[\d+\]\[\d+\]\s*\n([\s\S]+?)(?=^sst\.time\[|^Grid\s|^})",
                  text, re.MULTILINE)
    if m:
        parts = [p.strip() for p in m.group(1).split(",")]
        out["sst"] = [float(p) for p in parts if FLOAT_RE.match(p)]
    return out

def temp_to_color(t, t_min=-2, t_max=32):
    if t < -8: return (0, 0, 0, 0)
    t = max(t_min, min(t_max, t))
    norm = (t - t_min) / (t_max - t_min)
    stops = [
        (0.00, (10, 10, 100)),
        (0.20, (10, 80, 200)),
        (0.35, (10, 180, 220)),
        (0.50, (50, 230, 100)),
        (0.65, (240, 230, 50)),
        (0.80, (255, 150, 30)),
        (1.00, (255, 30, 30)),
    ]
    for i in range(len(stops)-1):
        if norm <= stops[i+1][0]:
            t0 = (norm - stops[i][0]) / (stops[i+1][0] - stops[i][0])
            r = int(stops[i][1][0] + (stops[i+1][1][0] - stops[i][1][0]) * t0)
            g = int(stops[i][1][1] + (stops[i+1][1][1] - stops[i][1][1]) * t0)
            b = int(stops[i][1][2] + (stops[i+1][1][2] - stops[i][1][2]) * t0)
            return (r, g, b, 180)
    return stops[-1][1] + (180,)

def main():
    from PIL import Image
    
    p = argparse.ArgumentParser()
    p.add_argument("--years", type=int, default=3)
    p.add_argument("--lat-step", type=int, default=4, help="Sampling step para lat (1 = full res 0.25°, 4 = cada 1°)")
    p.add_argument("--lon-step", type=int, default=4)
    args = p.parse_args()
    
    # OISST: t=0 = Dec 1981
    # Total meses para N años hacia atrás
    end_idx = 538  # ago 2025 (último disponible al 2026-08-16 → idx puede ser 539)
    start_idx = end_idx - args.years * 12 + 1
    
    ctx = ssl.create_default_context()
    HEADERS = {"User-Agent": "Fabian-sismos/1.0"}
    
    results = {}
    print(f"=== SST Ingest ===")
    print(f"  Rango: idx {start_idx} → {end_idx}")
    print(f"  Sampling: lat x{args.lat_step}, lon x{args.lon_step}")
    
    for i, tidx in enumerate(range(start_idx, end_idx + 1)):
        # Calcular ym: tidx 0 = Dec 1981
        total_months = tidx + 1
        y = 1981 + (total_months - 1) // 12 + 1
        m = (total_months - 1) % 12 + 1
        ym = f"{y:04d}-{m:02d}"
        
        url = ("https://psl.noaa.gov/thredds/dodsC/Datasets/noaa.oisst.v2.highres/sst.mon.mean.nc.ascii?"
               f"lat%5B{LAT_IDX_MIN}:{args.lat_step}:{LAT_IDX_MAX}%5D,"
               f"lon%5B{LON_IDX_MIN}:{args.lon_step}:{LON_IDX_MAX}%5D,"
               f"sst%5B{tidx}:1:{tidx}%5D%5B{LAT_IDX_MIN}:{args.lat_step}:{LAT_IDX_MAX}%5D"
               f"%5B{LON_IDX_MIN}:{args.lon_step}:{LON_IDX_MAX}%5D")
        
        for retry in range(3):
            try:
                req = urllib.request.Request(url, headers=HEADERS)
                with urllib.request.urlopen(req, context=ctx, timeout=60) as r:
                    text = r.read().decode()
                parsed = parse_dap(text)
                results[ym] = {"t_idx": tidx, **parsed}
                if (i+1) % 5 == 0 or i == 0:
                    print(f"  [{i+1}/{end_idx-start_idx+1}] {ym}: {len(parsed.get('sst') or [])} valores")
                break
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    print(f"    Rate limit {ym}, esperando...")
                    tt.sleep(10 + retry*5)
                else:
                    print(f"  ✗ {ym} HTTP {e.code}")
                    break
            except Exception as e:
                print(f"  ✗ {ym}: {e}")
                break
        tt.sleep(0.4)
    
    print(f"\n✓ {len(results)} meses descargados")
    
    # Guardar raw
    OUT_RAW.parent.mkdir(exist_ok=True)
    with open(OUT_RAW, "w") as f:
        json.dump(results, f)
    print(f"  Raw: {OUT_RAW}")
    
    # Generar PNGs
    print(f"\n=== Generando PNGs ===")
    OUT_PNG_DIR.mkdir(exist_ok=True)
    manifest = {}
    
    # Bounds para Leaflet (esquinas exactas del subset)
    bounds = [[LAT_MIN, LON_MIN_DEG], [LAT_MAX, LON_MAX_DEG]]
    
    for ym in sorted(results.keys()):
        d = results[ym]
        lat, lon, sst = d.get("lat"), d.get("lon"), d.get("sst")
        if not (lat and lon and sst): continue
        nl, no = len(lat), len(lon)
        img = Image.new("RGBA", (no, nl), (0, 0, 0, 0))
        pixels = img.load()
        idx = 0
        for i in range(nl):
            for j in range(no):
                if idx < len(sst):
                    pixels[j, i] = temp_to_color(sst[idx])
                    idx += 1
        out = OUT_PNG_DIR / f"sst_{ym}.png"
        img.save(out, optimize=True)
        manifest[ym] = {"file": out.name, "bounds": bounds,
                        "size_kb": round(out.stat().st_size / 1024, 1)}
    
    with open(OUT_MANIFEST, "w") as f:
        json.dump(manifest, f, indent=2)
    
    total_mb = sum(m["size_kb"] for m in manifest.values()) / 1024
    # Aplicar máscara tierra/océano
    try:
        from shapely.geometry import shape
        from shapely.prepared import prep
        land_path = ROOT/"data/land_mask.geojson"
        if land_path.exists():
            print(f"\n=== Aplicando máscara tierra/océano ===")
            with open(land_path) as f:
                land_data = json.load(f)
            land_geoms = []
            for feat in land_data["features"]:
                g = shape(feat["geometry"])
                if g.geom_type == "MultiPolygon":
                    for p in g.geoms: land_geoms.append(prep(p))
                else:
                    land_geoms.append(prep(g))
            def is_land(lat, lon):
                pt = type(land_geoms[0])([lon, lat]) if False else None  # noqa
                from shapely.geometry import Point
                return any(g.contains(Point(lon, lat)) for g in land_geoms)
            masked_dir = ROOT/"data/sst_pngs_masked"
            masked_dir.mkdir(exist_ok=True)
            import numpy as np
            LAT_MIN, LAT_MAX = -60.0, 30.125
            LON_MIN, LON_MAX = -89.875, -29.875
            for ym in sorted(results.keys()):
                d = results[ym]; lat, lon, sst = d.get("lat"), d.get("lon"), d.get("sst")
                if not (lat and lon and sst): continue
                nl, no = len(lat), len(lon)
                img = Image.new("RGBA", (no, nl), (0,0,0,0))
                pixels = img.load(); idx = 0
                lats = np.linspace(LAT_MIN, LAT_MAX, nl)
                lons = np.linspace(LON_MIN, LON_MAX, no)
                # Pre-compute mask
                mask = np.zeros((nl, no), dtype=bool)
                for i in range(nl):
                    for j in range(no):
                        mask[i,j] = is_land(lats[i], lons[j])
                arr = np.array(img)
                idx = 0
                for i in range(nl):
                    for j in range(no):
                        if idx < len(sst):
                            from PIL import Image as I
                            t = sst[idx]
                            # Aplicar color
                            if t < -8: arr[i,j] = (0,0,0,0)
                            else:
                                t_min, t_max = -2, 32
                                t = max(t_min, min(t_max, t))
                                norm = (t - t_min)/(t_max - t_min)
                                stops = [(0,(10,10,100)),(.2,(10,80,200)),(.35,(10,180,220)),
                                         (.5,(50,230,100)),(.65,(240,230,50)),(.8,(255,150,30)),(1,(255,30,30))]
                                for k in range(len(stops)-1):
                                    if norm <= stops[k+1][0]:
                                        tt = (norm-stops[k][0])/(stops[k+1][0]-stops[k][0])
                                        r = int(stops[k][1][0]+(stops[k+1][1][0]-stops[k][1][0])*tt)
                                        g = int(stops[k][1][1]+(stops[k+1][1][1]-stops[k][1][1])*tt)
                                        b = int(stops[k][1][2]+(stops[k+1][1][2]-stops[k][1][2])*tt)
                                        arr[i,j] = (r,g,b,180); break
                            idx += 1
                arr[mask, 3] = 0
                Image.fromarray(arr, mode="RGBA").save(masked_dir / f"sst_{ym}.png", optimize=True)
            print(f"  ✓ {len(manifest)} PNGs enmascarados en {masked_dir}")
    except ImportError:
        print("  ⚠ shapely no instalado, saltando máscara")
    
    print(f"\n✓ {len(manifest)} PNGs · {total_mb:.2f} MB total")

if __name__ == "__main__":
    main()