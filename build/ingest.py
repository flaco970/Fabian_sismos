#!/usr/bin/env python3
"""
ingest.py — Baja eventos sísmicos USGS y los guarda en SQLite.

Uso:
    python3 ingest.py --region sudamerica --years 3
    python3 ingest.py --region mundial --years 1 --min-mag 5.0
    python3 ingest.py --region sudamerica --start 2020-01-01 --end 2026-08-16

Regiones predefinidas (bounding box):
    sudamerica_ext   lat -60..30,  lon -90..-30  (Sudamérica + Caribe)
    sudamerica       lat -60..15,  lon -85..-50  (Sudamérica continental)
    ecuador          lat -7..3,    lon -82..-75  (Ecuador continental + Galápagos)
    nazca_subduction lat -50..5,   lon -85..-65  (Zona de subducción Nazca-SAM)
    andes            lat -55..12,  lon -82..-65  (Cordillera de los Andes)
    mundial          sin filtro geográfico
"""
import argparse, sqlite3, urllib.request, ssl, json, sys, time as tt
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).parent.parent
DB   = ROOT/"data/sismos.db"

REGIONS = {
    "sudamerica_ext":   {"minlat": -60, "maxlat":  30, "minlon": -90, "maxlon": -30},
    "sudamerica":       {"minlat": -60, "maxlat":  15, "minlon": -85, "maxlon": -50},
    "ecuador":          {"minlat":  -7, "maxlat":   3, "minlon": -82, "maxlon": -75},
    "nazca_subduction": {"minlat": -50, "maxlat":   5, "minlon": -85, "maxlon": -65},
    "andes":            {"minlat": -55, "maxlat":  12, "minlon": -82, "maxlon": -65},
}

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--region", default="sudamerica_ext", choices=list(REGIONS.keys())+["mundial"])
    p.add_argument("--years", type=int, default=3, help="Años hacia atrás desde hoy")
    p.add_argument("--start", help="YYYY-MM-DD (override --years)")
    p.add_argument("--end",   help="YYYY-MM-DD (default: hoy)")
    p.add_argument("--min-mag", type=float, default=4.5)
    p.add_argument("--db", default=str(DB))
    return p.parse_args()

def fetch_usgs(url):
    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, headers={"User-Agent": "Fabian-sismos/1.0"})
    with urllib.request.urlopen(req, context=ctx, timeout=120) as r:
        return json.loads(r.read())

def main():
    args = parse_args()
    end_date   = args.end   or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    start_date = args.start or (
        datetime.now(timezone.utc).replace(year=datetime.now().year - args.years)
        .strftime("%Y-%m-%d"))

    bbox = REGIONS.get(args.region, {})

    conn = sqlite3.connect(args.db)
    conn.execute("PRAGMA journal_mode=WAL")  # más rápido en escrituras
    cur = conn.cursor()

    # Log de ingesta
    cur.execute("""INSERT INTO ingest_log(started_at,start_date,end_date,min_mag,region)
                   VALUES(?,?,?,?,?)""",
                (datetime.now(timezone.utc).isoformat(), start_date, end_date,
                 args.min_mag, args.region))
    log_id = cur.lastrowid
    conn.commit()

    print(f"=== INGESTA USGS ===")
    print(f"  Región:    {args.region} {bbox}")
    print(f"  Rango:     {start_date} → {end_date}")
    print(f"  Min mag:   {args.min_mag}")

    # Paginar por año para evitar el límite de 20k eventos/request de USGS
    sd = datetime.strptime(start_date, "%Y-%m-%d")
    ed = datetime.strptime(end_date,   "%Y-%m-%d")
    year_starts = []
    cur_year = sd.year
    while cur_year <= ed.year:
        y_start = max(sd, datetime(cur_year, 1, 1))
        y_end   = min(ed, datetime(cur_year, 12, 31))
        year_starts.append((y_start.strftime("%Y-%m-%d"), y_end.strftime("%Y-%m-%d")))
        cur_year += 1

    total = 0
    for ys, ye in year_starts:
        url = (f"https://earthquake.usgs.gov/fdsnws/event/1/query?"
               f"format=geojson&starttime={ys}&endtime={ye}"
               f"&minmagnitude={args.min_mag}&orderby=time-asc")
        for k, v in bbox.items():
            url += f"&{k}={v}"
        print(f"\n  GET {ys}→{ye} ...", end="", flush=True)
        try:
            data = fetch_usgs(url)
        except Exception as e:
            print(f"\n  ✗ Error: {e}")
            continue
        feats = data.get("features", [])
        print(f" {len(feats)} eventos")
        for f in feats:
            p = f["properties"]; c = f["geometry"]["coordinates"]
            try:
                cur.execute("""INSERT OR REPLACE INTO events
                    (id,time_ms,mag,place,lat,lon,depth_km,url,updated_at)
                    VALUES(?,?,?,?,?,?,?,?,?)""",
                    (f["id"], p["time"], p["mag"], p.get("place",""),
                     c[1], c[0], c[2], p.get("url",""),
                     datetime.now(timezone.utc).isoformat()))
                total += 1
            except sqlite3.IntegrityError:
                pass
        conn.commit()
        tt.sleep(0.4)  # cortesía a USGS

    # Cerrar log
    cur.execute("""UPDATE ingest_log
                   SET finished_at=?, n_events=?, status='ok'
                   WHERE id=?""",
                (datetime.now(timezone.utc).isoformat(), total, log_id))
    conn.commit()

    # Stats finales
    n = cur.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    rng = cur.execute("SELECT MIN(time_ms), MAX(time_ms) FROM events").fetchone()
    print(f"\n✓ INGESTA COMPLETA")
    print(f"  Insertados: {total}")
    print(f"  Total en DB: {n}")
    if rng[0]:
        print(f"  Rango: {tt.strftime('%Y-%m-%d', tt.gmtime(rng[0]/1000))} → "
              f"{tt.strftime('%Y-%m-%d', tt.gmtime(rng[1]/1000))}")
    conn.close()

if __name__ == "__main__":
    main()