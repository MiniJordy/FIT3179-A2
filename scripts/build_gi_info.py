"""One row per wine region (GI) with everything the three maps show in their tooltips, so the map specs only
need a single lookup instead of repeating the same calculations in every panel.
Run from the DV2 folder after the other build scripts:  python3 scripts/build_gi_info.py
Reads  data/gi_regions.topojson, data/region_gst_1997_2017.csv, data/regions_bubbles_2026.csv,
       data/region_price_climate_2026.csv
Writes data/gi_region_info.csv
  gi_name     - GI name exactly as in the boundary file (the lookup key)
  label       - name to show (spelling fixed, e.g. McLaren Vale)
  state, gst_c, gst_note           - for Map 1
  crush_text                       - for Map 2 ("12,345 t", "Counted in ...", "N/A")
  region, price_txt, tonnes_txt, price_state - for Chart 7 (region = the point it links to on the scatter;
                                     price_state = state colour, or "none" when no price is published)
"""
import csv, json

MDSH = 'Murray Darling–Swan Hill'
LABEL = {'Mclaren Vale': 'McLaren Vale', 'New England Australia': 'New England'}

topo = json.load(open('data/gi_regions.topojson', encoding='utf-8'))
gis = [g['properties'] for g in topo['objects']['wine_gi_regions']['geometries']]
gst = {r['region']: r for r in csv.DictReader(open('data/region_gst_1997_2017.csv', encoding='utf-8'))}
tonnes = {r['region']: int(r['tonnes']) for r in csv.DictReader(open('data/regions_bubbles_2026.csv', encoding='utf-8'))}
price = {r['region']: r for r in csv.DictReader(open('data/region_price_climate_2026.csv', encoding='utf-8'))}

rows = []
for p in sorted(gis, key=lambda p: p['GI_NAME']):
    name = p['GI_NAME']; label = LABEL.get(name, name)
    if label in tonnes: crush = f'{tonnes[label]:,} t'
    elif name in ('Murray Darling', 'Swan Hill'): crush = f'Counted in {MDSH}'
    elif name in ('Granite Belt', 'South Burnett'): crush = 'Counted in the Queensland total'
    else: crush = 'N/A'
    link = MDSH if name in ('Murray Darling', 'Swan Hill') else label
    pr = price.get(link)
    rows.append(dict(
        gi_name=name, label=label, state=p['STATE'],
        gst_c=gst[name]['gst_c'], gst_note=gst[name]['note'], crush_text=crush,
        region=link,
        price_txt=f'${int(pr["value_per_tonne"]):,}' if pr else 'Not published',
        tonnes_txt=(f'{int(pr["tonnes"]):,}' + (' (both regions together)' if link == MDSH else '')) if pr else 'Not published',
        price_state=p['STATE'] if pr else 'none'))

with open('data/gi_region_info.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator='\n'); w.writeheader(); w.writerows(rows)
print(f'wrote data/gi_region_info.csv: {len(rows)} regions')
