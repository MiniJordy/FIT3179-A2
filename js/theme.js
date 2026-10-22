// Shared chart styling. Colours come from the CSS variables in css/style.css (one palette for page + charts).
//
// Specs refer to this file in three ways:
//   "style": "bubble"          -> a named bundle of mark settings (STYLES below)
//   "range": "wine"            -> a named list of colours for a scale (RANGES below)
//   "var(--merlot)"            -> a single palette colour, swapped in by resolveVars() before drawing
//   "var(--col-width)"         -> a layout size from the CSS grid, swapped in as a number (pixels)

// Read a CSS variable, e.g. css('--merlot') -> '#5a1f36'
const css = name => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

// Read a CSS size variable as a number of pixels, e.g. px('--col-width') -> 464 (works for calc() too)
function px(name) {
  const probe = document.createElement('div');
  probe.style.cssText = `position:absolute; visibility:hidden; width:var(${name})`;
  document.body.appendChild(probe);
  const w = probe.getBoundingClientRect().width;
  probe.remove();
  return w;
}

const RANGES = {
  wine:  [css('--wine-red'), css('--wine-white'), css('--wine-rose'), css('--wine-other')],
  flows: [css('--flow-exported'), css('--flow-domestic'), css('--flow-leftover'),
          css('--wine-red'), css('--wine-white'), css('--wine-other'), css('--flow-unsold')],
  heat:  [css('--heat-1'), css('--heat-2'), css('--heat-3'), css('--heat-4'), css('--merlot'), css('--merlot-deep')],
  gst:   [css('--gst-1'), css('--gst-2'), css('--gst-3'), css('--gst-4'), css('--gst-5')],   // 5 temperature bands, cool to hot
  state: [css('--state-sa'), css('--state-vic'), css('--state-nsw'), css('--state-wa'), css('--state-qld'), css('--state-tas')],
  world: [css('--world-ne-asia'), css('--world-n-america'), css('--world-europe'), css('--world-se-asia'), css('--world-oceania')]
};

const STYLES = {
  // note: use 'color' (not 'fill') here - Vega-Lite's default colour would override a styled fill
  // bubble map
  'bubble':       {color: css('--merlot'), fillOpacity: 0.85, stroke: css('--paper'), strokeWidth: 1.2},
  'land':         {color: css('--land'), stroke: css('--border'), strokeWidth: 0.8},
  'region':       {color: css('--region-fill'), stroke: css('--region-edge'), strokeWidth: 0.6},
  'leader-line':  {color: css('--muted'), strokeWidth: 0.8},   // bubble -> its true location
  'callout-line': {color: css('--ink-3'), strokeWidth: 0.7},   // label -> bubble
  'bubble-label': {fontSize: 10.5, fontWeight: 600, color: css('--ink-2')},
  'label-halo':   {stroke: css('--paper'), strokeWidth: 3, strokeJoin: 'round', strokeOpacity: 0.9},   // white outline drawn under a label
  // flow map
  'route-label':  {fontSize: 11, fontWeight: 600, color: css('--ink-2')},
  // bump chart
  'end-label':    {fontSize: 13.5, fontWeight: 600, color: css('--ink-2')},
  // waffle
  'key-label':    {fontSize: 13, color: css('--ink-2')}
};

const WINE_THEME = {
  background: null,
  font: 'system-ui, -apple-system, "Segoe UI", sans-serif',
  view: {stroke: null},
  title: {anchor: 'start', fontSize: 13.5, fontWeight: 600, color: css('--ink'), subtitleFontSize: 11.5, subtitleColor: css('--ink-3'), offset: 14},
  axis: {labelColor: css('--ink-3'), titleColor: css('--ink-2'), gridColor: css('--grid'), domainColor: css('--axis'), tickColor: css('--axis')},
  legend: {labelColor: css('--ink-3'), titleColor: css('--ink-2')},
  range: RANGES,
  style: STYLES
};
const EMBED_OPTS = {actions: false, config: WINE_THEME};

// Replace every "var(--name)" string in a spec with that variable's value.
function resolveVars(node) {
  if (typeof node === 'string') {
    const m = node.match(/^var\((--[\w-]+)\)$/);
    if (!m) return node;
    const value = css(m[1]);
    return /px$|^calc/.test(value) ? px(m[1]) : value;   // sizes become numbers, colours stay strings
  }
  if (Array.isArray(node)) return node.map(resolveVars);
  if (node && typeof node === 'object') {
    return Object.fromEntries(Object.entries(node).map(([k, v]) => [k, resolveVars(v)]));
  }
  return node;
}

// Load a spec file, fill in the palette colours, and draw it.
function embedChart(el, url) {
  return fetch(url)
    .then(r => r.json())
    .then(spec => vegaEmbed(el, resolveVars(spec), EMBED_OPTS))
    .catch(console.error);
}
