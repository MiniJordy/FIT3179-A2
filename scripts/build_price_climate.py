"""Chart 7 data: growing season temperature vs value per tonne for each wine region (2026 crush).
Run from the DV2 folder (after build_gst.py):  python3 scripts/build_price_climate.py
Reads  data/regions_crush_2026.csv     (tonnes and estimated value by Vintage Report region)
       data/region_gst_1997_2017.csv   (growing season temperature by GI region)
Writes data/region_price_climate_2026.csv
Murray Darling - Swan Hill is reported in two state parts: they are combined into one point (tonnes and value added)
with the average of the Murray Darling and Swan Hill temperatures. Queensland (Granite Belt + South Burnett reported
together, 541 t) is left out because the two regions have very different temperatures.
"""
import csv, math

gst = {r['region']: float(r['gst_c']) for r in csv.DictReader(open('data/region_gst_1997_2017.csv', encoding='utf-8'))}
gst['McLaren Vale'] = gst['Mclaren Vale']
MDSH = 'Murray Darling–Swan Hill'
gst[MDSH] = round((gst['Murray Darling'] + gst['Swan Hill']) / 2, 1)

agg = {}
for r in csv.DictReader(open('data/regions_crush_2026.csv', encoding='utf-8')):
    name = MDSH if r['region'].startswith('Murray Darling') else r['region']
    if name == 'Queensland': continue
    a = agg.setdefault(name, dict(region=name, state=r['state'] if name != MDSH else 'VIC/NSW', tonnes=0, est_value_aud=0))
    a['tonnes'] += int(r['tonnes']); a['est_value_aud'] += int(r['est_value_aud'])
rows = []
for a in agg.values():
    a['gst_c'] = gst[a['region']]
    a['value_per_tonne'] = round(a['est_value_aud'] / a['tonnes'])
    rows.append(a)
rows.sort(key=lambda r: r['gst_c'])
with open('data/region_price_climate_2026.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=['region', 'state', 'gst_c', 'tonnes', 'est_value_aud', 'value_per_tonne'], lineterminator='\n')
    w.writeheader(); w.writerows(rows)

xs = [r['gst_c'] for r in rows]; ys = [math.log(r['value_per_tonne']) for r in rows]
mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
r_ = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / math.sqrt(sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys))
slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
print(f'wrote data/region_price_climate_2026.csv: {len(rows)} regions; corr(GST, log price) = {r_:.2f}; '
      f'each +1 C ~ {100 * (math.exp(slope) - 1):.0f}% price')
