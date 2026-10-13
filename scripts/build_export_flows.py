"""Map 3 pre-processing: curved export routes from Australia to its top markets, for every year 2014-2025
(the map has a year slider).
Run from the DV2 folder:  python3 scripts/build_export_flows.py
Reads  data/exports_by_market_2014_2025.csv (UN Comtrade, converted to A$ with RBA annual rates; calendar years)
Writes data/export_markets_by_year.csv  (one row per market per year: point, label position, value, share, rank)
       data/export_routes_by_year.csv   (41 points per market per year tracing a curved route)
The map always shows the same set of markets: every market that is in the top TOP_N in at least one year.
Years outside the top TOP_N are kept, so a falling market's line thins out instead of vanishing.
Every market in that set needs an entry in PLACES.
Each route is a quadratic Bezier curve drawn in lon/lat. The control point sits beside the straight
line's midpoint, pushed sideways by BEND x route length, so routes going the same way fan apart.
"""
import csv, collections

TOP_N = 10
ORIGIN = (134.4, -25.6)          # centre of Australia: one symbolic starting point for every route

# market: (lon, lat, bend, label_lon, label_lat, label_align)  -- label '' = no label (tooltip only)
# Points are country centres, except Singapore and Hong Kong (city).
PLACES = {
    'China':       (104.0, 35.0,  0.12, 104.0, 41.0, 'center'),
    'UK':          (-2.0,  53.0,  0.06, -2.0,  59.5, 'center'),
    'USA':         (-98.0, 39.0, -0.20, -94.0, 38.0, 'left'),
    'Canada':      (-100.0, 56.0, -0.32, -100.0, 62.5, 'center'),
    'Singapore':   (103.8, 1.35, -0.10, 99.5,  -2.5, 'right'),
    'Hong Kong':   (114.2, 22.3, -0.16, 110.5, 24.0, 'right'),
    'New Zealand': (172.5, -41.5, 0.30, 176.5, -45.5, 'left'),
    'Thailand':    (101.0, 15.0,  0.02, 97.0,  15.0, 'right'),
    'Japan':       (138.0, 36.5,  0.20, 141.5, 39.5, 'left'),
    'Malaysia':    (102.0, 4.0,  -0.03, None, None, ''),
    'Netherlands': (5.3,   52.2,  0.12, None, None, ''),
    'Denmark':     (9.5,   56.0,  0.18, None, None, ''),
    'Belgium':     (4.6,   50.6,  0.09, None, None, ''),
    'South Korea': (127.8, 36.3,  0.10, None, None, ''),
    'Taiwan':      (121.0, 23.7, -0.04, 124.0, 23.0, 'left'),
}

by_year = collections.defaultdict(list)
for r in csv.DictReader(open('data/exports_by_market_2014_2025.csv', encoding='utf-8')):
    by_year[int(r['year'])].append(r)

def curve(lon, lat, bend):
    """41 points along a quadratic Bezier from ORIGIN to (lon, lat)."""
    L = lon + 360 if lon < -30 else lon               # go east across the Pacific to the Americas
    x0, y0 = ORIGIN; dx, dy = L - x0, lat - y0
    cx, cy = (x0 + L) / 2 - dy * bend, (y0 + lat) / 2 + dx * bend   # control point beside the midpoint
    return [((1 - t) ** 2 * x0 + 2 * (1 - t) * t * cx + t * t * L, (1 - t) ** 2 * y0 + 2 * (1 - t) * t * cy + t * t * lat)
            for t in (i / 40 for i in range(41))]

ranked = {y: sorted(rows, key=lambda r: -float(r['value_aud_m'])) for y, rows in by_year.items()}
SHOWN = {r['market'] for y in ranked for r in ranked[y][:TOP_N]}          # ever in a year's top TOP_N
missing = sorted(SHOWN - set(PLACES))
assert not missing, f'add coordinates for {missing}'

markets, routes = [], []
for year in sorted(by_year):
    rows = ranked[year]
    total = sum(float(r['value_aud_m']) for r in rows)
    for rank, r in enumerate(rows, 1):
        if r['market'] not in SHOWN: continue
        lon, lat, bend, llon, llat, align = PLACES[r['market']]
        v = float(r['value_aud_m'])
        markets.append(dict(year=year, rank=rank, market=r['market'], world_region=r['world_region'], value_aud_m=round(v, 1),
                            volume_ml=round(float(r['volume_ml']), 1), share_pct=round(100 * v / total, 1),
                            lon=lon, lat=lat, label_lon=llon if align else '', label_lat=llat if align else '', label_align=align))
        for i, (x, y) in enumerate(curve(lon, lat, bend)):
            routes.append(dict(year=year, market=r['market'], value_aud_m=round(v, 1), share_pct=round(100 * v / total, 1), t=round(i / 40, 3), lon=round(x, 3), lat=round(y, 3)))
    print(f'{year}: {len(SHOWN)} markets shown = {sum(m["value_aud_m"] for m in markets if m["year"] == year) / total:.0%} of A${total:,.0f}m')

for path, data in (('data/export_markets_by_year.csv', markets), ('data/export_routes_by_year.csv', routes)):
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(data[0])); w.writeheader(); w.writerows(data)
    print(f'wrote {path}: {len(data)} rows')
