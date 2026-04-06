# METHODOLOGY.md — Algorithms & Design Decisions

Tài liệu này mô tả các thuật toán và phương pháp **không có luận điểm trực tiếp từ bài báo** — những design decisions dựa trên engineering judgment, computational constraints, hoặc đặc thù của dữ liệu.

Các phương pháp **có** literature support → xem [REFERENCES.md](REFERENCES.md).

---

## 1. Earthquake: USGS NSHM 2023 Probabilistic Seismic Hazard

### Lịch sử approaches (đã bỏ)

Dự án trải qua 3 iterations trước khi đến approach hiện tại:

1. **Cumulative MMI sum (v1)**: Cộng MMI từ mọi EQ × mọi buffer distance → giá trị hàng nghìn, vô nghĩa vật lý. **Bỏ.**
2. **Max single-event summed (v2)**: Sum 6 distances per EQ → vẫn inflate. **Bỏ.**
3. **True felt MMI (v3 early)**: Closest buffer per EQ → đúng thang MMI nhưng source data chỉ có M2-4 → max 6.53, gần như không có exposure. **Bỏ.**

### Approach hiện tại: USGS NSHM 2023

Thay thế hoàn toàn bằng probabilistic seismic hazard — USGS 2023 National Seismic Hazard Model.

- **Data**: PGA contour polygons tại 10% probability of exceedance in 50 years
- **Method**: Point-in-polygon → lấy PGA midpoint của contour zone → convert to MMI
- **Coverage**: 50 states (bao gồm Alaska + Hawaii — fix limitation lớn nhất của old data)
- **Captures**: Toàn bộ seismic sources kể cả rare M7+ events (Cascadia, New Madrid, San Andreas)

### Tại sao 10% in 50 years (không phải 2%)?

- **10% in 50 years** (~475-year return period): standard "design-level" ground motion trong ASCE 7, IBC, FEMA HAZUS. Đây là mức mà structures thông thường được design để chịu.
- **2% in 50 years** (~2,475-year return period): "maximum considered" — quá conservative cho exposure assessment, dùng cho critical facilities (nuclear, dams).
- 10% level cho kết quả phân biệt tốt giữa states (PGA range 0.008g—0.62g) thay vì gần như everywhere exposed (2% level).

### PGA → MMI conversion

Dùng Wald et al. (1999) two-segment regression — **đây có direct literature support**:
- MMI = 3.66·log₁₀(PGA_cm/s²) − 1.66 (for PGA ≥ 0.039g)
- MMI = 2.20·log₁₀(PGA_cm/s²) + 1.00 (for PGA < 0.039g)

### Implementation

Script: `layout/earthquake/calculate_psha_exposure.py`
- Load shapefile via geopandas
- STRtree spatial index cho ~4,071 contour polygons
- Point-in-polygon → PGA midpoint → Wald et al. → MMI
- Output: `pga_10pct50yr`, `mmi_from_pga` per asset
- **50 states trong 25 phút** (~2,000-5,000 assets/sec)

### Legacy data (giữ tham khảo)

- `Exposure/earthquake_simplified/`: Historical + true felt MMI — superseded
- `layout/earthquake/recalculate_true_mmi.py`: True felt MMI script — superseded
- `layout/earthquake/regenerate_missing_states.py`: Fixed 7 corrupt states — superseded

---

## 2. Flood: FEMA NFHL Direct SFHA Classification

### Web visualization: Zone-based color gradient (NOT used in analysis)

Trên web map, FEMA flood zones được gán numeric scores **chỉ cho mục đích visualization** (color gradient). Scores KHÔNG được dùng trong bất kỳ phép tính exposure, statistical analysis, hay paper findings nào.

Thứ tự zone tuân theo FEMA flood zone hierarchy:
- V/VE zones (coastal velocity) nguy hiểm hơn A/AE zones — FEMA official distinction
- SFHA zones (1% annual chance) nguy hiểm hơn X zones (0.2% annual chance) — 44 CFR § 59.1
- Numeric values (VE=1.0, AE=0.7, X=0.2, etc.) là **design decision cho visualization**, không có literature prescribing specific values.

**Exposure classification vẫn là binary**: asset in SFHA = exposed, outside = not exposed. Kết quả 4.3% nationally exposed không bị ảnh hưởng bởi visualization scores.

### Lịch sử (đã bỏ)

Approach cũ dùng 5km heatmap grid với arbitrary zone weights (AE=0.90, A=0.85, X=0.30) và threshold=0.3. Phát hiện vi phạm Rule #2 — weights và threshold không có literature basis. **Bỏ hoàn toàn.**

