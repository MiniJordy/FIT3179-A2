"""Build the cleaned chart datasets in data/ from the raw files in data/raw/.
Run from the DV2 folder:  python3 scripts/build_datasets.py
Inputs : data/vintage2026_region_variety.csv (from parse_vintage_appendix.py), data/gi_region_points.csv (mapshaper),
         data/raw/MI-Annual-export-monitor-FY2026.pdf (via pdftotext), data/raw/comtrade_au_wine_exports_2014_2025.csv
"""
import csv, re, subprocess, collections, json

def read(p): return list(csv.DictReader(open(p, encoding='utf-8')))
def write(p, rows):
    with open(p, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print(f'wrote {p}: {len(rows)} rows')

# ---------- 1. Regional crush 2026 (one row per region in the appendix) ----------
vin = read('data/vintage2026_region_variety.csv')
for r in vin:
    r['region'] = re.sub(r'\s*\(including.*\)$', '', r['region'])          # "Barossa Valley (including Barossa zone – other…)" -> "Barossa Valley"
pts = {p['GI_NAME'].lower(): p for p in read('data/gi_region_points.csv')}
# Appendix rows that are not single GI regions: placed by hand (flagged in the output)
MANUAL = {('Murray Darling – Swan Hill (VIC)', 'VIC'): (142.25, -34.45, 'Murray Darling + Swan Hill GIs, Victorian side (placed near Mildura)'),
          ('Murray Darling – Swan Hill (NSW)', 'NSW'): (143.35, -34.25, 'Murray Darling + Swan Hill GIs, NSW side (placed near Euston/Balranald)'),
          ('Queensland', 'QLD'): (None, None, 'Whole state; placed at Granite Belt')}
reg = collections.OrderedDict()
for r in vin:
    k = (r['region'], r['state'])
    d = reg.setdefault(k, dict(region=r['region'], state=r['state'], tonnes=0, red_tonnes=0, white_tonnes=0, est_value_aud=0))
    t = int(r['tonnes_crushed']); d['tonnes'] += t; d['est_value_aud'] += int(r['est_value_aud'])
    d['red_tonnes' if r['colour'] == 'Red' else 'white_tonnes'] += t
out = []
for (name, st), d in reg.items():
    note = ''
    if (name, st) in MANUAL:
        lon, lat, note = MANUAL[(name, st)]
        if lon is None: p = pts['granite belt']; lon, lat = float(p['lon']), float(p['lat'])
        area = vine = ''
    else:
        p = pts[name.lower()]; lon, lat = float(p['lon']), float(p['lat']); area, vine = p['GI_AREA_KM2'], p['VINE_AREA_HA']
    out.append(dict(d, value_per_tonne=round(d['est_value_aud'] / d['tonnes']) if d['tonnes'] else '',
                    gi_area_km2=area, vine_area_ha=vine, lon=round(lon, 4), lat=round(lat, 4), placement_note=note))
write('data/regions_crush_2026.csv', out)

# ---------- 2. State x variety share of crush 2026 ----------
st_tot = collections.Counter(); sv = collections.Counter()
for r in vin:
    t = int(r['tonnes_crushed']); st_tot[r['state']] += t; sv[(r['state'], r['variety'], r['colour'])] += t
nat = collections.Counter()
for (s, v, c), t in sv.items(): nat[(v, c)] += t
top = [v for v, _ in nat.most_common() if not v[0].startswith('Other')][:10]
rows = [dict(state=s, variety=v, colour=c, tonnes=sv[(s, v, c)], state_tonnes=st_tot[s],
             share_pct=round(100 * sv[(s, v, c)] / st_tot[s], 1)) for s in sorted(st_tot) for (v, c) in top]
write('data/state_variety_2026.csv', rows)
colour = collections.Counter()
for r in vin: colour[r['colour']] += int(r['tonnes_crushed'])
write('data/crush_colour_2026.csv', [dict(colour=c, tonnes=t, share_pct=round(100 * t / sum(colour.values()), 1)) for c, t in colour.items()])

# ---------- 3. Exports by style, FY2015-FY2026 (Annual Export Monitor) ----------
txt = subprocess.run(['pdftotext', '-layout', 'data/raw/MI-Annual-export-monitor-FY2026.pdf', '-'], capture_output=True, text=True).stdout
years = list(range(2015, 2027)); measure = None; group = None; rows = []
num = r'(-?[\d ]*\d(?:\.\d+)?|\.\d+)'
for ln in txt.splitlines():
    if 'VOLUME' in ln: measure = 'volume_kl'; continue
    if 'FOB VALUE' in ln: measure = 'value_aud_m'; continue
    g = re.match(r'^\s+(White|Red|Rosé) still wine\s*$', ln)
    if g: group = g.group(1); continue
    m = re.match(r'^(\s*)([A-Za-zé ]+?)\s{2,}(.*)$', ln)
    if not (m and measure): continue
    label = m.group(2).strip()
    vals = re.findall(r'(?<![\d.])(?:\d{1,3}(?: \d{3})+|\d+)?(?:\.\d+)?(?![\d.])', m.group(3))
    vals = [v for v in vals if v.strip()][:12]
    if len(vals) < 12: continue
    style = (group + ' – ' + label) if label in ('Bottled', 'Unpackaged', 'Other', 'Total') and group else label
    if label in ('Fortified', 'Sparkling', 'Carbonated', 'Other wine', 'Total wine', 'Total still wine'): group = None; style = label
    for y, v in zip(years, vals):
        rows.append(dict(fy=f'FY{y}', year_end=y, style=style, measure=measure, value=float(v.replace(' ', ''))))
write('data/exports_by_style_fy2015_2026.csv', rows)

# ---------- 4. Exports by destination market, 2014-2025 (UN Comtrade, HS 2204) ----------
ct = read('data/raw/comtrade_au_wine_exports_2014_2025.csv')
# A$ = US$ / (US$ per A$), using RBA annual-average exchange rates (see data/raw/rba_audusd_annual_2014_2025.README.txt)
fx = {int(r['year']): float(r['usd_per_aud']) for r in read('data/raw/rba_audusd_annual_2014_2025.csv')}
# Comtrade reports Taiwan as 'Other Asia, nes' (UN naming convention).
RENAME = {'China, Hong Kong SAR': 'Hong Kong', 'Rep. of Korea': 'South Korea', 'United Kingdom': 'UK', 'USA': 'USA', 'Other Asia, nes': 'Taiwan'}
WORLD = {'China': 'Northeast Asia', 'Hong Kong': 'Northeast Asia', 'Japan': 'Northeast Asia', 'South Korea': 'Northeast Asia', 'Taiwan': 'Northeast Asia',
         'Singapore': 'Southeast Asia', 'Malaysia': 'Southeast Asia', 'Thailand': 'Southeast Asia', 'Viet Nam': 'Southeast Asia', 'Indonesia': 'Southeast Asia', 'Philippines': 'Southeast Asia',
         'UK': 'Europe', 'Netherlands': 'Europe', 'Germany': 'Europe', 'Denmark': 'Europe', 'Belgium': 'Europe', 'Sweden': 'Europe', 'Ireland': 'Europe', 'France': 'Europe', 'Finland': 'Europe', 'Norway': 'Europe', 'Switzerland': 'Europe',
         'USA': 'North America', 'Canada': 'North America', 'New Zealand': 'Oceania', 'Fiji': 'Oceania', 'Papua New Guinea': 'Oceania'}
rows = []
for r in ct:
    if r['partner'] == 'World': continue
    name = RENAME.get(r['partner'], r['partner'])
    rows.append(dict(year=int(r['year']), market=name, world_region=WORLD.get(name, 'Rest of world'),
                     value_usd_m=round(float(r['fob_value_usd']) / 1e6, 2),
                     value_aud_m=round(float(r['fob_value_usd']) / 1e6 / fx[int(r['year'])], 2), volume_ml=round(float(r['qty_litres']) / 1e6, 2)))
write('data/exports_by_market_2014_2025.csv', rows)

# ---------- 5. Waffle squares: 2026 crush by colour vs 2025-26 exports by style ----------
def waffle(chart, parts):
    """Turn {category: amount} into 100 squares (largest-remainder rounding so they add to exactly 100).
    Squares fill column by column from the left, so each category forms one solid block."""
    total = sum(parts.values()); exact = {k: 100 * v / total for k, v in parts.items()}
    n = {k: int(x) for k, x in exact.items()}
    for k in sorted(exact, key=lambda k: exact[k] - n[k], reverse=True)[:100 - sum(n.values())]: n[k] += 1
    cells, i = [], 0
    for key_row, k in enumerate(parts):          # key_row = this category's line in the key under the grid
        for _ in range(n[k]):
            cells.append(dict(chart=chart, cell=i, col=i // 10, row=i % 10, category=k,
                              pct=round(exact[k], 1), squares=n[k], key_row=key_row)); i += 1
    return cells
col = {r['colour']: float(r['tonnes']) for r in read('data/crush_colour_2026.csv')}
exp = {(r['style'], r['measure']): float(r['value']) for r in read('data/exports_by_style_fy2015_2026.csv') if r['fy'] == 'FY2026'}
v = lambda s: exp[(s, 'volume_kl')]
cells = waffle('crush', {'Red': col['Red'], 'White': col['White']})
cells += waffle('exports', {'Red': v('Red – Total'), 'White': v('White – Total'), 'Rosé': v('Rosé – Total'),
                            'Sparkling, fortified & other': v('Sparkling') + v('Fortified') + v('Carbonated') + v('Other wine')})
write('data/waffle_2026.csv', cells)

# ---------- 6. Sunburst: what happened to the wine made in 2024-25 ----------
# Source: Wine Australia, Production, Sales and Inventory Report 2024-25 (Tables 2, 6 and 8), read with pdftotext.
psi = subprocess.run(['pdftotext', '-layout', 'data/raw/MI_PSI_Report_2024-25.pdf', '-'], capture_output=True, text=True).stdout
def table(title):
    """{row label: 2024-25 value} for the PSI table whose heading starts with `title`."""
    block = psi[psi.index(title):].split('Table ', 2)[1]
    out = {}
    for ln in block.splitlines()[1:]:
        m = re.match(r'^\s*(\S.*?)\s{2,}([\d.]+)\s+([\d.]+)\s+-?\d+%', ln)   # label, 2023-24, 2024-25, change
        if m: out[m.group(1).strip()] = float(m.group(3))
    return out
prod = table('Table 2: Wine production by colour')['Total wine production']
dom, exp_ = table('Table 6: Domestic wine sales by wine style'), table('Table 8: Export wine sales by wine style')
dom_total, exp_total = dom.pop('Total'), exp_.pop('Total')
STYLE = {'Red and rosé': 'Red & rosé', 'White': 'White', 'Sparkling (inc carbonated)': 'Sparkling & fortified',
         'Fortified': 'Sparkling & fortified', 'Fortified and other': 'Sparkling & fortified'}
def by_style(d):
    out = collections.OrderedDict((s, 0.0) for s in ['Red & rosé', 'White', 'Sparkling & fortified'])
    for k, v in d.items(): out[STYLE[k]] += v
    return out
# Inner ring = the year's production. "Left over" = production minus sales (sales also draw on older stock,
# so this is the net amount not sold that year, not the exact change in inventory).
groups = [('Exported', exp_total, by_style(exp_)), ('Sold in Australia', dom_total, by_style(dom)),
          ('Left over', prod - dom_total - exp_total, None)]
TWO_PI = 2 * 3.141592653589793; rows = []; a = 0.0
for g, total, styles in groups:
    start = a
    for s, v in (styles.items() if styles else [('Unsold', total)]):
        a2 = a + TWO_PI * v / prod
        rows.append(dict(ring='outer', group=g, name=s, ml=round(v, 1), pct_of_group=round(100 * v / total, 1),
                         pct_of_total=round(100 * v / prod, 1), t1=round(a, 5), t2=round(a2, 5), mid=round((a + a2) / 2, 5)))
        a = a2
    rows.append(dict(ring='inner', group=g, name=g, ml=round(total, 1), pct_of_group=100.0, pct_of_total=round(100 * total / prod, 1),
                     t1=round(start, 5), t2=round(a, 5), mid=round((start + a) / 2, 5)))
write('data/wine_flows_2024_25.csv', rows)
