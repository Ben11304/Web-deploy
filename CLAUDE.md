# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Energy Infrastructure Risk Analysis — a system for analyzing and visualizing risk to US energy infrastructure. Combines OpenStreetMap energy asset data, natural hazard data (earthquake, flood, wildfire, drought), power outage history, social vulnerability indices, and network graph analysis into an interactive web dashboard.

## Running the Application

```bash
# Activate virtual environment
source .venv/bin/activate

# Run Flask dev server
cd app && python -m flask run
```

The app serves at `http://127.0.0.1:5000`. No `requirements.txt` exists; packages are installed directly in `.venv` (Flask, Shapely, NumPy, Pandas, NetworkX).

## Running Data Processing

Processing pipelines are Jupyter notebooks and standalone Python scripts. There is no unified build/test system.

```bash
# Vulnerability analysis for a state
python vulnerability/energy_vulnerability_analyzer.py --input <input.geojson> --output <output.geojson>

# Generate 5km grid heatmap
python vulnerability/generate_vulnerability_grid.py -v <vulnerability.geojson> -g <grid.geojson> -o <output.geojson>

# Batch processing via notebooks
jupyter notebook layout/earthquake/calculate_all_states_mmi.ipynb
jupyter notebook layout/flood/run_all.ipynb
jupyter notebook vulnerability/run_all_vulnerability.ipynb
```

## Architecture

### Flask Web App (`app/`)

Single-file Flask app (`app.py`) with two routes:
- `/` — Dashboard homepage with state/sector/hazard selection
- `/map` — Interactive Leaflet.js map with multiple view types: heatmap, hazard, impact, energy_vulnerability, exposure, energy_detail, social_vulnerability

The backend dynamically discovers available states and sectors from the filesystem (`static/geojson/states/`). Sector list comes from `vulnerability/cisa_osm_mapping.json` (16 CISA critical infrastructure sectors). Configuration is passed to Jinja2 templates which drive the frontend.

### Frontend (`app/static/js/`)

Vanilla JavaScript (no framework) with Leaflet.js 1.9.4:
- `lod-systems.js` — Level of Detail system for efficient rendering of 50k+ assets, controls feature visibility by zoom/score
- `map-controls.js` — View switching, layer management, legends, popups
- `map-utils.js` — GeoJSON loading, color palettes, URL parameter handling

HTML templates use a loader+panel partial pattern per view type (e.g., `map_hazard_loader.html` + `map_hazard_panel.html`).

### Exposure Calculation Pipeline

#### Earthquake Exposure (`layout/earthquake/calculate_asset_mmi.py`)

Tính Modified Mercalli Intensity (MMI) cho từng energy asset dựa trên khoảng cách đến tâm chấn:

- **Input**: Earthquake MMI zones tại 6 khoảng cách buffer: 5, 10, 25, 50, 100, 200 km (`us_earthquakes_mmi_d{N}km.geojson`)
- **Point assets**: Lấy max MMI từ tất cả zones chứa điểm đó
- **Line/Polygon assets**: Weighted average = `sum(overlap_percentage × MMI)` cho mỗi earthquake, chỉ dùng zone gần nhất để tránh double-counting
- **Output**: `Exposure/earthquake_simplified/{state}_mmi_results.json` với `weighted_mmi` (0-10), `calculation_method`, `contributing_earthquakes[]`
- **Threshold**: MMI ≥ 5 được coi là exposed

Data optimization: `simplify_earthquake_data.py` giữ lại chỉ `earthquake_id` + `mmi_contribution` (giảm ~95% size). `compress_earthquakes.py` giữ chỉ 1 earthquake/asset cho ultra-compression.

Batch processing: `calculate_all_states_mmi.ipynb`

#### Flood Exposure (`layout/flood/run_all.ipynb`)

Tính flood exposure bằng spatial intersection với FEMA flood zones:

- **Input**: Flood heatmap grids 5km (`heatmap_flood_lite/{state}/flood_heatmap_5.0km.geojson`) + Energy assets
- **Method**: Spatial intersection asset ↔ flood grid cells, aggregation scores
- **FEMA Zones**: A, AE, AH, AO, VE (high velocity)
- **Output**: `Exposure/flood/{state}_flood_results.json` với `flood_score` normalized [0, 1]
- **Threshold**: score ≥ 0.3 được coi là exposed

#### Wildfire Exposure (`calculate_wildfire_exposure.py`)

Tính wildfire exposure dựa trên overlap với historical burn polygons có weighting:

- **Input**: Burn polygons (`Hazard/wildfire/{state}.geojson`) + Energy assets (`states/{state}/Energy_Sector.geojson`)
- **Overlap calculation**:
  - Points: 1.0 nếu inside fire polygon, 0.0 otherwise
  - Lines: `length_inside / total_length`
  - Polygons: `area_inside / total_area`
- **Weighting** (per fire):
  - Area weight: `BurnBndAc / max_fire_acres_in_state`
  - Recency weight: exponential decay `exp(-ln(2)/20 × years_ago)` — half-life 20 năm, reference date 2026-02-27
- **Final score**: `raw = sum(overlap × area_weight × recency_weight)`, sau đó normalize / max
- **Output**: `Exposure/wildfire/{state}_wildfire_results.json` với `wildfire_exposure_raw`, `wildfire_exposure_normalized`, `contributing_fires[]`
- **Spatial indexing**: Shapely STRtree cho hiệu suất

#### Cross-Hazard Analysis (`layout/analyse/`)

- `energy_exposure_analysis.ipynb` — Merge earthquake + flood + wildfire results, tính multi-hazard exposure, tạo summary statistics
- `summary_statistics.ipynb` — Aggregate statistics across all 50 states
- Output: `output/research_parameters.csv`, `output/vulnerability_exposure_cross_analysis.csv`, `output/svi_exposure_cross_analysis.csv`

### Vulnerability Analysis (`vulnerability/`, `vulnerability_new/`, `vulnerability_new_development_embeded/`)

Energy network modeled as graph G=(V,E): nodes = energy assets (plants, substations, generators, towers), edges = transmission lines/cables snapped to nodes within buffer radius via R-tree spatial index.

**Vulnerability formula**: `score = 0.40×betweenness_centrality + 0.30×weighted_degree + 0.30×node_weight`

Ba iterations khác nhau:

| Version | Buffer Radius | Node Weight | Special |
|---------|--------------|-------------|---------|
| `vulnerability/` (original) | 0.001° (~111m) | voltage_kV × power_MW | Baseline |
| `vulnerability_new/` | 0.0002° (~22m) | power_MW only | + Node type weights (tower=0.1, plant/substation=1.0) |
| `vulnerability_new_development_embeded/` | 0.0002° (~22m) | power_MW (min 1W) | No type weights, GDP-weighted |

**Criticality classification**: HIGH (top 10%), MEDIUM (10-50%), LOW (bottom 50%)

**Grid heatmap** (`generate_vulnerability_grid.py`): Aggregate vulnerability scores vào 5km grid cells, combined_score = `0.6×avg_node_vuln + 0.4×avg_edge_vuln`, P95 log normalization. Output: `heatmap_vulnerability/{state}_heatmap.geojson`

### Social Vulnerability Index (SVI) Integration

#### Data Source (`social_vulnerability_index/`)

CDC/ATSDR SVI 2022 county-level data — 3,144 counties, 158 columns. Source: `Dataset/SVI_2022_US_county.csv`.

**SVI Metrics** (percentile ranking 0-1):
- `RPL_THEMES`: Overall social vulnerability (composite)
- `RPL_THEME1`: Socioeconomic Status
- `RPL_THEME2`: Household Characteristics & Disability
- `RPL_THEME3`: Racial & Ethnic Minority Status
- `RPL_THEME4`: Housing Type & Transportation

#### Build SVI GeoJSON (`_build_svi_geojson.py`)

Join SVI county data với county boundary polygons:

- **Input**: `SVI_2022_US_county.csv` + `US_county_border_by_state_new/*.geojson` (3,235 files)
- **Matching**: Multi-stage — exact (county_clean, state_clean) → state without spaces → Virginia independent cities → partial substring
- **Name normalization**: lowercase, remove suffixes (county, parish, borough...), strip non-alphanumeric
- **Output**: `app/static/geojson/social_vulnerability/svi_us_county.geojson` (~1.7GB, coordinates rounded to 4 decimals)
- **Validation**: `_check_svi.py` — kiểm tra data shape, RPL_THEMES range, state/county counts

#### SVI × Exposure Cross-Analysis (`layout/analyse/`)

- Spatial join energy assets → counties → SVI scores
- Phân tích: high-SVI (≥0.6) vs low-SVI (<0.6) counties
- Kết quả: 50.3% hazard-exposed assets nằm trong high-SVI counties, high-SVI areas có 68.4% exposure rate vs 60.8% low-SVI
- Output: `output/svi_exposure_cross_analysis.csv`

#### SVI Web View (`map_social_vulnerability_*`)

- Color scale: green (0.0, low vulnerability) → red (1.0, high vulnerability), 10-step gradient
- Opacity: 0.3–0.8 theo score
- 4 vulnerability levels: Very High (0.75-1.0), High (0.50-0.75), Moderate (0.25-0.50), Low (0.00-0.25)
- UI: metric selector, level filter checkboxes, threshold slider, population stats
- Popup: county name, FIPS, all 5 SVI themes, population

### Data Storage

All processed GeoJSON lives under `app/static/geojson/`:
- `states/{state_name}/` — Per-state sector GeoJSON + energy vulnerability + heatmaps
- `Exposure/` — flood, earthquake_simplified, wildfire exposure by state
- `Hazard/` — Earthquake zones, wildfire burns, flood heatmaps
- `impact/` — Power outage data (2022, 2024)
- `social_vulnerability/` — SVI county-level GeoJSON

Geographic boundaries are in `Geo/` (state and county borders) and `US_county_border_by_state_new/` (3235 county files).

## Static Site Deployment (GitHub Pages + Cloudflare R2)

### Tổng quan

Flask app ban đầu cần Python server chạy backend. Tuy nhiên app không có logic server-side thực sự (chỉ serve static files + render Jinja2 templates). Do đó, toàn bộ app được chuyển sang **100% static site** để deploy miễn phí trên GitHub Pages, với data lớn (46GB GeoJSON) được host trên Cloudflare R2 CDN.

### Kiến trúc triển khai

```
┌─────────────────────────┐     ┌──────────────────────────────┐
│   GitHub Pages (Free)   │     │   Cloudflare R2 CDN (Free)   │
│                         │     │                              │
│  index.html             │────>│  us-states.geojson           │
│  map_heatmap.html       │     │  states/ohio/Energy_Sector   │
│  map_exposure.html      │     │  Exposure/flood/ohio_flood   │
│  map_hazard.html        │     │  Hazard/wildfire/California  │
│  map_impact.html        │     │  heatmap_flood_lite/...      │
│  map_energy_detail.html │     │  impact/poweroutage_2022     │
│  map_energy_vuln.html   │     │  social_vulnerability/...    │
│  map_social_vuln.html   │     │                              │
│  static/js/css/images   │     │  2,276 files, 1.7GB gzipped  │
│                         │     │  (23GB original)             │
│  ~54MB total            │     │                              │
└─────────────────────────┘     └──────────────────────────────┘
         │                                    │
         └──── Browser tải HTML/JS ──────────>┘
               rồi fetch GeoJSON từ R2
```

### Quy trình build (Flask → Static)

**Script chính:** `build_static.py`

