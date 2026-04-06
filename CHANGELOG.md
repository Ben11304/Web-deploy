# CHANGELOG.md — Nhật ký thay đổi

---

## 2026-04-06

### Bug fix: Heatmap sector dropdown không hoạt động trên static site

**Vấn đề**: Khi user chọn sector khác trong dropdown (ví dụ Government Facilities), trang reload nhưng vẫn hiển thị data "Combined". Dropdown cũng không hiện đúng sector đang chọn.

**Nguyên nhân (2 bugs)**:
1. `loadGeoJSONHeatmap()` hardcode `var heatmapSectorLocal = "combined"` thay vì đọc từ `MAP_CONFIG.heatmapSector` — dù URL param thay đổi đúng, data luôn load combined
2. `initHeatmapControls()` không sync dropdown value từ URL param — dropdown luôn hiển thị "Combined" dù page đang load sector khác

**Fix**:
- `docs/map_heatmap.html`: `heatmapSectorLocal = MAP_CONFIG.heatmapSector || "combined"`
- `docs/static/js/map-controls.js` + `app/static/js/map-controls.js`: Thêm `heatmapSelect.value = MAP_CONFIG.heatmapSector` và `hazardSelect.value = MAP_CONFIG.hazardType` trước event listener

**Phụ**: Cũng fix GitHub Pages deploy config — source path sai `/docs` thay vì `/` (do subtree push tạo flat structure)

---

## 2026-04-05 (update 3)

### SNODAS SWE P95 — COMPLETE (50/50 states)
- `winter_storm/winter_storm_final/`: SNODAS pipeline run on server, all SLURM jobs completed
- **National: 19.4% exposed** (SWE P95 ≥ 100mm, PRELIMINARY threshold)
- 50/50 states valid JSON, `snodas_swe_p95.tif` (6MB)
- Top: NH 99.3%, ME 99.0%, MN 98.0%, ND 96.3%, CT 95.4%
- Bottom: TX 0%, FL 0%, LA 0%, MS 0%, SC 0%
- AK/HI: No Data (CONUS only)
- Spot-check results plausible: heavy snow belt states high, southern states zero
- Threshold ≥100mm PRELIMINARY — needs sensitivity analysis + ASCE 7-22 cross-reference

### Winter Storm v3 (Storm Events) validated + SNODAS pipeline ready

**Storm Events v3 completed on server**: 50/50 states, all JSON valid, NWS zone + county matching working. Confirms 0% measured intensity across ALL states — database limitation, not bug. v3 provides frequency-only data (event counts, annual frequency) as supplementary analysis.

### Winter Storm primary pipeline redesigned — SNODAS SWE P95

**Problem identified**: NOAA Storm Events Database (v1/v2/v3) fundamentally unsuitable for primary exposure:
- v1: ~0% measured intensity, fabricated magnitude = threshold, county-level only, 3 states missing
- v2: Fixed fabrication but still 0% measured data (database limitation), 23/51 files corrupted

**Root cause**: NOAA Storm Events Database records event occurrence but almost never reports intensity measurements for winter events. This is a **data source limitation**, not a methodology violation.

**New approach**: NOAA SNODAS (Snow Data Assimilation System)
- 1km gridded daily SWE (Snow Water Equivalent), 2003-2025
- P95 of annual max SWE per pixel → point-raster sampling (same paradigm as WFPI P95)
- NOAA-authoritative, free, DOI: 10.7265/N5TB14TC
- Pipeline: `winter_storm/snodas_pipeline/` (download_snodas.py, compute_swe_p95.py, calculate_winter_exposure.py)

**SWE unit verified on server** (test download 2024-01-15):
- Header: `Data units: Meters / 1000.000000` → raw int16 = millimeters
- Spot-checks: CO Rockies 133mm, Sierra Nevada 252mm, Minnesota 6mm, Miami 0mm ✓
- Saturation artifact: Max=32767 (int16 max) → filtered ≥5000mm as NaN

**Threshold**: PRELIMINARY — data first, threshold later. ASCE 7-22 cross-reference for classification.

