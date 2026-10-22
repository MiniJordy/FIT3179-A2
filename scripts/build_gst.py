"""Map 1 data: mean growing season temperature (GST, Oct-Apr, 1997-2017) for every wine region (GI).
Run from the DV2 folder:  python3 scripts/build_gst.py   (needs poppler's pdfimages, Pillow, numpy)

Source: Wine Australia / Remenyi et al. (2019) "Australia's Wine Future - A Climate Atlas", National Summary,
Figure 12 (p. 14): regions ranked by observed mean GST 1997-2017. The figure is a bar chart without printed
values, so each bar's length is measured from the embedded 300 dpi image and converted to degrees C using the
x-axis tick marks (10, 12, ... 22 C). Check: the 10 regions that also appear as printed numbers in University of
Adelaide Wine Economics working paper 2021-07 (Table 4, GST 1997-2017) match these readings within 0.05 C.

Writes data/region_gst_1997_2017.csv  (region = GI name as in data/gi_regions.topojson)
       data/gst_map_labels.csv      (the regions labelled on Map 1: dot position, label position, text)
"""
import csv, subprocess, tempfile, os
import numpy as np
from PIL import Image

PDF = 'data/raw/Climate_Atlas_National_Summary.pdf'

# Bar labels in Figure 12, top (hottest) to bottom, transcribed from the figure.
ATLAS_ORDER = ['South Burnett', 'Murray Darling', 'Riverina', 'Swan District', 'Riverland', 'Perth Hills', 'Swan Hill',
    'Hastings River', 'Cowra', 'Adelaide Plains', 'Southern Flinders Ranges', 'Hunter', 'Peel', 'Perricoota', 'Gundagai',
    'Rutherglen', 'Goulburn Valley', 'Mudgee', 'Glenrowan', 'Hilltops', 'Geographe', 'Shoalhaven Coast', 'Langhorne Creek',
    'Clare Valley', 'Barossa Valley', 'Margaret River', 'Granite Belt', 'Bendigo', 'Mclaren Vale', 'Blackwood Valley',
    'Currency Creek', 'Heathcote', 'Eden Valley', 'New England', 'Pemberton', 'Orange', 'Manjimup', 'Southern Fleurieu',
    'Southern Highlands', 'Great Southern', 'Pyrenees', 'Adelaide Hills', 'Beechworth', 'Padthaway', 'Canberra District',
    'Kangaroo Island', 'Strathbogie Ranges', 'King Valley', 'Sunbury', 'Wrattonbully', 'Tumbarumba', 'Mornington Peninsula',
    'Coonawarra', 'Geelong', 'Grampians', 'Mount Benson', 'Robe', 'Alpine Valleys', 'Upper Goulburn', 'Mount Gambier',
    'Henty', 'Yarra Valley', 'Tasmania Furneaux Islands', 'Macedon Ranges', 'Tasmania King Island', 'Tasmania North East',
    'Tasmania Central North', 'Tasmania East Coast', 'Tasmania North West Coast', 'Tasmania South East',
    'Tasmania Upper Derwent Valley']
RENAME = {'New England': 'New England Australia'}          # atlas name -> GI name in our boundary file
TICKS_PX = [67.5, 462.5, 857.5, 1252.5, 1648, 2043.5, 2438.5]   # x-axis tick marks in the 2833 px image
TICKS_C = [10, 12, 14, 16, 18, 20, 22]

def figure12():
    with tempfile.TemporaryDirectory() as d:
        subprocess.run(['pdfimages', '-f', '14', '-l', '14', '-png', PDF, os.path.join(d, 'img')], check=True)
        return np.array(Image.open(os.path.join(d, 'img-000.png')).convert('RGB')).astype(int)

def measure(a):
    k, b = np.polyfit(TICKS_PX, TICKS_C, 1)
    col = a[:, 80]                                         # a column just inside the plot, crossing every bar
    is_bar = ~(col >= 230).all(1)                          # anything not grey background / white
    segs, start = [], None
    for y in range(len(col)):                              # vertical runs of one bar colour = one bar
        new_bar = start is not None and (not is_bar[y] or np.abs(a[y, 80] - a[y - 1, 80]).sum() > 30)
        if new_bar: segs.append((start, y - 1)); start = None
        if is_bar[y] and start is None: start = y
    segs = [(s, e) for s, e in segs if e - s > 5]
    values = []
    for s, e in segs:
        y = (s + e) // 2; c = a[y, 80]; x = 80
        while x < a.shape[1] - 1 and np.abs(a[y, x + 1] - c).sum() < 40: x += 1   # walk to the bar's right end
        values.append(float(np.polyval([k, b], x + 0.5)))
    return values

values = measure(figure12())
assert len(values) == len(ATLAS_ORDER), (len(values), len(ATLAS_ORDER))
atlas = dict(zip(ATLAS_ORDER, values))

rows = []
tas = {n: v for n, v in atlas.items() if n.startswith('Tasmania')}
for name, v in atlas.items():
    if name.startswith('Tasmania'): continue
    rows.append(dict(region=RENAME.get(name, name), gst_c=round(v, 1), note=''))
rows.append(dict(region='Tasmania', gst_c=round(sum(tas.values()) / len(tas), 1),
                 note=f'Average of the atlas\'s {len(tas)} Tasmanian areas ({min(tas.values()):.1f}-{max(tas.values()):.1f} C)'))
rows.sort(key=lambda r: -r['gst_c'])
with open('data/region_gst_1997_2017.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=['region', 'gst_c', 'note'], lineterminator='\n'); w.writeheader(); w.writerows(rows)
print(f'wrote data/region_gst_1997_2017.csv: {len(rows)} regions, {rows[-1]["gst_c"]}-{rows[0]["gst_c"]} C')

# Regions labelled on Map 1: (panel, region, dot lon, dot lat, label lon, label lat, text alignment)
LABELS = [('WA', 'Swan District', 115.83, -31.49, 116.15, -31.49, 'left'),
          ('WA', 'Margaret River', 115.15, -33.96, 115.45, -33.96, 'left'),
          ('WA', 'Great Southern', 117.62, -34.58, 117.62, -35.25, 'center'),
          ('SE', 'South Burnett', 151.75, -26.44, 151.25, -26.44, 'right'),
          ('SE', 'Hunter', 150.88, -32.33, 151.35, -32.33, 'left'),
          ('SE', 'Riverina', 145.93, -34.33, 146.45, -34.33, 'left'),
          ('SE', 'Murray Darling', 142.39, -34.25, 142.0, -33.0, 'center'),
          ('SE', 'Riverland', 140.34, -34.23, 140.2, -32.9, 'center'),
          ('SE', 'Barossa Valley', 138.94, -34.51, 138.45, -34.51, 'right'),
          ('SE', 'Coonawarra', 140.87, -37.31, 140.45, -37.55, 'right'),
          ('SE', 'Yarra Valley', 145.54, -37.72, 146.05, -37.72, 'left'),
          ('SE', 'Tasmania', 146.58, -42.02, 146.58, -42.02, 'center')]
gst_of = {r['region']: r['gst_c'] for r in rows}
with open('data/gst_map_labels.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f, lineterminator='\n')
    w.writerow(['view', 'region', 'lon', 'lat', 'llon', 'llat', 'align', 'label', 'dot'])
    for view, region, lon, lat, llon, llat, align in LABELS:
        w.writerow([view, region, lon, lat, llon, llat, align, f'{region}  {gst_of[region]:.1f}°', int(region != 'Tasmania')])
print(f'wrote data/gst_map_labels.csv: {len(LABELS)} labels')
