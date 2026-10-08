"""Maritime SAR, Aids to Navigation, Tiered Oil Spill & Dredging Engine.

Vietnamese Maritime Code 2015, IAMSAR Manual, IALA Buoyage System,
Decision 12/2021/QĐ-TTg, Decree 159/2018/NĐ-CP & Decree 08/2022/NĐ-CP.

Pure Python standard library implementation - Zero external dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
from typing import Dict, List, Optional, Tuple


# ==============================================================================
# PHASE 247: MARITIME SEARCH AND RESCUE (SAR) & IAMSAR ENGINE
# ==============================================================================

class SarDistressPhase(str, Enum):
    """IAMSAR Emergency Distress Phases."""
    UNCERTAINTY = "uncertainty"  # INCERFA - Giai đoạn nghi ngờ
    ALERT = "alert"              # ALERFA - Giai đoạn báo động
    DISTRESS = "distress"        # DETRESFA - Giai đoạn nguy cấp


class SarSearchPattern(str, Enum):
    """IAMSAR Standard Visual Search Patterns."""
    EXPANDING_SQUARE = "expanding_square"  # SS - Vết quét hình vuông mở rộng
    SECTOR_SEARCH = "sector_search"        # VS - Vết quét hình nan quạt/khu vực
    PARALLEL_TRACK = "parallel_track"      # PS - Vết quét đường song song
    CREEPING_LINE = "creeping_line"        # CS - Vết quét đường lượn chữ chi


class SearchObjectType(str, Enum):
    """Search Target Types for Sweep Width Determination."""
    PERSON_IN_WATER = "person_in_water"    # PIW - Người dưới nước
    LIFE_RAFT_4_6 = "life_raft_4_6"        # Bè cứu sinh 4-6 người
    LIFE_RAFT_15_25 = "life_raft_15_25"    # Bè cứu sinh 15-25 người
    SMALL_CRAFT_UNDER_9M = "craft_under_9m"  # Phương tiện thủy < 9m
    VESSEL_10_20M = "vessel_10_20m"        # Tàu thuyền 10-20m
    VESSEL_OVER_20M = "vessel_over_20m"    # Tàu thuyền > 20m


@dataclass(frozen=True)
class SarOperationPlan:
    """Maritime SAR Operation Plan & Search Area Allocation."""
    incident_id: str
    phase: SarDistressPhase
    target_type: SearchObjectType
    datum_lat: float
    datum_lon: float
    search_radius_nm: float
    search_area_sq_nm: float
    recommended_pattern: SarSearchPattern
    track_spacing_nm: float
    sweep_width_nm: float
    coverage_factor: float
    probability_of_detection_pct: float
    required_search_hours: float
    operational_summary: str


class MaritimeSarEngine:
    """IAMSAR Search and Rescue Planning Engine compliant with Vietnam SAR regulations."""

    # Baseline Sweep Width (NM) under 10 NM visibility (IAMSAR Table)
    SWEEP_WIDTH_TABLE: Dict[SearchObjectType, float] = {
        SearchObjectType.PERSON_IN_WATER: 0.4,
        SearchObjectType.LIFE_RAFT_4_6: 1.8,
        SearchObjectType.LIFE_RAFT_15_25: 2.7,
        SearchObjectType.SMALL_CRAFT_UNDER_9M: 3.2,
        SearchObjectType.VESSEL_10_20M: 5.5,
        SearchObjectType.VESSEL_OVER_20M: 8.2,
    }

    @classmethod
    def evaluate_distress_phase(
        cls,
        communications_lost_minutes: int,
        unreported_delay_minutes: int,
        mayday_received: bool = False,
        epirb_active: bool = False,
        grave_imminent_danger: bool = False,
    ) -> Tuple[SarDistressPhase, str]:
        """Classify IAMSAR Distress Phase based on situational evidence."""
        if mayday_received or epirb_active or grave_imminent_danger:
            return (
                SarDistressPhase.DISTRESS,
                "DETRESFA: Tín hiệu Mayday/EPIRB hoặc nguy cơ chìm đắm/cháy nổ cận kề đe dọa sinh mạng.",
            )
        if communications_lost_minutes >= 60 or unreported_delay_minutes >= 60:
            return (
                SarDistressPhase.ALERT,
                "ALERFA: Mất liên lạc hoặc quá hạn đến cảng trên 60 phút, khả năng vận hành bị suy giảm.",
            )
        if communications_lost_minutes >= 15 or unreported_delay_minutes >= 30:
            return (
                SarDistressPhase.UNCERTAINTY,
                "INCERFA: Nghi ngờ về an toàn phương tiện, chậm trễ báo cáo thông tin hải trình.",
            )
        return (
            SarDistressPhase.UNCERTAINTY,
            "Giai đoạn theo dõi thông tin ban đầu, chưa đủ căn cứ kích hoạt ALERFA.",
        )

    @classmethod
    def calculate_search_parameters(
        cls,
        incident_id: str,
        phase: SarDistressPhase,
        target_type: SearchObjectType,
        datum_lat: float,
        datum_lon: float,
        position_error_nm: float = 1.0,
        drift_error_nm: float = 1.5,
        safety_factor: float = 1.3,
        visibility_nm: float = 10.0,
        available_speed_kts: float = 12.0,
        number_of_search_units: int = 1,
    ) -> SarOperationPlan:
        """Calculate IAMSAR datum probable error, search radius, area, and coverage."""
        # Total probable error: E = sqrt(d_e^2 + d_t^2)
        total_probable_error = math.sqrt(position_error_nm**2 + drift_error_nm**2)
        safety_factor_clamped = max(1.1, min(safety_factor, 1.8))
        search_radius_nm = round(total_probable_error * safety_factor_clamped, 2)

        # Standard IAMSAR square search area: A = 4 * R^2
        search_area_sq_nm = round(4.0 * (search_radius_nm**2), 2)

        # Base sweep width adjusted for visibility
        base_w = cls.SWEEP_WIDTH_TABLE.get(target_type, 2.0)
        vis_factor = max(0.4, min(visibility_nm / 10.0, 1.5))
        sweep_width_nm = round(base_w * math.sqrt(vis_factor), 2)

        # Recommended search pattern and track spacing S
        if search_radius_nm <= 5.0 and target_type in (
            SearchObjectType.PERSON_IN_WATER,
            SearchObjectType.LIFE_RAFT_4_6,
        ):
            pattern = SarSearchPattern.SECTOR_SEARCH
            track_spacing_nm = max(0.5, round(sweep_width_nm * 0.8, 2))
        elif search_radius_nm <= 10.0:
            pattern = SarSearchPattern.EXPANDING_SQUARE
            track_spacing_nm = max(0.8, round(sweep_width_nm * 1.0, 2))
        elif number_of_search_units >= 2:
            pattern = SarSearchPattern.PARALLEL_TRACK
            track_spacing_nm = max(1.0, round(sweep_width_nm * 1.2, 2))
        else:
            pattern = SarSearchPattern.CREEPING_LINE
            track_spacing_nm = max(1.0, round(sweep_width_nm * 1.0, 2))

        # Coverage factor C = W / S
        coverage_factor = round(sweep_width_nm / track_spacing_nm, 2)

        # Probability of Detection (POD) formula: POD = 100 * (1 - e^(-1.25 * C))
        pod_pct = round(100.0 * (1.0 - math.exp(-1.25 * coverage_factor)), 1)
        pod_pct = min(99.0, max(15.0, pod_pct))

        # Required search hours = Total Track Length / (Speed * Units)
        # Total Track Length L = Area / S
        total_track_length = search_area_sq_nm / track_spacing_nm
        effective_fleet_speed = max(1.0, available_speed_kts * max(1, number_of_search_units))
        required_hours = round(total_track_length / effective_fleet_speed, 1)

        summary = (
            f"IAMSAR KH-TKCN [{incident_id}]: Giai đoạn {phase.value.upper()}. "
            f"Tâm tìm kiếm ({datum_lat:.4f}N, {datum_lon:.4f}E), Bán kính R={search_radius_nm} NM. "
            f"Diện tích A={search_area_sq_nm} NM². Mẫu tìm kiếm đề xuất: {pattern.value.upper()}. "
            f"Khoảng cách vết quét S={track_spacing_nm} NM, Hệ số bao phủ C={coverage_factor}, "
            f"Xác suất phát hiện POD={pod_pct}%. Thời gian dự kiến: {required_hours}h."
        )

        return SarOperationPlan(
            incident_id=incident_id,
            phase=phase,
            target_type=target_type,
            datum_lat=datum_lat,
            datum_lon=datum_lon,
            search_radius_nm=search_radius_nm,
            search_area_sq_nm=search_area_sq_nm,
            recommended_pattern=pattern,
            track_spacing_nm=track_spacing_nm,
            sweep_width_nm=sweep_width_nm,
            coverage_factor=coverage_factor,
            probability_of_detection_pct=pod_pct,
            required_search_hours=required_hours,
            operational_summary=summary,
        )


# ==============================================================================
# PHASE 248: AIDS TO NAVIGATION (AtoN) & IALA BUOYAGE SYSTEM REGION A
# ==============================================================================

class IalaMarkType(str, Enum):
    """IALA Maritime Buoyage System Region A Mark Types."""
    PORT_HAND = "port_hand"              # Phao mạn trái (Đỏ, trụ/hình trụ)
    STARBOARD_HAND = "starboard_hand"    # Phao mạn phải (Xanh lục, nón)
    CARDINAL_NORTH = "cardinal_north"    # Phao phương vị Bắc
    CARDINAL_EAST = "cardinal_east"      # Phao phương vị Đông
    CARDINAL_SOUTH = "cardinal_south"    # Phao phương vị Nam
    CARDINAL_WEST = "cardinal_west"      # Phao phương vị Tây
    ISOLATED_DANGER = "isolated_danger"  # Phao chướng ngại biệt lập
    SAFE_WATER = "safe_water"            # Phao vùng nước an toàn
    SPECIAL_MARK = "special_mark"        # Phao chuyên dùng


class IalaCategory(int, Enum):
    """IALA AtoN Operational Availability Categories."""
    CATEGORY_1 = 1  # Tính khả dụng tối thiểu >= 99.8% (Hải đăng/phao trục chính)
    CATEGORY_2 = 2  # Tính khả dụng tối thiểu >= 99.0% (Phao luồng thứ cấp)
    CATEGORY_3 = 3  # Tính khả dụng tối thiểu >= 97.0% (Báo hiệu phụ trợ/nội thủy)


@dataclass(frozen=True)
class AtonSpecification:
    """AtoN Engineering & Visual Characteristics."""
    aton_id: str
    name: str
    mark_type: IalaMarkType
    category: IalaCategory
    color: str
    topmark: str
    light_characteristic: str
    elevation_above_sea_level_m: float
    luminous_intensity_candela: float
    geographic_range_nm: float
    luminous_range_nm: float
    operational_availability_pct: float
    meets_iala_standard: bool
    notice_to_mariners_required: bool
    remarks: str


class AtonMaritimeEngine:
    """Aids to Navigation (AtoN) Planning and IALA Region A Compliance Engine."""

    # Statutory Availability Thresholds (%)
    AVAILABILITY_TARGETS: Dict[IalaCategory, float] = {
        IalaCategory.CATEGORY_1: 99.8,
        IalaCategory.CATEGORY_2: 99.0,
        IalaCategory.CATEGORY_3: 97.0,
    }

    # Visual specifications under IALA Region A (Vietnam Maritime Waters)
    IALA_SPECS: Dict[IalaMarkType, Dict[str, str]] = {
        IalaMarkType.PORT_HAND: {
            "color": "Đỏ (Red)",
            "topmark": "Hình trụ đơn màu đỏ (Single red can)",
            "light": "Chớp đỏ (Fl R) chu kỳ bất kỳ trừ nhóm (2+1)",
        },
        IalaMarkType.STARBOARD_HAND: {
            "color": "Xanh lục (Green)",
            "topmark": "Hình nón đỉnh hướng lên màu xanh lục (Single green cone)",
            "light": "Chớp xanh lục (Fl G) chu kỳ bất kỳ trừ nhóm (2+1)",
        },
        IalaMarkType.CARDINAL_NORTH: {
            "color": "Đen phía trên vàng (Black above yellow)",
            "topmark": "Hai nón đen đỉnh hướng lên (Two cones points up)",
            "light": "Chớp nhanh liên tục trắng (Q W hoặc VQ W)",
        },
        IalaMarkType.CARDINAL_EAST: {
            "color": "Đen với dải vàng ở giữa (Black with yellow band)",
            "topmark": "Hai nón đen đáy đối nhau (Two cones bases together)",
            "light": "Chớp nhóm 3 trắng (VQ(3) 5s hoặc Q(3) 10s)",
        },
        IalaMarkType.CARDINAL_SOUTH: {
            "color": "Vàng phía trên đen (Yellow above black)",
            "topmark": "Hai nón đen đỉnh hướng xuống (Two cones points down)",
            "light": "Chớp nhóm 6 + chớp dài trắng (Q(6)+LFl 15s)",
        },
        IalaMarkType.CARDINAL_WEST: {
            "color": "Vàng với dải đen ở giữa (Yellow with black band)",
            "topmark": "Hai nón đen đỉnh đối nhau (Two cones points together)",
            "light": "Chớp nhóm 9 trắng (VQ(9) 10s hoặc Q(9) 15s)",
        },
        IalaMarkType.ISOLATED_DANGER: {
            "color": "Đen với một hoặc nhiều dải đỏ ngang (Black with red bands)",
            "topmark": "Hai quả cầu đen đặt chồng lên nhau (Two black spheres)",
            "light": "Chớp nhóm 2 trắng (Fl(2) W)",
        },
        IalaMarkType.SAFE_WATER: {
            "color": "Sọc đỏ trắng xen kẽ thẳng đứng (Red and white vertical stripes)",
            "topmark": "Một quả cầu đỏ đơn (Single red sphere)",
            "light": "Đẳng cự, gián đoạn, chớp dài 10s hoặc Morse 'A' (Iso/Occ/LFl/Mo(A) W)",
        },
        IalaMarkType.SPECIAL_MARK: {
            "color": "Vàng hoàn toàn (Yellow)",
            "topmark": "Chữ X màu vàng (Single yellow X)",
            "light": "Chớp vàng bất kỳ (Fl Y)",
        },
    }

    @classmethod
    def calculate_ranges(
        cls,
        elevation_m: float,
        intensity_candela: float,
        observer_eye_height_m: float = 5.0,
        atmospheric_transmissivity: float = 0.74,
    ) -> Tuple[float, float]:
        """Calculate Geographic Range (NM) and Luminous Range (NM) using Allard's Law."""
        # Geographic Range formula: D_g = 2.08 * (sqrt(H) + sqrt(h))
        elev_clamped = max(1.0, elevation_m)
        obs_clamped = max(1.0, observer_eye_height_m)
        geographic_range = round(2.08 * (math.sqrt(elev_clamped) + math.sqrt(obs_clamped)), 2)

        # Luminous Range estimate using Allard's law threshold E = 2e-7 lux at night
        # Simplified standard nautical formula: D_l ~ 1.5 * (Intensity)^0.35 * (T_a / 0.74)
        intensity_clamped = max(1.0, intensity_candela)
        luminous_range = round(
            1.5
            * (intensity_clamped**0.35)
            * (max(0.2, atmospheric_transmissivity) / 0.74),
            2,
        )
        return geographic_range, luminous_range

    @classmethod
    def evaluate_aton_status(
        cls,
        aton_id: str,
        name: str,
        mark_type: IalaMarkType,
        category: IalaCategory,
        elevation_m: float,
        intensity_candela: float,
        total_service_hours: float = 8760.0,
        outage_hours: float = 12.0,
        observer_eye_height_m: float = 5.0,
    ) -> AtonSpecification:
        """Audit AtoN operational parameters against IALA standards."""
        geo_range, lum_range = cls.calculate_ranges(
            elevation_m, intensity_candela, observer_eye_height_m
        )
        specs = cls.IALA_SPECS.get(mark_type, {
            "color": "Tiêu chuẩn",
            "topmark": "Tiêu chuẩn",
            "light": "Tiêu chuẩn",
        })

        serv_hours = max(100.0, total_service_hours)
        clamped_outage = max(0.0, min(outage_hours, serv_hours))
        actual_avail = round(((serv_hours - clamped_outage) / serv_hours) * 100.0, 3)

        target_avail = cls.AVAILABILITY_TARGETS[category]
        meets_standard = actual_avail >= target_avail
        notice_required = not meets_standard or clamped_outage > 4.0

        remarks = (
            f"Báo hiệu hàng hải [{aton_id}] {name}: Loại {mark_type.value}. Cấp độ {category.value}. "
            f"Tính khả dụng đạt {actual_avail}% (Tiêu chuẩn IALA tối thiểu: {target_avail}%). "
            f"Tầm địa lý: {geo_range} NM, Tầm hiệu lực ánh sáng: {lum_range} NM. "
            f"{'ĐẠT CHUẨN IALA.' if meets_standard else 'KHÔNG ĐẠT CHUẨN - Cần ban hành Thông báo Hàng hải khẩn cấp.'}"
        )

        return AtonSpecification(
            aton_id=aton_id,
            name=name,
            mark_type=mark_type,
            category=category,
            color=specs["color"],
            topmark=specs["topmark"],
            light_characteristic=specs["light"],
            elevation_above_sea_level_m=elevation_m,
            luminous_intensity_candela=intensity_candela,
            geographic_range_nm=geo_range,
            luminous_range_nm=lum_range,
            operational_availability_pct=actual_avail,
            meets_iala_standard=meets_standard,
            notice_to_mariners_required=notice_required,
            remarks=remarks,
        )