### v4 comprehensive analysis notebook created
- `layout/analyse/comprehensive_analysis_v4.ipynb` — integrates 4 hazards (EQ, Flood, WFPI, Hurricane)
- Based on v3, adds hurricane data loading, exposure flags, sensitivity analysis, visualizations
- `layout/analyse/build_v4.py` — script to generate v4 from v3

### Mass documentation update — all .md files
- CLAUDE.md: Winter Storm section rewritten (SNODAS replaces Storm Events)
- DATA_SOURCES.md: Added Section 8 (SNODAS), updated Exposure Output Files
- REFERENCES.md: Added Section 5 (Winter Storm, refs 26-30)
- METHODOLOGY.md: Added Section 4 (Winter Storm design decisions, legacy history)
- PLAN.md: Winter Storm updated, timeline refreshed
- CHANGELOG.md: This entry

---

## 2026-04-05 (update 2)

### Mass documentation update — v3 clarification
- **Mục đích**: Cập nhật toàn bộ .md files với version v3-PSHA-FEMA
- **Thay đổi**:
  - README.md: Thêm comprehensive introduction với coverage, results, quick start
  - PROJECT_OVERVIEW.md: Update hazard descriptions, add Hurricane + Winter Storm, Research Integrity Rule, threshold justification table
  - CLAUDE.md: Update Project Overview với 4 hazards (EQ, Flood, WFPI, Hurricane), add Hurricane + Winter Storm pipeline sections
- **Clarification về v3**:
  - comprehensive_analysis_v3.ipynb covers **3 hazards** (Earthquake, Flood, Wildfire WFPI)
  - Historical burns là comparison data, KHÔNG phải hazard thứ 4
  - Hurricane data đã chạy xong (6.7% exposed) nhưng chưa integrate vào comprehensive analysis
  - Khi integrate hurricane → sẽ là v4
- **Coverage summary confirmed**:
  - Earthquake PSHA: **50/50 states** (including AK + HI)
  - Flood FEMA: **50/50 states**
  - Wildfire WFPI: **50/50 states** (CONUS only, AK/HI = No Data)
  - Hurricane IBTrACS: **50/50 states**
  - Winter Storm: Pipeline ready, not yet run

## 2026-04-05 (update 1)

### Documentation fixes — Flood-outage finding
- **Phát hiện**: PLAN.md nói "Power Outage negative finding (all p > 0.05)" nhưng notebook v3 thực tế có **Flood-outage ρ=0.456, p=0.001 (significant!)**
- Updated PLAN.md: "Power Outage correlation | ✅ Flood-outage ρ=0.456*** (p=0.001) — EQ, WFPI, Any, Multi all NS"
- Updated METHODOLOGY.md: Changed section 8 title từ "Negative Finding" → "Mixed Finding (Flood Significant, Others NS)"
- Added detailed interpretation: tại sao chỉ Flood có correlation (direct causality, recurring flooding) nhưng EQ/WFPI không (mediating factors)
- **Không ảnh hưởng kết quả**: Numbers đúng 100%, chỉ documentation inconsistency

### Winter Storm pipeline created
- Tạo `winter_storm/` folder: download NOAA Storm Events → exposure calculation
- Thresholds: Ice ≥0.25", Snow ≥6"/12h, Blizzard ≥35mph (NWS Warning criteria)
- Literature: ✅✅✅ Strong (NWS 10-512, IEEE 2013, ASCE 7-22, Changnon 2003)
- Scripts ready: `download_storm_data.py`, `process_storm_tracks.py`, `calculate_winter_exposure.py`
- Sẽ là hazard thứ 5 (sau Earthquake, Flood, Wildfire, Hurricane)

### Hurricane REFERENCES.md integration
- Added Hurricane section (refs 17-21) với DOIs:
  - Knapp 2010 (IBTrACS data)
  - NOAA/NWS Saffir-Simpson scale
  - WMO tropical cyclone definitions
  - Holland 1980 (parametric wind model)
  - FEMA HAZUS hurricane fragility

