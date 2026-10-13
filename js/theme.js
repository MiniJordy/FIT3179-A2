// Shared Vega-Lite config applied to every chart (keeps fonts, axes and colours consistent).
const WINE_THEME = {
  background: null,
  font: 'system-ui, -apple-system, "Segoe UI", sans-serif',
  view: {stroke: null},
  title: {anchor: 'start', fontSize: 16, fontWeight: 600, color: '#1f1f1e', subtitleFontSize: 12.5, subtitleColor: '#5a5a57', offset: 14},
  axis: {labelColor: '#5a5a57', titleColor: '#3a3a37', gridColor: '#f2c3ad', domainColor: '#c99e8b', tickColor: '#c99e8b'},
  legend: {labelColor: '#5a5a57', titleColor: '#3a3a37'}
};
const EMBED_OPTS = {actions: false, config: WINE_THEME};
