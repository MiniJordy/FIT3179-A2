"""Parse Wine Australia National Vintage Report 2026 appendix (pdftotext -layout output)
into a tidy CSV: region, state, colour, variety, tonnes_crushed, est_value_aud.
Usage: pdftotext -layout MI_VintageReport2026_Appx_F.pdf appx.txt && python3 parse_vintage_appendix.py appx.txt out.csv
"""
import re, sys, csv

STATES = {'NSW', 'QLD', 'SA', 'TAS', 'VIC', 'WA'}
row_re = re.compile(r'^  (\S.*?)\s{2,}.*?(-?[\d,]+)\s+\$([\d,]+)\s*$')       # variety row: ... total crushed  $est value
tot_re = re.compile(r'^(Red|White|Grand) Total\b.*?(-?[\d,]+)\s+\$([\d,]+)\s*$')
title_re = re.compile(r'^(\S.*?)\s{2,}(NSW|QLD|SA|TAS|VIC|WA)\s*$')
num = lambda s: int(s.replace(',', ''))

lines = open(sys.argv[1], encoding='utf-8').read().splitlines()
rows, totals, region, state, colour = [], [], None, None, None
for ln in lines:
    m = title_re.match(ln)
    if m:
        region = re.sub(r'\s*\(continued\)', '', m.group(1)).strip(); state = m.group(2); continue
    s = ln.strip()
    if s in ('Red', 'White'):
        colour = s; continue
    m = tot_re.match(s)
    if m and region:
        totals.append((region, state, m.group(1), num(m.group(2)), num(m.group(3)))); continue
    m = row_re.match(ln)
    if m and region and colour:
        rows.append(dict(region=region, state=state, colour=colour, variety=m.group(1).strip(),
                         tonnes_crushed=num(m.group(2)), est_value_aud=num(m.group(3))))

with open(sys.argv[2], 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

# self-check: variety rows must sum to each region's printed Red/White totals
from collections import defaultdict
agg = defaultdict(lambda: [0, 0])
for r in rows:
    agg[(r['region'], r['state'], r['colour'])][0] += r['tonnes_crushed']; agg[(r['region'], r['state'], r['colour'])][1] += r['est_value_aud']
bad = [(t, agg[(t[0], t[1], t[2])]) for t in totals if t[2] != 'Grand' and abs(agg[(t[0], t[1], t[2])][0] - t[3]) > 2]
print(f'{len(rows)} variety rows, {len({(r["region"], r["state"]) for r in rows})} regions; total mismatches: {len(bad)}')
for b in bad[:10]: print('  MISMATCH', b)
