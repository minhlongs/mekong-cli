# Phase 01: Thiết kế Lõi Modular & Central Facade

## 1. Mục tiêu
Xây dựng 4 micro-engines độc lập trong thư mục `src/core/maritime/` và một central facade `src/core/maritime_aton_vnsw_imsbc_hm_engine.py`:
- `phase_331_iala_aton_telemetry.py` (< 200 LOC)
- `phase_332_vnsw_fal_clearance.py` (< 200 LOC)
- `phase_333_imsbc_group_b_safety.py` (< 200 LOC)
- `phase_334_hm_damage_survey.py` (< 200 LOC)
- Central facade `maritime_aton_vnsw_imsbc_hm_engine.py` (< 200 LOC)

## 2. Checklist Thực hiện
- [ ] Xây dựng `src/core/maritime/phase_331_iala_aton_telemetry.py`
- [ ] Xây dựng `src/core/maritime/phase_332_vnsw_fal_clearance.py`
- [ ] Xây dựng `src/core/maritime/phase_333_imsbc_group_b_safety.py`
- [ ] Xây dựng `src/core/maritime/phase_334_hm_damage_survey.py`
- [ ] Cập nhật re-export trong `src/core/maritime/__init__.py`
- [ ] Xây dựng facade `src/core/maritime_aton_vnsw_imsbc_hm_engine.py`
