// Map 2 pre-processing: place one bubble per wine region so that no two bubbles overlap
// (a "Dorling-style" layout), then pick a label position for each labelled bubble.
//
// Why pre-compute? Vega-Lite can't move marks to avoid overlaps, so we do it here once and save the
// shifted positions (dlon/dlat) as data columns. The spec then just plots them, using the SAME
// projections, which this script also writes into specs/crush_bubble_map.json.
//
// Run from the DV2 folder:  NODE_PATH=<folder with d3-geo installed> node scripts/build_bubble_positions.mjs
import fs from 'fs';
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const d3 = require('d3-geo');

const csv = t => { const [h, ...rows] = t.trim().split(/\r?\n/); const cols = h.split(',');
  return rows.map(r => { const v = r.match(/("([^"]|"")*"|[^,]*)(,|$)/g).map(s => s.replace(/,$/, '').replace(/^"|"$/g, '').replace(/""/g, '"'));
    return Object.fromEntries(cols.map((c, i) => [c, v[i]])); }); };
const crush = csv(fs.readFileSync('data/regions_crush_2026.csv', 'utf8'));

// ---- size scale: bubble AREA proportional to tonnes (must match the spec's size scale) ----
const SIZE_DOMAIN_MAX = 340000, SIZE_RANGE_MAX = 4400;        // px² at 340,000 t  (radius ≈ 37 px)
const MIN_T = 2500;                                            // floor so the smallest regions stay visible
const radius = t => Math.sqrt((SIZE_RANGE_MAX * Math.max(t, MIN_T) / SIZE_DOMAIN_MAX) / Math.PI);

// ---- the two views ----
const VIEWS = {
  SE: { W: 580, H: 560, box: [[134.6, -26.2], [153.6, -43.8]], parallels: [-30, -40], rotate: [-144, 0] },
  WA: { W: 220, H: 260, box: [[114.9, -31.0], [118.4, -35.1]], parallels: [-30, -36], rotate: [-117, 0] },
};
for (const v of Object.values(VIEWS)) {
  v.proj = d3.geoConicEqualArea().parallels(v.parallels).rotate(v.rotate)
    .fitExtent([[12, 12], [v.W - 12, v.H - 12]], { type: 'MultiPoint', coordinates: v.box });
}

// Only regions with published crush figures get a bubble; the rest are shown by their shaded boundary only.
// Murray Darling–Swan Hill is published as two touching bubbles (Vic and NSW sides of the river) that share
// one name label, split over two lines ('|' = line break; the spec sets lineBreak: '|').
const LABEL = { 'Murray Darling – Swan Hill (VIC)': '', 'Murray Darling – Swan Hill (NSW)': 'Murray Darling–|Swan Hill' };
const ALWAYS_LABEL = new Set(['Yarra Valley', 'Hunter', 'Margaret River', 'Great Southern', 'Tasmania', 'Queensland', 'Swan District']);

const spots = (x, y, r, w, h, g) => [
  ['left', x + r + g, y, [x + r + g, y - h / 2, x + r + g + w, y + h / 2]],
  ['right', x - r - g, y, [x - r - g - w, y - h / 2, x - r - g, y + h / 2]],
  ['center', x, y + r + g + h / 2, [x - w / 2, y + r + g, x + w / 2, y + r + g + h]],
  ['center', x, y - r - g - h / 2, [x - w / 2, y - r - g - h, x + w / 2, y - r - g]],
  ['left', x + r * 0.7 + g, y - r * 0.7 - h / 2, [x + r * 0.7 + g, y - r * 0.7 - h, x + r * 0.7 + g + w, y - r * 0.7]],
  ['left', x + r * 0.7 + g, y + r * 0.7 + h / 2, [x + r * 0.7 + g, y + r * 0.7, x + r * 0.7 + g + w, y + r * 0.7 + h]],
  ['right', x - r * 0.7 - g, y - r * 0.7 - h / 2, [x - r * 0.7 - g - w, y - r * 0.7 - h, x - r * 0.7 - g, y - r * 0.7]],
  ['right', x - r * 0.7 - g, y + r * 0.7 + h / 2, [x - r * 0.7 - g - w, y + r * 0.7, x - r * 0.7 - g, y + r * 0.7 + h]]];

const nodes = [];
for (const c of crush) {
  const t = +c.tonnes;
  nodes.push({ region: c.region, state: c.state, tonnes: t, red_tonnes: +c.red_tonnes, white_tonnes: +c.white_tonnes,
    value_per_tonne: +c.value_per_tonne, lon: +c.lon, lat: +c.lat, r: radius(t),
    label: (t >= 9000 || ALWAYS_LABEL.has(c.region)) ? (c.region in LABEL ? LABEL[c.region] : c.region) : '' });
}
for (const n of nodes) n.view = n.lon < 125 ? 'WA' : 'SE';

