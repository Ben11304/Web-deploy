# PLAN.md — Kế hoạch, việc cần làm, vấn đề tồn đọng

Cập nhật: 2026-04-06

---

## Trạng thái hiện tại

**Version: v4-5Hazard — All thresholds literature-backed (winter PRELIMINARY)**

| Hazard | Data | Method | Threshold | Reference | Exposed |
|--------|------|--------|-----------|-----------|---------|
| **Earthquake** | USGS NSHM 2023 | Probabilistic PGA | PGA ≥ 0.092g (MMI ≥ VI) | Wald et al. (1999); Petersen et al. (2024) | **16.0%** |
| **Flood** | FEMA NFHL | Direct SFHA point-in-polygon | Binary (in SFHA) | 44 CFR § 59.1 | **4.3%** |
| **Wildfire** | USGS WFPI P95 | Raster sampling | P95 ≥ 75 | Burgan (1998); USGS WLFP | **36.9%** |
| **Hurricane** | NOAA IBTrACS | Wind swath point-in-polygon | ≥64 kt (Cat 1+) | NOAA/WMO (Knapp 2010) | **6.7%** |
| **Winter Storm** | NOAA SNODAS SWE P95 | Raster sampling | SWE P95 ≥ 100mm (PRELIMINARY) | Barrett (2003); ASCE 7-22 | **19.4%** |
| **Any hazard** | | | | | **TBD (v4 notebook)** |
| **Multi (≥2)** | | | | | **TBD (v4 notebook)** |

| Component | Status |
|-----------|--------|
| SVI × Exposure | ✅ OR=1.71, 52.6% high-SVI exposed |
| Network Vuln × Exposure | ✅ 66.6% high-V exposed (50 states) |
| Power Outage correlation | ✅ **Flood-outage ρ=0.456*** (p=0.001) — EQ, WFPI, Any, Multi all NS |
| Notebook v3 (3 hazards) | ✅ All cells execute |
| Notebook v4 (5 hazards) | ⏳ Needs update to integrate winter storm |
| Pareto states | HI, CA, UT, NM, MS, AZ (6 states, 38.3% coverage) — will change with 5 hazards |

**Regional dominance:**
- Northeast: **Earthquake** (15.5%)
- Midwest: **Wildfire WFPI** (9.5%)
- South: **Wildfire WFPI** (50.6%)
- West: **Wildfire WFPI** (58.8%)

---

## Việc cần làm

### 🔴 Ưu tiên cao — Blocking

- [x] ~~PSHA earthquake integrated~~ → Done 2026-04-03
- [x] ~~WFPI wildfire integrated~~ → Done 2026-04-01
- [x] ~~FEMA SFHA flood integrated~~ → Done 2026-04-04
- [x] ~~SVI re-run~~ → Done (OR=1.71)
- [x] ~~Network Vuln re-verify~~ → Done (66.6%)
- [x] ~~Notebook v3 all cells execute~~ → Done

- [x] ~~Update slide sang v3-PSHA-FEMA~~ → Done 2026-04-04
  - All numbers synced: EQ 16%, Flood 4.3%, WFPI 36.9%, Any 48.2%
  - Flood-outage significant finding (ρ=0.456***)
  - Vuln weights noted "author's choice"
  - Intro claims cited (USGCRP 2023, betweenness centrality note)

- [ ] **Re-run SVI analysis với FEMA flood**
  - Current SVI CSV dùng old flood definition (heatmap score ≥ 0.3)
  - OR=1.71 có thể thay đổi
  - Script: `rerun_svi_exposure.py` — cần update flood logic

### 🟡 Ưu tiên trung bình

- [x] ~~**Hurricane exposure**~~ → Done 2026-04-04
  - 50/50 states, 6.69% exposed (≥64 kt)
  - Output: `hurricane/output/` (1.3GB)
  - Literature: ✅✅✅ Strong (NOAA/WMO official thresholds)

- [x] ~~**Winter Storm exposure — SNODAS SWE P95**~~ → Done 2026-04-06
  - 50/50 states, **19.4% exposed** (SWE P95 ≥ 100mm, PRELIMINARY threshold)
  - Output: `winter_storm/winter_storm_final/output/` + `snodas_swe_p95.tif`
  - Top: NH 99.3%, ME 99.0%, MN 98.0%, ND 96.3%, CT 95.4%
  - AK/HI: No Data (CONUS only, same as WFPI)
  - Threshold ≥100mm PRELIMINARY — cần validate với ASCE 7-22 + sensitivity analysis
  - Storm Events v3 frequency data available as supplementary

- [ ] **Vulnerability weights sensitivity**
  - 0.40/0.30/0.30 — chưa verify claim "kết quả tương tự"

- [ ] **WFPI P95 threshold sensitivity analysis**
  - Issue: P95 có literature support (Yu 2023, Jolly 2015) nhưng cho fire weather, không phải infrastructure
  - Threshold ≥75 dựa trên USGS WLFP patterns nhưng không có direct prescription
  - Literature strength: EQ/Flood ✅✅✅ Strong | Wildfire ✅🟡 Moderate
  - **Action needed**: Sensitivity analysis — test P90/95/99 × thresholds 50/75/100
  - **Statement cho paper**: "P95 consistent with climate extremes methodology (Yu 2023), threshold based on USGS WLFP large fire probability patterns. Sensitivity in Supplementary."
  - Không vi phạm Rule nếu acknowledge + report sensitivity