## 2026-04-04

### Hurricane exposure — HOÀN THÀNH
- 50/50 states, output: `hurricane/output/` (1.3GB)
- National: 6.69% exposed (≥64 kt hurricane-force wind)
- Top: Florida 68.5%, Connecticut 56.7%, Louisiana 47.0%
- Thresholds: ≥34 kt (TS), ≥64 kt (Cat 1, primary), ≥96 kt (Cat 3+)
- All thresholds = NOAA/WMO official definitions (✅✅✅ Strong)

## 2026-04-03 (tiếp)

### Slide updated to v3-PSHA-FEMA — ALL violations fixed
- Tất cả numbers synced: EQ 16.0%, Flood 4.3% (SFHA), WFPI 36.9%, Any 48.2%
- Pareto: HI, CA, UT, NM, MS, AZ (6 states, 38.3%)
- New finding: Flood-outage ρ=0.456 (p=0.001) — significant! (trước đó negative)
- Vuln weights: thêm "Author's choice" note
- Intro claims: thêm USGCRP 2023 reference
- Research Integrity Rule: **KHÔNG CÒN VI PHẠM NÀO**

### Flood FEMA NFHL — HOÀN THÀNH
- Phát hiện: old flood pipeline dùng arbitrary zone weights (AE=0.90, A=0.85, X=0.30) — vi phạm Rule #2
- Tạo `flood_fema/` folder, chạy trên HPC server (Kaggle GPKG 44GB, 4.4M polygons)
- Direct point-in-polygon SFHA classification → 50/50 states, 792MB output
- **Tích hợp vào notebook v3**: Flood 22.1% (old heatmap) → **4.3%** (FEMA SFHA)
- Any hazard: 59.5% → **48.2%**, Multi: 14.3% → **8.7%**
- Reference: 44 CFR § 59.1 — NO arbitrary weights/thresholds

### Hurricane pipeline created
- Tạo `hurricane/` folder: download IBTrACS/HURDAT2 → wind field reconstruction → asset exposure
- Classification: Saffir-Simpson (NOAA official) + ASCE 7 basic wind speed
- Status: scripts ready, chờ chạy trên server

### USGS NSHM 2023 — Earthquake hoàn toàn mới
- Download `US_PGA_10Pct50Yrs_BC_poly.shp` (56MB) từ USGS ScienceBase
- Script `layout/earthquake/calculate_psha_exposure.py`: point-in-polygon PGA sampling + Wald et al. PGA→MMI conversion
- **50/50 states** trong 25 phút, output: `Exposure/earthquake_psha/{state}_psha_results.json`
- Threshold: PGA ≥ 0.092g (MMI ≥ VI, "strong shaking, light damage begins")
- Key results: Alaska 94% MMI≥VI, California 93.5%, Oregon 49.5%, Hawaii 100%
- Supersedes toàn bộ old earthquake data (historical MMI, cumulative sum, true felt MMI)
- CLAUDE.md, REFERENCES.md, METHODOLOGY.md, PLAN.md đều cập nhật
- Notebook v3 đang update để dùng PSHA

### PLAN.md created
- Kế hoạch, việc cần làm, vi phạm tồn đọng, timeline

## 2026-04-03

### Slide updated to v3 data
- Tất cả số liệu trong `slide/main.tex` chuyển từ v2 sang v3
- Key changes: 36.3% → 61.8% any-hazard, wildfire 2.3% → 36.9% (WFPI), Pareto 3 → 6 states
- Compile OK, 17 pages

### Documentation restructure
- Tạo `docs/REFERENCES.md` — 16 citations với DOIs, threshold justifications
- Tạo `docs/METHODOLOGY.md` — 8 design decisions, rationale
- Tạo `docs/DATA_SOURCES.md` — 9 data sources, download instructions
- Tạo `docs/CHANGELOG.md` — file này
- `CLAUDE.md` thêm Research Integrity Rule (6 quy tắc) + navigation table trỏ đến docs/