1. **Discover data**: Scan `app/static/geojson/states/` để lấy danh sách 50 states, đọc `cisa_osm_mapping.json` lấy 16 sectors
2. **Render templates**: Dùng Jinja2 engine (cùng engine với Flask) render `app/templates/` thành HTML tĩnh
3. **Tạo 1 file HTML per view type**: `map_heatmap.html`, `map_exposure.html`, ... (7 files) — mỗi file chứa đúng panel + loader cho view đó
4. **Post-process** (`fix_paths()`):
   - Thay `/static/geojson/` → `window.DATA_BASE_URL` (trỏ đến R2)
   - Thay `../static/` → `./static/` (relative paths)
   - Thay Jinja2 server-side loops (rỗng vì build với `selected_regions=[]`) bằng JS runtime loops dùng `MAP_CONFIG.selectedRegions.forEach(...)`
   - Inject `ALL_STATES` array để `mode=entire` hoạt động
   - Inject URL param override script SAU `MAP_CONFIG` definition
5. **Copy assets**: JS, CSS, images, CI icons → `docs/static/`
6. **Bundle small data**: impact (19MB), SVI (12MB), boundaries (23MB) → `docs/data/`
7. **Output**: `docs/` directory (~54MB) sẵn sàng deploy

```bash
python build_static.py
# Output: docs/ (27 files, 54MB)
```

### Quy trình nén & upload data lên R2

**Bước 1: Gzip compress** (`deploy_r2.py --prepare`)

GeoJSON là text → nén rất hiệu quả:

| Thư mục | Original | Gzipped | Giảm |
|---------|----------|---------|------|
| Exposure/earthquake_simplified | 11.6 GB | ~580 MB | 95% |
| states/ (50 states × 16 sectors) | 7.6 GB | ~380 MB | 95% |
| Exposure/flood | 1.6 GB | ~80 MB | 95% |
| Hazard/wildfire | 1.4 GB | ~70 MB | 95% |
| Exposure/wildfire | 863 MB | ~43 MB | 95% |
| heatmap_wildfire_lite | 451 MB | ~23 MB | 95% |
| heatmap_flood_lite | 258 MB | ~13 MB | 95% |
| **Tổng** | **~23 GB** | **~1.7 GB** | **93%** |

```bash
python deploy_r2.py --prepare
# Output: .r2_upload/ (2,276 files, 1.7GB)
```

**Bước 2: Upload song song** (`deploy_r2_parallel.py`)

Dùng boto3 (S3 API) upload 8 files đồng thời. Tự skip files đã upload.

```bash
python deploy_r2_parallel.py --workers 8
# Hỏi: Account ID, Access Key, Secret Key (từ R2 API Token)
# Thời gian: ~2 phút cho 1.7GB
```

### Cloudflare R2 Setup

**Bucket**: `energy-risk-data`
**Public URL**: `https://pub-2d678d396f414cb681a74d123b7e90b4.r2.dev`

**CORS** (bắt buộc để browser fetch được từ GitHub Pages domain):
```json
{
  "rules": [{
    "allowed": {
      "origins": ["*"],
      "methods": ["GET", "HEAD"],
      "headers": ["*"]
    },
    "maxAgeSeconds": 86400
  }]
}
```

Set CORS qua wrangler:
```bash
wrangler r2 bucket cors set energy-risk-data --file cors-rules.json --force
```

**R2 Free Tier**: 10GB storage, 10M reads/tháng — dư sức cho project này.

### GitHub Pages Setup

**Repo**: `https://github.com/Ben11304/Web-deploy`
**Settings → Pages → Source**: Deploy from branch → `main` → `/docs`
**Live URL**: `https://ben11304.github.io/Web-deploy/`

### Cách hoạt động runtime (trong browser)

1. User mở `index.html` → chọn states + view type → submit form
2. Form gửi đến `map_{view_type}.html?region=ohio&exposure_type=flood`
3. `map_exposure.html` load:
   - `site-config.js` → set `window.DATA_BASE_URL = "https://pub-xxx.r2.dev"`
   - `MAP_CONFIG` được Jinja2 bake với defaults
   - **URL override script** đọc `?region=ohio` → ghi đè `MAP_CONFIG.selectedRegions = ["ohio"]`
   - `mode=entire` → ghi đè `MAP_CONFIG.selectedRegions = ALL_STATES` (50 states)
4. Fetch `DATA_BASE_URL + '/us-states.geojson'` → vẽ boundary
5. Loader chạy `MAP_CONFIG.selectedRegions.forEach(...)` → fetch data per state từ R2
6. Render Leaflet.js map với LOD system