// ---- Dorling-style relaxation: repeatedly push overlapping circles apart, with a gentle pull home ----
for (const [name, v] of Object.entries(VIEWS)) {
  const ns = nodes.filter(n => n.view === name);
  for (const n of ns) { [n.x0, n.y0] = v.proj([n.lon, n.lat]); n.x = n.x0; n.y = n.y0; }
  for (let it = 0; it < 600; it++) {
    for (const n of ns) { n.x += (n.x0 - n.x) * 0.02; n.y += (n.y0 - n.y) * 0.02; }
    for (let i = 0; i < ns.length; i++) for (let j = i + 1; j < ns.length; j++) {
      const a = ns[i], b = ns[j]; const dx = b.x - a.x, dy = b.y - a.y, d = Math.hypot(dx, dy) || 0.01, min = a.r + b.r + 1.5;
      if (d < min) { const k = (min - d) / d, wa = b.r / (a.r + b.r), wb = a.r / (a.r + b.r);
        a.x -= dx * k * wa; a.y -= dy * k * wa; b.x += dx * k * wb; b.y += dy * k * wb; }
    }
    for (const n of ns) { n.x = Math.min(v.W - n.r - 2, Math.max(n.r + 2, n.x)); n.y = Math.min(v.H - n.r - 2, Math.max(n.r + 2, n.y)); }
  }

  // ---- label placement: try right, left, above, below; keep the first spot that hits nothing ----
  const boxes = ns.map(n => [n.x - n.r, n.y - n.r, n.x + n.r, n.y + n.r]);
  const hit = (b) => boxes.some(o => b[0] < o[2] && b[2] > o[0] && b[1] < o[3] && b[3] > o[1]) || b[0] < 0 || b[2] > v.W || b[1] < 0 || b[3] > v.H;
  for (const n of ns.filter(n => n.label).sort((a, b) => b.r - a.r)) {
    const lines = n.label.split('|');
    const w = Math.max(...lines.map(l => l.length)) * 6.1, h = 13 * lines.length;
    const tries = [];
    // Spots hugging the bubble first; if none is free, try further out and draw a thin callout line to the label.
    for (const g of [3, 8, 22, 36]) tries.push(...spots(n.x, n.y, n.r, w, h, g).map(t => [...t, g]));
    const pick = tries.find(t => !hit(t[3]));
    if (!pick) { console.warn('no free label spot for', n.label); n.label = ''; continue; }
    [n.lalign, n.lx, n.ly] = pick; boxes.push(pick[3]);
    if (pick[4] > 8) {   // callout: from the bubble's edge to the nearest point of the label box
      const [x0, y0, x1, y1] = pick[3]; const tx = Math.min(Math.max(n.x, x0), x1), ty = Math.min(Math.max(n.y, y0), y1);
      const d = Math.hypot(tx - n.x, ty - n.y); n.c1 = [n.x + (tx - n.x) * n.r / d, n.y + (ty - n.y) * n.r / d]; n.c2 = [tx, ty]; }
  }
  for (const n of ns) {
    [n.dlon, n.dlat] = v.proj.invert([n.x, n.y]);
    if (n.label) [n.llon, n.llat] = v.proj.invert([n.lx, n.ly]);
    if (n.c1) { [n.c1lon, n.c1lat] = v.proj.invert(n.c1); [n.c2lon, n.c2lat] = v.proj.invert(n.c2); }
    n.moved = Math.hypot(n.x - n.x0, n.y - n.y0) > n.r + 2;   // only draw a leader line when the true spot is outside the bubble
  }
}

// ---- write data ----
const cols = ['region', 'state', 'view', 'tonnes', 'red_tonnes', 'white_tonnes', 'value_per_tonne', 'lon', 'lat', 'dlon', 'dlat', 'moved', 'label', 'llon', 'llat', 'lalign', 'c1lon', 'c1lat', 'c2lon', 'c2lat'];
const fmt = v => v === undefined ? '' : typeof v === 'number' ? +v.toFixed(5) : /[,"]/.test(v) ? `"${String(v).replace(/"/g, '""')}"` : v;
fs.writeFileSync('data/regions_bubbles_2026.csv', [cols.join(','), ...nodes.map(n => cols.map(c => fmt(n[c])).join(','))].join('\n') + '\n');
console.log(`wrote data/regions_bubbles_2026.csv: ${nodes.length} rows`);

// ---- write the matching projections into the spec ----
const specPath = 'specs/crush_bubble_map.json';
if (fs.existsSync(specPath)) {
  const spec = JSON.parse(fs.readFileSync(specPath, 'utf8'));
  const panels = spec.hconcat.flatMap(p => p.vconcat || [p]).filter(p => VIEWS[p.name]);   // WA panel sits in a vconcat with the size legend
  for (const panel of panels) {
    const v = VIEWS[panel.name];
    panel.width = v.W; panel.height = v.H;
    panel.projection = { type: 'conicEqualArea', parallels: v.parallels, rotate: v.rotate,
      scale: +v.proj.scale().toFixed(3), translate: v.proj.translate().map(t => +t.toFixed(3)), clipExtent: [[0, 0], [v.W, v.H]] };
  }
  fs.writeFileSync(specPath, JSON.stringify(spec, null, 2) + '\n');
  console.log('updated projections in', specPath);
}