# ==============================================================================
# PHASE 249: TIERED OIL SPILL RESPONSE & DISPERSANT COMPLIANCE
# ==============================================================================

class OilSpillTier(str, Enum):
    """Decision 12/2021/QĐ-TTg National Oil Spill Response Tiers."""
    TIER_1 = "tier_1"  # Cấp cơ sở: Dưới 20 tấn
    TIER_2 = "tier_2"  # Cấp khu vực: Từ 20 đến 100 tấn
    TIER_3 = "tier_3"  # Cấp quốc gia: Trên 100 tấn


class OilProductClass(str, Enum):
    """Petroleum Product Volatility and Persistence Class."""
    LIGHT_DISTILLATE = "light_distillate"      # Xăng, naphtha, condensate (nhóm 1)
    MIDDLE_DISTILLATE = "middle_distillate"    # Dầu diesel (DO), dầu hỏa (nhóm 2)
    HEAVY_RESIDUAL = "heavy_residual"          # Dầu FO, crude oil, bitumen (nhóm 3)


@dataclass(frozen=True)
class OilSpillResponsePlan:
    """Oil Spill Incident Evaluation & Technical Countermeasures."""
    incident_id: str
    tier: OilSpillTier
    spill_volume_tons: float
    product_class: OilProductClass
    command_authority: str
    required_response_time_hours: float
    min_containment_boom_m: float
    min_skimmer_capacity_m3_h: float
    dispersant_permitted: bool
    dispersant_assessment: str
    statutory_fine_vnd: float
    remedial_measures: List[str]