### Các vấn đề đã giải quyết trong quá trình build

| Vấn đề | Nguyên nhân | Giải pháp |
|--------|-------------|-----------|
| CSS render ra ngoài `<style>` | Regex-based template processing lỗi | Dùng Jinja2 engine trực tiếp |
| Tất cả view dẫn đến heatmap | Form action cố định `map_heatmap.html` | JS `updateFormAction()` theo view type |
| Data không load | `/static/geojson/` paths hardcoded | `fix_paths()` thay bằng `DATA_BASE_URL` |
| MAP_CONFIG override không hoạt động | Override script chạy TRƯỚC `MAP_CONFIG` define | Di chuyển override SAU MAP_CONFIG block |
| Browser chặn fetch từ R2 | Không có CORS headers | Set CORS policy trên R2 bucket |
| Heatmap/Hazard loading vĩnh viễn | Jinja2 `{% for region %}` render rỗng | Thay bằng `MAP_CONFIG.selectedRegions.forEach()` |
| `mode=entire` không load gì | `selectedRegions` rỗng | Inject `ALL_STATES` array, gán khi `mode=entire` |
| wrangler upload vào local simulator | Thiếu `--remote` flag | Thêm `--remote` vào deploy script |

### Files liên quan

| File | Mục đích |
|------|----------|
| `build_static.py` | Build script: Jinja2 → static HTML + post-process |
| `deploy_r2.py` | Gzip compress data (`--prepare`) + upload tuần tự |
| `deploy_r2_parallel.py` | Upload song song qua S3 API (boto3) |
| `docs/` | Output directory — **KHÔNG edit tay**, luôn generate từ build script |
| `docs/static/js/site-config.js` | `DATA_BASE_URL` config — thay đổi khi đổi CDN |
| `.r2_upload/` | Thư mục tạm chứa data đã gzip (gitignored) |
| `.github/workflows/deploy-pages.yml` | GitHub Actions auto-deploy (optional) |

### Rebuild & redeploy

```bash
# 1. Rebuild static site
python build_static.py

# 2. Push docs/ lên Web-deploy repo
# (copy docs/ sang temp dir, git push --force)

# 3. Nếu data thay đổi:
python deploy_r2.py --prepare          # Gzip lại
python deploy_r2_parallel.py           # Upload (auto-skip unchanged)
```

## Performance Optimizations

### Flask App (local dev)
- **Gzip compression**: `flask-compress` nén responses ~90% (208MB → ~20MB qua mạng)
- **Cache-Control headers**: GeoJSON 7 ngày, JS/CSS 1 ngày, images 7 ngày

### Static Site (production)
- **R2 CDN**: Data serve từ Cloudflare edge servers, tự động gzip decompress
- **Zoom-based LOD**: Exposure & Energy Detail views tự điều chỉnh số features theo zoom level
  - Zoom 14+ (street): 100% features
  - Zoom 10-11: 30-45%
  - Zoom 6-7: 4-7%
  - Zoom <6 (continent): 2% — chỉ top assets
  - Toggle on/off: checkbox "Auto LOD (zoom-based)"
- **LOD slider**: Manual cap, hoạt động cùng zoom LOD (effective% = min(slider%, zoom%))
- **Per-view pages**: Mỗi view type 1 HTML file riêng → chỉ load JS/data cần thiết

### Lưu ý hiệu năng
- `mode=entire` cho Exposure/Energy Detail load 50 states (~1-2GB) → rất chậm. Nên chọn 1-5 states cụ thể.
- Impact và Social Vulnerability load toàn US nhẹ (county-level, ~10MB mỗi file).

## Key Conventions

- GeoJSON is the universal data interchange format
- State names are used as directory keys (e.g., `California/`, `Texas/`)
- The PROJECT_OVERVIEW.md is written in Vietnamese
- Root-level Python scripts (`_build_svi_geojson.py`, `calculate_wildfire_exposure.py`, etc.) are standalone utilities, not part of the Flask app
- No test suite exists
