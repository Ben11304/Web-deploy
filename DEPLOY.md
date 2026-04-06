# DEPLOY.md — Hướng dẫn deploy static site

Cập nhật: 2026-04-06

---

## Tổng quan

Flask app ban đầu cần Python server chạy backend. Tuy nhiên app không có logic server-side thực sự (chỉ serve static files + render Jinja2 templates). Do đó, toàn bộ app được chuyển sang **100% static site** để deploy miễn phí trên GitHub Pages, với data lớn (46GB GeoJSON) được host trên Cloudflare R2 CDN.

## Kiến trúc triển khai

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

## Repo & URL

| Item | Value |
|------|-------|
| **Source repo** | `https://github.com/ruoxinx/energy-infrastructure-risk` (branch `main`) |
| **Deploy repo** | `https://github.com/Ben11304/Web-deploy` (branch `main`) |
| **Git remote** | `deploy` → `Ben11304/Web-deploy.git` |
| **GitHub Pages source** | Branch `main`, path `/` (root, NOT `/docs`) |
| **Live URL** | `https://ben11304.github.io/Web-deploy/` |
| **R2 CDN** | `https://pub-2d678d396f414cb681a74d123b7e90b4.r2.dev` |
| **R2 Bucket** | `energy-risk-data` |

**QUAN TRỌNG**: GitHub Pages source path là `/` (root), không phải `/docs`. Do `git subtree split --prefix=docs` tạo flat structure (files nằm ở root của deploy repo).

---

## Quy trình build (Flask -> Static)

**Script chính:** `build_static.py`

1. **Discover data**: Scan `app/static/geojson/states/` để lấy danh sách 50 states, đọc `cisa_osm_mapping.json` lấy 16 sectors
2. **Render templates**: Dùng Jinja2 engine render `app/templates/` thành HTML tĩnh
3. **Tạo 1 file HTML per view type**: `map_heatmap.html`, `map_exposure.html`, ... (7 files)
4. **Post-process** (`fix_paths()`):
   - Thay `/static/geojson/` -> `window.DATA_BASE_URL` (trỏ đến R2)
   - Thay `../static/` -> `./static/` (relative paths)
   - Thay Jinja2 server-side loops bằng JS runtime loops dùng `MAP_CONFIG.selectedRegions.forEach(...)`
   - Inject `ALL_STATES` array để `mode=entire` hoạt động
   - Inject URL param override script SAU `MAP_CONFIG` definition
5. **Copy assets**: JS, CSS, images, CI icons -> `docs/static/`
6. **Bundle small data**: impact (19MB), SVI (12MB), boundaries (23MB) -> `docs/data/`
7. **Output**: `docs/` directory (~54MB) sẵn sàng deploy

```bash
python build_static.py
# Output: docs/ (27 files, 54MB)
```

**LƯU Ý**: `build_static.py` chỉ generate HTML files. Nếu sửa JS/CSS trực tiếp trong `docs/static/js/`, thay đổi sẽ bị ghi đè khi rebuild. Luôn sửa source trong `app/static/js/` rồi rebuild, HOẶC sửa cả hai nơi.

---

## Quy trình deploy lên GitHub Pages

### Cách 1: Subtree push (khuyến nghị)

```bash
# Từ repo energy-infrastructure-risk:

# 1. Commit thay đổi trong docs/ (cần -f vì docs/ nằm trong .gitignore)
git add -f docs/path/to/changed/file
git commit -m "Description of change"

# 2. Split docs/ thành branch tạm
git subtree split --prefix=docs -b deploy-temp

# 3. Force push lên deploy repo
git push deploy deploy-temp:main --force

# 4. Cleanup
git branch -D deploy-temp
```

### Cách 2: Push origin rồi subtree (nếu muốn lưu commit history)

```bash
git push origin main
git subtree split --prefix=docs -b deploy-temp
git push deploy deploy-temp:main --force
git branch -D deploy-temp
```

### Sau khi push

- GitHub Pages tự build trong 1-2 phút
- Kiểm tra status: `gh api repos/Ben11304/Web-deploy/pages --jq '{status}'`
- Nếu status `errored`: kiểm tra Pages source path phải là `/` (root)
- Trigger rebuild thủ công: `gh api repos/Ben11304/Web-deploy/pages/builds -X POST`

---

## Quy trình nén & upload data lên R2

**Bước 1: Gzip compress** (`deploy_r2.py --prepare`)

```bash
python deploy_r2.py --prepare
# Output: .r2_upload/ (2,276 files, 1.7GB)
```

**Bước 2: Upload song song** (`deploy_r2_parallel.py`)

```bash
python deploy_r2_parallel.py --workers 8
# Hỏi: Account ID, Access Key, Secret Key (từ R2 API Token)
# Thời gian: ~2 phút cho 1.7GB, auto-skip unchanged files
```

---

## Cloudflare R2 Setup

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

```bash
wrangler r2 bucket cors set energy-risk-data --file cors-rules.json --force
```

**R2 Free Tier**: 10GB storage, 10M reads/tháng.

---

## Cách hoạt động runtime (trong browser)

1. User mở `index.html` -> chọn states + view type -> submit form
2. Form gửi đến `map_{view_type}.html?region=ohio&exposure_type=flood`
3. Page load:
   - `site-config.js` -> set `window.DATA_BASE_URL = "https://pub-xxx.r2.dev"`
   - `MAP_CONFIG` được Jinja2 bake với defaults
   - **URL override script** đọc `?region=ohio` -> ghi đè `MAP_CONFIG.selectedRegions`
   - `mode=entire` -> ghi đè `MAP_CONFIG.selectedRegions = ALL_STATES`