class TieredOilSpillEngine:
    """National Oil Spill Response Decision 12/2021/QĐ-TTg & Decree 45/2022/NĐ-CP Engine."""

    # Containment boom safety multiplier based on vessel LOA
    BOOM_LOA_MULTIPLIER = 3.0

    @classmethod
    def classify_spill_tier(
        cls,
        spill_volume_tons: float,
        facility_capacity_exceeded: bool = False,
        transboundary_risk: bool = False,
    ) -> OilSpillTier:
        """Classify statutory response tier per Decision 12/2021/QĐ-TTg."""
        if spill_volume_tons > 100.0 or transboundary_risk:
            return OilSpillTier.TIER_3
        if spill_volume_tons >= 20.0 or facility_capacity_exceeded:
            return OilSpillTier.TIER_2
        return OilSpillTier.TIER_1

    @classmethod
    def evaluate_dispersant_application(
        cls,
        water_depth_m: float,
        distance_from_shore_nm: float,
        near_marine_protected_area: bool,
        near_aquaculture_zone: bool,
        product_class: OilProductClass,
    ) -> Tuple[bool, str]:
        """Audit chemical dispersant application criteria per Vietnam regulations."""
        # Prohibited for light distillates due to toxic vapors and rapid natural evaporation
        if product_class == OilProductClass.LIGHT_DISTILLATE:
            return (
                False,
                "CẤM SỬ DỤNG CHẤT PHÂN TÁN: Dầu nhẹ có độ bay hơi cao, chất phân tán làm tăng độc tính hòa tan.",
            )

        # Environmental safety boundaries: Depth >= 20m, Shore Distance >= 3 NM
        if water_depth_m < 20.0:
            return (
                False,
                f"CẤM SỬ DỤNG CHẤT PHÂN TÁN: Độ sâu khu vực ({water_depth_m}m) < 20m, nguy cơ ô nhiễm đáy biển.",
            )
        if distance_from_shore_nm < 3.0:
            return (
                False,
                f"CẤM SỬ DỤNG CHẤT PHÂN TÁN: Khoảng cách tới bờ ({distance_from_shore_nm} NM) < 3.0 NM theo Quy chế.",
            )
        if near_marine_protected_area or near_aquaculture_zone:
            return (
                False,
                "CẤM SỬ DỤNG CHẤT PHÂN TÁN: Khu vực gần khu bảo tồn biển hoặc vùng nuôi trồng thủy sản tập trung.",
            )

        return (
            True,
            "CHẤP THUẬN CÓ ĐIỀU KIỆN: Đủ điều kiện độ sâu >= 20m, xa bờ >= 3 NM. "
            "Phải sử dụng hóa chất trong danh mục cho phép của Bộ Tài nguyên & Môi trường.",
        )

    @classmethod
    def evaluate_spill_incident(
        cls,
        incident_id: str,
        spill_volume_tons: float,
        product_class: OilProductClass,
        vessel_loa_m: float = 120.0,
        water_depth_m: float = 25.0,
        distance_from_shore_nm: float = 5.0,
        near_mpa: bool = False,
        near_aquaculture: bool = False,
        delayed_reporting: bool = False,
        unauthorized_discharge: bool = True,
    ) -> OilSpillResponsePlan:
        """Formulate complete oil spill emergency tactical response plan."""
        tier = cls.classify_spill_tier(spill_volume_tons)

        if tier == OilSpillTier.TIER_1:
            authority = "Ban chỉ huy ứng phó sự cố cơ sở / Cảng biển chủ trì"
            resp_time = 1.0
        elif tier == OilSpillTier.TIER_2:
            authority = "Ủy ban nhân dân tỉnh / thành phố ven biển chỉ đạo (Trung tâm TKCN hàng hải hỗ trợ)"
            resp_time = 2.0
        else:
            authority = "Ủy ban Quốc gia Ứng phó sự cố, thiên tai và TKCN chỉ huy toàn diện"
            resp_time = 4.0

        # Minimum boom length: 3 * LOA or minimum 250m
        min_boom = max(250.0, round(vessel_loa_m * cls.BOOM_LOA_MULTIPLIER, 1))

        # Skimmer recovery capacity needed (target recovery within 72h)
        # EDRC (Effective Daily Recovery Capacity) derated at 20% efficiency
        # Required nameplate = Volume (m3) / (72h * 0.20)
        density = 0.88 if product_class == OilProductClass.MIDDLE_DISTILLATE else 0.95
        vol_m3 = spill_volume_tons / density
        min_skimmer = max(10.0, round(vol_m3 / (72.0 * 0.20), 1))

        dispersant_ok, dispersant_notes = cls.evaluate_dispersant_application(
            water_depth_m, distance_from_shore_nm, near_mpa, near_aquaculture, product_class
        )

        # Administrative penalties under Decree 45/2022/NĐ-CP Art. 34
        # Range: 50,000,000 to 1,000,000,000 VND (organization fine doubled)
        base_fine = 100_000_000.0
        if spill_volume_tons >= 100.0:
            base_fine = 900_000_000.0
        elif spill_volume_tons >= 20.0:
            base_fine = 450_000_000.0
        elif spill_volume_tons >= 5.0:
            base_fine = 250_000_000.0

        if delayed_reporting:
            base_fine += 100_000_000.0
        fine_vnd = min(1_000_000_000.0, base_fine)

        remedial = [
            f"Triển khai phao quây ngăn chặn dài tối thiểu {min_boom}m bao vây nguồn dầu.",
            f"Vận hành hệ thống máy hút dầu tràn (skimmer) công suất danh định >= {min_skimmer} m³/h.",
            "Thu hồi dầu nhiễm vào két chứa chuyên dụng, nghiêm cấm xả nước la-găng lẫn dầu ra biển.",
            "Lấy mẫu nước biển và trầm tích độc lập để quan trắc chỉ số Hydrocarbon dầu (TPH).",
            "Ký quỹ tài chính khắc phục sự cố môi trường và đền bù thiệt hại sinh thái.",
        ]

        return OilSpillResponsePlan(
            incident_id=incident_id,
            tier=tier,
            spill_volume_tons=spill_volume_tons,
            product_class=product_class,
            command_authority=authority,
            required_response_time_hours=resp_time,
            min_containment_boom_m=min_boom,
            min_skimmer_capacity_m3_h=min_skimmer,
            dispersant_permitted=dispersant_ok,
            dispersant_assessment=dispersant_notes,
            statutory_fine_vnd=fine_vnd,
            remedial_measures=remedial,
        )