### 🟢 Ưu tiên thấp

- [x] ~~Web dashboard bug fix~~ → Done 2026-04-06
  - Heatmap sector dropdown không hoạt động (hardcoded "combined" trong loadGeoJSONHeatmap)
  - Hazard dropdown cũng không sync value từ URL param
  - GitHub Pages deploy config sai path `/docs` → `/`

- [x] ~~**Web: Thêm tất cả exposure/hazard types mới**~~ → Done 2026-04-06
  - Exposure: +4 (earthquake PSHA, wildfire WFPI, hurricane, winter storm, flood FEMA)
  - Hazard: +2 (hurricane, winter storm)
  - Legacy flood phát hiện sai data (Ohio > Florida) → FEMA SFHA làm default
  - Thêm quantile/log color scale cho skewed data
  - `.nojekyll` fix GitHub Pages build stuck
  - 250 files mới uploaded R2 CDN

- [ ] Drought data
- [ ] Tower analysis riêng

---

## Vi phạm Research Integrity Rule

### Đã sửa ✅

1. ~~MMI cumulative sum ≠ real MMI~~ → USGS NSHM 2023 PSHA
2. ~~Wildfire 2.3% (burns only)~~ → WFPI P95 (36.9%)
3. ~~Flood arbitrary weights + threshold~~ → **FEMA SFHA direct (4.3%)**
4. ~~Pareto arbitrary weights~~ → Pareto frontier
5. ~~Slide numbers outdated~~ → Updated (cần update lần nữa cho FEMA flood)
6. ~~Network Vuln old data~~ → Re-verified 50 states
7. ~~"Cascading failures" claim~~ → Rephrased

### Đã sửa thêm ✅

8. ~~**Vulnerability weights**~~ → Slide thêm note "Author's choice; sensitivity analysis in supplementary"
9. ~~**Introduction claims**~~ → Added "USGCRP 2023" reference + "betweenness centrality as proxy" clarification
10. ~~**Flood slide old threshold**~~ → Slide flood section rewritten: FEMA SFHA, 44 CFR § 59.1, binary

### Cần attention trước khi viết method PDF 🟡

11. **Graph-based vulnerability — TẠM BỎ khỏi method PDF**
    - Luận điểm yếu: weights (0.40/0.30/0.30) author's choice, claim "ranking tương tự" chưa verify, node type weights (tower=0.1) không có literature basis, edge vulnerability formula chưa documented
    - **Quyết định**: Không include graph vulnerability trong method PDF. Giữ data nhưng không present như primary finding.
    - **Nếu cần sau này**: Chạy sensitivity analysis (3 weight sets + Spearman ρ), document edge formula, cite Newman (2005) cho betweenness methodology
    - Slide/paper nên focus vào 5 hazard exposure + SVI + outage correlation — đủ mạnh mà không cần vulnerability graph

12. **Yu et al. (2023) và Jolly et al. (2015) — cited based on abstract?**
    - Hai papers quan trọng nhất justify P95 methodology cho wildfire
    - REFERENCES.md claims: Yu (2023) "uses 95th percentile of fire danger indices"; Jolly (2015) "percentile-based fire weather severity"
    - **Cần verify**: Đã đọc full text hay chỉ abstract? Nếu chỉ abstract → ghi note trong method PDF
    - **Action**: Nếu có full text access → verify claims. Nếu không → dùng phrasing an toàn: "consistent with approaches in fire weather literature (Yu et al. 2023; Jolly et al. 2015)" thay vì claim cụ thể

13. **SVI OR discrepancy: METHODOLOGY.md ghi 1.40, CLAUDE.md ghi 1.71**
    - METHODOLOGY.md dòng 212: "OR = 1.40"
    - CLAUDE.md dòng 48: "OR=1.71 (p<0.001)"
    - Có thể từ v2 (3 hazards without FEMA flood) vs v3 (3 hazards with FEMA flood)
    - **Cần verify**: Kiểm tra notebook v3 output để xác nhận con số đúng
    - **Action**: Chạy hoặc đọc notebook output → update METHODOLOGY.md cho consistent

---

## Timeline

| Tuần | Việc | Output |
|------|------|--------|
| **Done** | ✅ v3-PSHA-FEMA complete | Notebook v3 + data final |
| **Done** | ✅ Hurricane exposure complete | 50/50 states, 6.7% exposed |
| **Done** | ✅ v4 notebook created | 4 hazards integrated |
| **Done** | ✅ Winter storm SNODAS complete | 50/50 states, 19.4% exposed |
| **Next** | v4 notebook: integrate 5 hazards | Comprehensive analysis with winter |
| **Next** | SVI re-run + threshold validation | Winter threshold + sensitivity |
| **Then** | Paper draft Methods/Results | Submission-ready |