### Approach hiện tại: Direct point-in-polygon

1. Download FEMA NFHL flood zone polygons (4.4M polygons, 44GB GPKG)
2. Extract `S_Fld_Haz_Ar` layer per state → GeoJSON
3. Spatial join: mỗi energy asset → STRtree → point-in-polygon → `FLD_ZONE`
4. Classify: SFHA zone → Exposed. Non-SFHA → Not exposed.

### Tại sao SFHA binary (không dùng continuous score)

- **SFHA** = Special Flood Hazard Area = 1% annual chance flood. Đây là **legal standard** (44 CFR § 59.1), không phải research choice.
- Binary classification (in/out SFHA) loại bỏ hoàn toàn arbitrary threshold.
- Flood insurance, building code, infrastructure planning đều dùng SFHA binary.

### Kết quả

- Old (heatmap score ≥ 0.3): 19.5% exposed — **inflated** vì grid cell có BẤT KỲ flood zone coverage
- New (FEMA SFHA direct): **4.3%** exposed (excl. towers), **7.4%** (all assets)
- Top: Louisiana 28.6%, Florida 24.1%, Mississippi 19.0%
- Bottom: Idaho 0.5%, Montana 1.1%

### Implementation

Script: `flood_fema/calculate_flood_exposure.py`
- Data: Kaggle `viethuyduong/usflood` (FEMA NFHL, GPKG)
- Extraction: `flood_fema/process_kaggle_gpkg.py` per state
- STRtree spatial index cho flood zone polygons
- Processed trên HPC server (32GB RAM, 10-27 min/state)
- Output: `flood_fema/output/{state}_flood_results.json` (50 states, 792MB)

---

## 3. Wildfire WFPI: P95 Raster Sampling

### Approach

Thay vì overlap với historical burn polygons (chỉ capture nơi ĐÃ cháy), dùng satellite-derived fire potential index.

### Pipeline design decisions

1. **P95 thay vì mean/median**: Mean WFPI phản ánh average conditions (hầu hết ngày không có fire weather). P95 captures near-worst-case → relevant hơn cho risk assessment. P99 quá extreme, sensitive to individual outlier days.

2. **Daily rasters 2008–2025**: ~6,300 observations/pixel → P95 statistically robust (>300 obs tối thiểu). Start 2008 vì WFPI product bắt đầu năm đó.

3. **Chunked processing (100 rows)**: RAM constraint ~4GB. Full stack (6300 files × 2889 rows × 4587 cols × 4 bytes) = ~316GB. Chunk = 6300 × 100 × 4587 × 4 = ~11GB per chunk → fit in memory sau khi bỏ NaN.

4. **Point sampling (không buffer)**: Energy assets là Points (hoặc centroid cho Lines). 1km resolution WFPI → 1 pixel per asset. Buffer sampling (e.g., 5km radius average) có thể smooth ra nhưng tăng complexity mà ít thêm accuracy.

### Tại sao WFPI thay vì FWI (Fire Weather Index)?

- WFPI tích hợp **vegetation condition** (NDVI) + weather. FWI chỉ dùng weather.
- WFPI có sẵn dạng gridded product từ USGS, daily, 1km. FWI cần tính lại từ weather station data.
- NREL đã dùng WFPI cho energy infrastructure context (Panossian & Elgindy, 2023).

---

## 4. Winter Storm: SNODAS SWE P95 Raster Sampling

### Lịch sử approaches (đã bỏ)

1. **NOAA Storm Events v1**: County-level footprints, fabricated magnitude = threshold khi thiếu data. County coverage không đều (Washington 1/39 counties, Idaho 1/44). **Bỏ.**
2. **NOAA Storm Events v2**: Fixed fabrication (magnitude = None khi thiếu), added NWS zone matching. Kết quả: 0% measured intensity across ALL states — Storm Events Database fundamentally thiếu magnitude cho winter events. 23/51 track files corrupted do server issue. **Bỏ.**

**v3 (final Storm Events)**: 50/50 states valid, NWS zone + county matching, 0% measured intensity confirmed. Provides frequency-only data (event counts, annual frequency). Useful as **supplementary analysis** nhưng không dùng cho primary exposure.

Cả ba versions bị thay thế cho primary exposure vì **data source limitation** (not methodology violation): NOAA Storm Events Database ghi nhận event occurrence nhưng hầu như không report intensity measurements cho winter events (0% across all 50 states in v3).

### Approach hiện tại: SNODAS SWE P95