# ==============================================================================
# PHASE 250: CHANNEL DREDGING, MAINTENANCE & SEA DUMPING LICENSING
# ==============================================================================

class SedimentClass(str, Enum):
    """QCVN 43:2017/BTNMT Marine Sediment Quality Classification."""
    CLASS_A_CLEAN = "class_a_clean"        # Trầm tích sạch, đạt chuẩn nhận chìm biển
    CLASS_B_RESTRICTED = "class_b_marginal" # Trầm tích cận ngưỡng, cần giám sát đặc biệt
    CLASS_C_CONTAMINATED = "class_c_toxic"  # Trầm tích ô nhiễm, cấm nhận chìm ngoài biển


@dataclass(frozen=True)
class DredgingProjectAssessment:
    """Navigation Channel Dredging Maintenance & Sea Dumping Assessment."""
    project_id: str
    channel_name: str
    dredge_length_m: float
    design_bottom_width_m: float
    design_depth_cd_m: float
    surveyed_depth_cd_m: float
    siltation_depth_m: float
    infill_volume_m3: float
    side_slope_volume_m3: float
    allowable_overdepth_volume_m3: float
    total_dredge_volume_m3: float
    sediment_class: SedimentClass
    sea_dumping_eligible: bool
    sea_dumping_licensing_criteria: str
    estimated_dredging_cost_vnd: float
    statutory_licensing_fee_vnd: float
    environmental_deposit_vnd: float


