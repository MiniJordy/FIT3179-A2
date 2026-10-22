"""Chart 10 data: where each of the 10 most-crushed grape varieties is grown, by growing season temperature.
Run from the DV2 folder (after build_gst.py):  python3 scripts/build_variety_climate.py
Reads  data/vintage2026_region_variety.csv  (tonnes crushed by region and variety, Vintage Report 2026 appendix)
       data/region_gst_1997_2017.csv        (growing season temperature by GI region, Climate Atlas)
Writes data/variety_climate_2026.csv        (one row per variety x region with tonnes > 0)
The 10 varieties are the same as the state x variety heatmap (Chart 4).
Vintage Report regions that are not single GIs:
  Murray Darling - Swan Hill (NSW and VIC parts) -> average of the Murray Darling and Swan Hill GIs
  Queensland (541 t, Granite Belt + South Burnett together) -> left out
"""
import csv, collections

VARIETIES = ['Shiraz', 'Cabernet Sauvignon', 'Merlot', 'Pinot Noir',
             'Chardonnay', 'Sauvignon Blanc', 'Pinot Gris/Grigio', 'Muscat Gordo Blanco', 'Semillon', 'Colombard']
gst = {r['region']: float(r['gst_c']) for r in csv.DictReader(open('data/region_gst_1997_2017.csv', encoding='utf-8'))}
md_sh = round((gst['Murray Darling'] + gst['Swan Hill']) / 2, 1)
NAME = {'Barossa Valley (including Barossa zone – other: 873 tonnes)': ('Barossa Valley', gst['Barossa Valley']),
        'McLaren Vale': ('McLaren Vale', gst['Mclaren Vale']),
        'Murray Darling – Swan Hill (NSW)': ('Murray Darling–Swan Hill (NSW)', md_sh),
        'Murray Darling – Swan Hill (VIC)': ('Murray Darling–Swan Hill (VIC)', md_sh)}

rows = []
for r in csv.DictReader(open('data/vintage2026_region_variety.csv', encoding='utf-8')):
    t = int(r['tonnes_crushed'])
    if r['variety'] not in VARIETIES or t <= 0 or r['region'] == 'Queensland': continue
    name, g = NAME.get(r['region'], (r['region'], gst.get(r['region'])))
    assert g is not None, f'no GST for {r["region"]}'
    rows.append(dict(variety=r['variety'], colour=r['colour'], region=name, state=r['state'], gst_c=g, tonnes=t))

tot = collections.Counter(); wsum = collections.Counter()
for r in rows: tot[r['variety']] += r['tonnes']; wsum[r['variety']] += r['tonnes'] * r['gst_c']
for r in rows:
    r['share_pct'] = round(100 * r['tonnes'] / tot[r['variety']], 1)
    r['variety_avg_gst'] = round(wsum[r['variety']] / tot[r['variety']], 2)
rows.sort(key=lambda r: (r['variety_avg_gst'], -r['tonnes']))
with open('data/variety_climate_2026.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator='\n'); w.writeheader(); w.writerows(rows)
print(f'wrote data/variety_climate_2026.csv: {len(rows)} rows')
for v in sorted(tot, key=lambda v: wsum[v] / tot[v]):
    print(f'  {v:20s} {tot[v]:7,d} t  avg {wsum[v] / tot[v]:.1f} C')
