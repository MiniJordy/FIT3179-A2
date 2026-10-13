# Australian Wine: Climate, Regions and Trade

FIT3179 Data Visualisation 2 — Jordan Russo, October 2026.

A single-page data visualisation following Australian wine from the vineyard to the glass. All charts and maps are built with [Vega-Lite](https://vega.github.io/vega-lite/).

## What's in this repository
| Folder | Contents |
|---|---|
| `index.html` | The web page |
| `specs/` | One Vega-Lite JSON specification per chart or map |
| `data/` | Processed data files loaded by the charts |
| `css/`, `js/` | Page styling and the shared chart theme |
| `scripts/` | Python/Node scripts that turned the original downloads into the files in `data/` |

## Data sources
- Wine Australia, *National Vintage Report 2026* (regional appendix) — https://www.wineaustralia.com/market-insights/national-vintage-report
- Wine Australia, *Production, Sales and Inventory Report 2024–25* — https://www.wineaustralia.com/market-insights/australian-wine-production-sales-and-inventory
- Wine Australia, *Australian Wine Export Monitor* FY2026 and *Export Report* (June 2026) — https://www.wineaustralia.com/market-insights/australian-wine-exports
- Wine Australia, *Wine Geographical Indications Australia* (region boundaries) — https://wineaustralia-opendata-wineaustralia.hub.arcgis.com/datasets/2dd4c385f0ed4d109c2e18ae99e819e2
- UN Comtrade, Australia's exports of HS 2204 (wine of fresh grapes) by partner, 2014–2025 — https://comtradeplus.un.org/
- Reserve Bank of Australia, Statistical Table F11 Exchange Rates (AUD/USD) — https://www.rba.gov.au/statistics/historical-data.html
- World map: `world-110m.json` from [vega-datasets](https://github.com/vega/vega-datasets) (Natural Earth)

The original downloaded reports are not included in this repository; they are available from the links above.