### Earthquake: True felt MMI recalculation
- Phát hiện `mmi_contribution` trong simplified data = **sum across 6 buffer distances** per earthquake, KHÔNG phải true MMI
- Script `layout/earthquake/recalculate_true_mmi.py`: recalculate toàn bộ 50 states, dùng closest buffer → true felt MMI (thang I-XII)
- Kết quả: max felt MMI toàn US = 6.53 (Texas). Hầu hết assets 1.5–2.5. Threshold ≥ 5 chỉ 1,368 assets (0.05%)
- **Vấn đề chưa giải quyết**: source earthquake data chỉ chứa M2-4 events. True felt MMI quá thấp để dùng threshold ≥ 4 hoặc ≥ 5 hiệu quả. Cần quyết định: dùng threshold thấp hơn (≥ 3), acknowledge limitation, hoặc đổi sang USGS PSHA
- Notebook v3 hiện vẫn dùng old summed metric (chưa switch sang true felt MMI) — pending decision

## 2026-04-01

### WFPI wildfire integration
- Tạo `wildfire_wfpi/calculate_wfpi_exposure.py` — sample WFPI P95 raster tại mỗi energy asset
- 50 states, 81 giây, output: `Exposure/wildfire_wfpi/{state}_wfpi_results.json`
- Kết quả: 36.8% assets exposed (WFPI P95 ≥ 75), vs 2.9% historical burns
- Top: New Mexico 95.4%, Wyoming 85.5%, Utah 74.6%
- WFPI P95 raster: `wfpi_p95_conus.tif` (7.3MB, 2889×4587, CONUS only)
- Citations: Burgan 1998, USGS WFPI/WLFP, Yu 2023, Jolly 2015, NREL 2023

### Earthquake: 7 states regenerated
- 6 states corrupt JSON (Idaho, Nevada, New Mexico, Oklahoma, Utah, Wyoming) — file generation crash, chỉ có 1 entry
- Washington: simplified file truncated at line 12.5M — full data (722MB) parseable
- Script `layout/earthquake/regenerate_missing_states.py` — STRtree optimized, ~700-1000 assets/sec
- Washington: re-simplified from full data
- 6 states: recalculated from scratch
- Kết quả: Nevada 62.3%, Oklahoma 49.5%, Utah 52.7%, Washington 44.8% above MMI 5 (summed metric)

### Notebook v3 created
- `layout/analyse/comprehensive_analysis_v3.ipynb`
- 4 hazard layers: EQ + Flood + WFPI + historical burns (comparison)
- Tất cả cells chạy thành công
- Key results: 61.8% any-hazard, 18.1% multi-hazard, 6 Pareto states

### Notebook v2 issues found
- MMI cumulative vs max-single: cumulative inflate giá trị lên hàng nghìn
- Towers 92.7% mask asset-type differences
- 7 states corrupt earthquake data
- Wildfire historical burns quá thấp (2.3%)

## 2026-03-31

### Comprehensive analysis v1 & v2
- `comprehensive_analysis.ipynb` (v1): first full integration of EQ + Flood across 50 states
- `comprehensive_analysis_v2.ipynb`: added max-single MMI, excluded towers, inferential stats, sensitivity analysis, Pareto frontier
- Phát hiện: v1 con số 73.9% dùng cumulative MMI (sai), v2 corrected to 36.3%

### Data audit
- Earthquake: 43/50 parseable (7 corrupt + 2 no coverage)
- Flood: 50/50 OK
- Wildfire burns: 46/50 (missing CT, NH, RI, VT)
- Alaska/Hawaii: earthquake source data không cover (lat 28-49°N only)

### Prior work (pre-Claude session)
- Flask web app với 7 view types
- Earthquake exposure pipeline (`calculate_asset_mmi.py`)
- Flood exposure pipeline (`layout/flood/run_all.ipynb`)
- Historical wildfire exposure (`calculate_wildfire_exposure.py`)
- Vulnerability network analysis (3 versions)
- SVI integration (`_build_svi_geojson.py`)
- Static site deployment (GitHub Pages + Cloudflare R2)