Thay thế hoàn toàn bằng NOAA SNODAS gridded SWE — tương đương WFPI P95 pipeline cho wildfire.

- **Data**: SNODAS daily SWE grids, 1km, 2003-2025 (product 1034)
- **Method**: P95 of annual max SWE per pixel → point-raster sampling
- **Coverage**: CONUS only (no Alaska, Hawaii — same as WFPI)

### Pipeline design decisions

1. **SWE thay vì snow depth**: SWE đo water mass = structural load thực tế. Cùng depth wet snow vs dry snow → weight khác nhiều lần. ASCE 7-22 dùng water-equivalent (psf). IEEE 1048-2013 dùng equivalent ice radial thickness.

2. **P95 of annual max (không phải mean hay P95 of all days)**: Mean SWE quá thấp (hầu hết ngày = 0). P95 of all daily values dominated bởi zero days. Annual max per water year → P95 across years = near-worst-case seasonal loading. Consistent với WFPI P95 methodology.

3. **Water year Oct-Apr (không phải calendar year)**: Snow season spans Oct–Apr. Calendar year splitting mất context (Dec snow → Jan melt là cùng season).

4. **Minimum 5 years valid data per pixel**: P95 từ <5 observations không đủ reliable. Pixels thiếu data → NaN.

5. **Saturation filter ≥5000mm → NaN**: Raw data max = 32767 (int16 signed max) = artifact. Realistic max CONUS SWE ~3000mm (extreme mountains). 5000mm generous bound để không loại data hợp lệ.

6. **Threshold ≥100mm (PRELIMINARY)**: Dựa trên ASCE 7-22: 100mm SWE ≈ 20 psf ground snow load — onset of meaningful structural loading. Results: **19.4% nationally exposed**. Top: NH 99.3%, ME 99.0%, MN 98.0%. Bottom: TX/FL/LA 0%. Cần sensitivity analysis ở 50/75/100/150/250mm trước khi finalize.

### Tại sao SNODAS thay vì ERA5-Land hay ASCE 7-22 shapefile?

- **ERA5-Land** (9km, 1950-present): Longer record nhưng coarser (9km vs 1km). SNODAS 1km matches WFPI pipeline resolution.
- **ASCE 7-22 Ground Snow Load**: Copyrighted by ASCE, no free shapefile download. API requires authentication, not suitable for 2.8M point queries.
- **SNODAS**: Free (US Government), 1km, NOAA-authoritative, daily → P95 computable, SWE = direct load metric.

---

## 5. Vulnerability: Graph-Based Network Analysis

### Graph construction

- **Nodes**: Energy assets (plants, substations, generators, towers)
- **Edges**: Transmission lines/cables — snapped to nearest node within buffer radius
- **Buffer**: 0.0002° (~22m) — spatial tolerance cho snapping

### Formula: `score = 0.40×BC + 0.30×WD + 0.30×NW`

| Component | Weight | Rationale |
|-----------|--------|-----------|
| Betweenness Centrality (BC) | 0.40 | Đo "bottleneck" — node mà nhiều shortest paths đi qua. Disruption ở đây cascade rộng nhất. |
| Weighted Degree (WD) | 0.30 | Số connections × capacity. Node với nhiều lines high-voltage quan trọng hơn. |
| Node Weight (NW) | 0.30 | Intrinsic importance: power_MW. Plant/substation inherently quan trọng hơn tower. |

**Tại sao 0.40/0.30/0.30**: BC là metric mạnh nhất cho cascade risk trong power networks (literature support). WD và NW bổ sung thêm local importance. Tổng weights = 1.0. Đã test 0.33/0.33/0.33 và 0.50/0.25/0.25 — kết quả ranking tương tự nhưng 0.40 BC cho discriminative power tốt hơn.

### Criticality classification: top 10% / 10-50% / bottom 50%

- **HIGH (top 10%)**: Aggressive threshold — chỉ assets thực sự critical
- **MEDIUM (10-50%)**: Bulk of "important" assets
- **LOW (bottom 50%)**: Majority — towers, minor generators

Không có standard classification trong literature. 10% threshold commonly used trong infrastructure resilience studies.

---

## 5. Towers: Excluded from Core Analysis

### Lý do

- Towers = **92.7%** of all energy assets (2,621,808 / 2,827,591)
- Towers distributed khắp nơi → exposure rate ≈ national average
- Bao gồm towers khiến mọi asset-type analysis bị dominated bởi tower statistics
- Khi loại towers: generators (62%), fuel stations (21%), lines (17%) — differences giữa types trở nên visible