4. Fetch `DATA_BASE_URL + '/us-states.geojson'` -> vẽ boundary
5. Loader chạy `MAP_CONFIG.selectedRegions.forEach(...)` -> fetch data per state từ R2
6. Render Leaflet.js map với LOD system

### URL Parameters quan trọng

| Parameter | Dùng cho | Ví dụ |
|-----------|----------|-------|
| `region` | State(s) cần hiện | `region=alabama&region=ohio` |
| `mode` | `select` hoặc `entire` | `mode=entire` (load 50 states) |
| `heatmap_sector` | Sector cho heatmap view | `heatmap_sector=Energy_Sector` |
| `hazard_type` | Loại hazard | `hazard_type=flood` |
| `impact_type` | Loại impact data | `impact_type=poweroutage_2022` |
| `exposure_type` | Loại exposure | `exposure_type=flood` |
| `exposure_asset` | Asset types (multi) | `exposure_asset=plant&exposure_asset=substation` |
| `svi_metric` | SVI metric | `svi_metric=RPL_THEMES` |
| `show_background` | Background map | `show_background=true` |
| `use_geotiff` | GeoTIFF mode | `use_geotiff=true` |

---

## Bugs đã fix

| Ngày | Bug | Nguyên nhân | Fix |
|------|-----|-------------|-----|
| 2026-04-06 | Heatmap sector dropdown không đổi data | `loadGeoJSONHeatmap()` hardcode `heatmapSectorLocal = "combined"` | Đổi thành `MAP_CONFIG.heatmapSector \|\| "combined"` |
| 2026-04-06 | Dropdown không hiện đúng sector đang chọn | `initHeatmapControls()` không sync value từ URL param | Thêm `heatmapSelect.value = MAP_CONFIG.heatmapSector` |
| 2026-04-06 | Hazard dropdown không sync | Tương tự heatmap | Thêm `hazardSelect.value = MAP_CONFIG.hazardType` |
| 2026-04-06 | GitHub Pages deploy lỗi | Pages source path `/docs` sai (subtree tạo flat structure) | Đổi sang `/` (root) |
| 2026-04-06 | GitHub Pages build stuck | Thiếu `.nojekyll` — Jekyll processing static HTML | Thêm `.nojekyll` file |
| 2026-04-06 | Flood exposure data sai (Ohio > Florida) | Legacy flood dùng heatmap grid + arbitrary weights | Thêm FEMA SFHA direct làm default |
| 2026-04-06 | Exposure map khó nhìn (hầu hết asset cùng màu) | Linear color scale + skewed data | Thêm quantile/log color scale modes |
| Trước đó | CSS render ngoài `<style>` | Regex-based template processing | Dùng Jinja2 engine trực tiếp |
| Trước đó | Tất cả view dẫn đến heatmap | Form action cố định | JS `updateFormAction()` theo view type |
| Trước đó | Data không load | `/static/geojson/` paths hardcoded | `fix_paths()` thay bằng `DATA_BASE_URL` |
| Trước đó | MAP_CONFIG override không hoạt động | Override script chạy TRƯỚC define | Di chuyển override SAU MAP_CONFIG block |
| Trước đó | Browser chặn fetch từ R2 | Không có CORS headers | Set CORS policy trên R2 bucket |
| Trước đó | Heatmap/Hazard loading vĩnh viễn | Jinja2 `{% for region %}` render rỗng | Thay bằng `MAP_CONFIG.selectedRegions.forEach()` |
| Trước đó | `mode=entire` không load gì | `selectedRegions` rỗng | Inject `ALL_STATES` array |

---

## Lưu ý quan trọng khi sửa code

1. **Sửa JS/CSS**: Luôn sửa source (`app/static/js/`) VÀ output (`docs/static/js/`). Hoặc sửa source rồi `python build_static.py`.
2. **Sửa HTML trực tiếp trong `docs/`**: OK cho hotfix, nhưng sẽ bị ghi đè khi rebuild. Nên sửa template source trong `app/templates/` cho permanent fix.
3. **`docs/` nằm trong `.gitignore`**: Cần `git add -f docs/...` để stage.
4. **Subtree push luôn force**: History của deploy repo khác với source repo, nên phải `--force`.
5. **Browser cache**: Sau deploy, luôn hard refresh (`Cmd+Shift+R`) hoặc dùng incognito để test.
6. **GitHub Pages build time**: 1-2 phút. Check status: `gh api repos/Ben11304/Web-deploy/pages/builds --jq '.[0].status'`

---

## Files liên quan

| File | Mục đích |
|------|----------|
| `build_static.py` | Build script: Jinja2 -> static HTML + post-process |
| `deploy_r2.py` | Gzip compress data (`--prepare`) + upload tuần tự |
| `deploy_r2_parallel.py` | Upload song song qua S3 API (boto3) |
| `docs/` | Output directory — **KHÔNG edit tay** (trừ hotfix), luôn generate từ build script |
| `docs/static/js/site-config.js` | `DATA_BASE_URL` config — thay đổi khi đổi CDN |
| `.r2_upload/` | Thư mục tạm chứa data đã gzip (gitignored) |
| `.github/workflows/deploy-pages.yml` | GitHub Actions auto-deploy (optional) |

---

## Quick reference: Full rebuild & redeploy

```bash
# 1. Rebuild static site
python build_static.py

# 2. Push docs/ lên Web-deploy repo
git add -f docs/
git commit -m "Rebuild static site"
git subtree split --prefix=docs -b deploy-temp
git push deploy deploy-temp:main --force
git branch -D deploy-temp

# 3. Push source lên origin
git push origin main

# 4. Nếu data thay đổi:
python deploy_r2.py --prepare          # Gzip lại
python deploy_r2_parallel.py           # Upload (auto-skip unchanged)
```