class ChannelDredgingEngine:
    """Navigation Channel Dredging Decree 159/2018/NĐ-CP & Decree 08/2022/NĐ-CP Engine."""

    # QCVN 43:2017/BTNMT Marine Sediment Contamination Thresholds (mg/kg dry weight)
    SEDIMENT_LIMITS = {
        "arsenic": 41.6,
        "cadmium": 4.2,
        "lead": 112.0,
        "mercury": 0.70,
        "copper": 108.0,
        "zinc": 271.0,
    }

    # Dredging unit rate benchmarks (VND/m3) based on standard maintenance hydraulic cutter/grab
    BASE_DREDGING_RATE_VND_M3 = 115_000.0

    @classmethod
    def evaluate_sediment_quality(
        cls,
        heavy_metals_mg_kg: Dict[str, float],
    ) -> Tuple[SedimentClass, str]:
        """Evaluate sediment samples against QCVN 43:2017/BTNMT."""
        exceeded_metals = []
        marginal_metals = []

        for metal, limit in cls.SEDIMENT_LIMITS.items():
            val = heavy_metals_mg_kg.get(metal, 0.0)
            if val > limit:
                exceeded_metals.append(f"{metal.upper()} ({val} > {limit})")
            elif val >= limit * 0.85:
                marginal_metals.append(f"{metal.upper()} ({val} ~ {limit})")

        if exceeded_metals:
            return (
                SedimentClass.CLASS_C_CONTAMINATED,
                f"Trầm tích nhiễm kim loại nặng vượt chuẩn QCVN 43: {', '.join(exceeded_metals)}. "
                "CẤM NHẬN CHÌM Ở BIỂN. Bắt buộc vận chuyển vào bãi chứa trên bờ để xử lý.",
            )
        if marginal_metals:
            return (
                SedimentClass.CLASS_B_RESTRICTED,
                f"Trầm tích tiệm cận ngưỡng quy chuẩn: {', '.join(marginal_metals)}. "
                "Được phép nhận chìm có điều kiện, kèm quan trắc liên tục độ đục TSS.",
            )
        return (
            SedimentClass.CLASS_A_CLEAN,
            "Trầm tích sạch, đạt tất cả chỉ tiêu an toàn QCVN 43:2017/BTNMT. "
            "Đủ điều kiện cấp phép nhận chìm tại vị trí quy hoạch hàng hải.",
        )

    @classmethod
    def calculate_dredging_volumes_and_licensing(
        cls,
        project_id: str,
        channel_name: str,
        dredge_length_m: float,
        design_bottom_width_m: float,
        design_depth_cd_m: float,      # e.g., -14.0m CD
        surveyed_depth_cd_m: float,    # e.g., -11.5m CD (shallower)
        side_slope_ratio: float = 3.0, # m:1 (m=3)
        allowable_overdepth_m: float = 0.4,
        heavy_metals_mg_kg: Optional[Dict[str, float]] = None,
        dumping_distance_nm: float = 12.0,
        dumping_depth_m: float = 28.0,
        buffer_from_mpa_nm: float = 8.0,
    ) -> DredgingProjectAssessment:
        """Compute navigation channel dredge volumes and statutory sea dumping license fees."""
        # Depths are represented in chart datum (negative meters)
        # Siltation depth = |design_depth| - |surveyed_depth|
        des_depth_abs = abs(design_depth_cd_m)
        surv_depth_abs = abs(surveyed_depth_cd_m)
        siltation_depth = max(0.0, des_depth_abs - surv_depth_abs)

        # 1. Main Infill Volume: V_infill = L * W * delta_h
        infill_vol = round(dredge_length_m * design_bottom_width_m * siltation_depth, 2)

        # 2. Side slope cut: V_slope = L * m * (delta_h)^2
        slope_vol = round(dredge_length_m * side_slope_ratio * (siltation_depth**2), 2)

        # 3. Allowable overdepth cut: V_overdepth = L * (W + 2 * m * delta_h) * overdepth
        overdepth_width = design_bottom_width_m + (2.0 * side_slope_ratio * siltation_depth)
        overdepth_vol = round(dredge_length_m * overdepth_width * allowable_overdepth_m, 2)

        total_vol = round(infill_vol + slope_vol + overdepth_vol, 2)

        # Sediment evaluation
        metals = heavy_metals_mg_kg or {
            "arsenic": 12.0,
            "cadmium": 0.8,
            "lead": 25.0,
            "mercury": 0.15,
            "copper": 30.0,
            "zinc": 65.0,
        }
        sed_class, sed_notes = cls.evaluate_sediment_quality(metals)

        # Sea dumping licensing conditions per Law on Sea & Decree 40/2019/NĐ-CP
        is_dumping_ok = (
            sed_class != SedimentClass.CLASS_C_CONTAMINATED
            and dumping_distance_nm >= 6.0
            and dumping_depth_m >= 20.0
            and buffer_from_mpa_nm >= 5.0
        )

        criteria_notes = (
            f"Vị trí nhận chìm: Cách bờ {dumping_distance_nm} NM (>=6 NM: ĐẠT), "
            f"Độ sâu {dumping_depth_m}m (>=20m: ĐẠT), "
            f"Cách khu bảo tồn biển {buffer_from_mpa_nm} NM (>=5 NM: ĐẠT). {sed_notes}"
        )

        # Cost & statutory deposit calculations
        est_dredge_cost = round(total_vol * cls.BASE_DREDGING_RATE_VND_M3, 0)
        # Circular 262/2016/TT-BTC licensing fee: 20M to 100M VND based on volume
        licensing_fee = 50_000_000.0 if total_vol >= 100_000 else 25_000_000.0
        # Environmental remediation escrow deposit: 5% of dredging cost
        env_deposit = round(est_dredge_cost * 0.05, 0)

        return DredgingProjectAssessment(
            project_id=project_id,
            channel_name=channel_name,
            dredge_length_m=dredge_length_m,
            design_bottom_width_m=design_bottom_width_m,
            design_depth_cd_m=design_depth_cd_m,
            surveyed_depth_cd_m=surveyed_depth_cd_m,
            siltation_depth_m=siltation_depth,
            infill_volume_m3=infill_vol,
            side_slope_volume_m3=slope_vol,
            allowable_overdepth_volume_m3=overdepth_vol,
            total_dredge_volume_m3=total_vol,
            sediment_class=sed_class,
            sea_dumping_eligible=is_dumping_ok,
            sea_dumping_licensing_criteria=criteria_notes,
            estimated_dredging_cost_vnd=est_dredge_cost,
            statutory_licensing_fee_vnd=licensing_fee,
            environmental_deposit_vnd=env_deposit,
        )