### Substations nổi bật

Sau khi loại towers, substations có EQ exposure **50.9%** (gấp 3× loại khác) vì concentrate ở seismically active zones (California, South Carolina).

---

## 6. SVI × Exposure: Statistical Methods

### Tại sao Mann-Whitney thay vì t-test

- SVI scores KHÔNG normal distribution (uniform-like vì đã percentile-ranked)
- Mann-Whitney U là non-parametric, không assume normality
- Với n = 100,000 (sampled from 2.7M), power rất cao

### Odds Ratio interpretation

- OR = 1.71 → assets trong high-SVI counties có 71% higher odds of being hazard-exposed
- 95% CI: 1.70–1.71 → very tight (do sample size lớn)
- Effect size nhỏ (Cohen's d ~0.2) nhưng statistically significant
- Interpretation: association exists, moderate in magnitude
- *Note: OR=1.40 trong v3_executed.ipynb là từ flood method cũ (heatmap ≥0.3). OR=1.71 là từ FEMA SFHA binary (hiện tại).*

### Logistic Regression: `is_exposed ~ SVI_themes + region`

- Region là strongest predictor (Northeast OR=4.68) → geography drives exposure more than social vulnerability
- SVI theme 1 (socioeconomic) là SVI component quan trọng nhất (OR=1.94)
- Model accuracy 66.5% → better than random (50%) nhưng not highly predictive
- Interpretation: exposure is primarily geographically determined, with SVI as secondary modulating factor

---

## 7. Pareto Frontier for Priority States

### Tại sao Pareto thay vì weighted scoring

- Weighted scoring (0.30/0.25/0.25/0.20) → kết quả thay đổi hoàn toàn khi đổi weights
- Pareto optimality: state X dominated bởi state Y khi Y ≥ X trên TẤT CẢ criteria VÀ Y > X trên ít nhất 1
- Transparent, reproducible, không cần arbitrary weights

### Criteria: Any-Hazard %, Multi-Hazard %, Mean SVI

3 dimensions capture:
1. **Breadth** (any hazard %): bao nhiêu assets exposed
2. **Depth** (multi-hazard %): overlap severity
3. **Social impact** (SVI): community vulnerability

---

## 8. Power Outage: Mixed Finding (Flood Significant, Others NS)

### Spearman correlation (not Pearson)

- Outage data highly skewed (few states dominate)
- Spearman rank-based → robust to outliers
- **Finding**: Flood exposure significantly correlates, others do not

### Kết quả (v3-PSHA-FEMA)

| Hazard | Spearman ρ | p-value | Significant? |
|--------|-----------|---------|-------------|
| **Flood (FEMA SFHA)** | **+0.456** | **0.001** | **Yes (***)** |
| EQ (PSHA) | +0.269 | 0.059 | No (borderline) |
| Multi-hazard | +0.240 | 0.094 | No |
| Any-hazard | +0.107 | 0.461 | No |
| Wildfire (WFPI) | -0.151 | 0.296 | No |

**Finding thay đổi so với v2**: Trước đó (heatmap flood) tất cả correlations negative/insignificant. Với FEMA SFHA direct, **flood exposure significantly correlates với outage frequency** (ρ=0.456, p=0.001).

### Interpretation: Tại sao chỉ Flood có correlation?

**Flood exposure predicts outages vì:**
1. **Direct causality**: Flooding directly damages substations, underground cables → immediate outages
2. **Persistent vulnerability**: Assets trong SFHA nằm ở floodplains → repeatedly flooded mỗi khi có heavy rain
3. **Geographic clustering**: SFHA assets concentrated ở coastal/riverine areas → cùng trải qua storm surge/river flooding

**EQ và WFPI không predict outages vì:**
1. **Earthquake**: Exposure (PGA ≥ 0.092g) = potential hazard, nhưng actual shaking events rare (10% in 50 years = low annual probability). Outage data (2022) chỉ capture 1 year → không có major EQ events trong window.
2. **Wildfire**: Exposure = high fire potential (WFPI P95), nhưng mediating factors dominate:
   - Vegetation management (power line clearance) reduces ignition risk
   - Proactive shutoffs (PSPS) prevent fire-caused outages
   - Grid modernization (undergrounding) in high-risk areas
3. **Mediating infrastructure factors**: Grid age, redundancy, maintenance quality vary independently of hazard exposure

**Implication**: Exposure ≠ realized impact. Flood là exception vì direct, recurring causality. EQ/wildfire impacts mediated bởi preparedness, design standards, operational practices.
