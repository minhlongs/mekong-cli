"""
Vietnamese Geodesy, Cartography, Remote Sensing & Geographic Information System (GIS) Engine.
Pure Python standard library implementation adhering to tests/test_core_boundary.py.

Statutory Framework:
- Luật Đo đạc và bản đồ 2018 (Luật số 27/2018/QH14):
  * Hệ quy chiếu và Hệ tọa độ quốc gia VN-2000 (Quyết định số 83/2000/QĐ-TTg):
    - Ellipsoid WGS-84: Bán trục lớn a = 6378137m, độ dẹt alpha = 1/298.257223563.
    - Lưới chiếu UTM / Transverse Mercator: Múi chiếu 3 độ (k0 = 0.9999) hoặc 6 độ (k0 = 0.9996).
    - Kinh tuyến trục (Central Meridian) địa phương theo từng tỉnh/thành phố.
    - Điểm gốc tọa độ quốc gia tại Viện Khoa học Đo đạc và Bản đồ, Hà Nội.
  * Hạ tầng dữ liệu không gian địa lý quốc gia (NSDI - National Spatial Data Infrastructure).
  * Bảo vệ chủ quyền lãnh thổ trên bản đồ (Điều 6):
    - Nghiêm cấm xuất bản, lưu hành bản đồ không thể hiện hoặc thể hiện sai lệch chủ quyền biên giới quốc gia,
      quần đảo Hoàng Sa và Trường Sa, hoặc có đường lưỡi bò phi pháp.
  * Điều kiện cấp Giấy phép hoạt động đo đạc và bản đồ (Điều 51, 52):
    - Người phụ trách kỹ thuật có bằng đại học chuyên ngành và kinh nghiệm >= 5 năm.
    - Tối thiểu 02 nhân sự kỹ thuật có chứng chỉ hành nghề.
    - Thiết bị đo đạc (GNSS RTK, máy toàn đạc) được kiểm định, hiệu chuẩn còn hiệu lực.
- Thông tư số 25/2014/TT-BTNMT & Thông tư số 09/2021/TT-BTNMT về Bản đồ địa chính:
  * Quy định sai số trung phương vị trí điểm góc ranh thửa đất so với điểm khống chế:
    - Đô thị: Tỷ lệ 1:500 (<= 0.07m), 1:1000 (<= 0.10m), 1:2000 (<= 0.20m).
    - Nông thôn: Tỷ lệ 1:1000 (<= 0.15m), 1:2000 (<= 0.30m), 1:5000 (<= 0.70m).
- Nghị định số 18/2020/NĐ-CP & Nghị định số 04/2022/NĐ-CP:
  * Xử phạt vi phạm hành chính trong lĩnh vực đo đạc bản đồ, vi phạm chủ quyền lãnh thổ (30M - 50M VND, tịch thu tang vật).
"""

from __future__ import annotations

import datetime
import hashlib
import json
import math
import os
import sqlite3
from typing import Any, Dict, List, Optional


class GeodesyEngine:
    """Core engine for Vietnamese Geodesy, National VN-2000 Coordinates, Map Sovereignty & Cadastral GIS."""

    # Statutory Central Meridians (Kinh tuyến trục) for key provinces/cities (Degrees)
    CENTRAL_MERIDIANS: Dict[str, float] = {
        "HÀ NỘI": 105.0,
        "TP. HỒ CHÍ MINH": 105.75,
        "ĐÀ NẴNG": 107.75,
        "HẢI PHÒNG": 105.75,
        "CẦN THƠ": 105.0,
        "ĐỒNG NAI": 107.75,
        "BÌNH DƯƠNG": 105.75,
        "BÀ RỊA - VŨNG TÀU": 107.75,
        "QUẢNG NINH": 107.75,
        "KHÁNH HÒA": 108.25,
        "LÂM ĐỒNG": 107.75,
        "THỪA THIÊN HUẾ": 107.0,
        "NGHỆ AN": 104.75,
        "THANH HÓA": 105.0,
        "AN GIANG": 104.5,
        "KIÊN GIANG": 104.5,
        "CÀ MAU": 104.5,
    }

    def __init__(self, db_path: Optional[str] = None) -> None:
        if db_path is None:
            base_dir = os.path.join(os.getcwd(), ".mekong")
            os.makedirs(base_dir, exist_ok=True)
            self.db_path = os.path.join(base_dir, "geodesy.db")
        else:
            self.db_path = db_path
            parent = os.path.dirname(db_path)
            if parent:
                os.makedirs(parent, exist_ok=True)

        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS coordinate_conversions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversion_code TEXT UNIQUE NOT NULL,
                    point_id TEXT NOT NULL,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    zone_deg INTEGER NOT NULL,
                    central_meridian_deg REAL NOT NULL,
                    x_northing_m REAL NOT NULL,
                    y_easting_m REAL NOT NULL,
                    is_in_vietnam INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS map_sovereignty_audits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    audit_code TEXT UNIQUE NOT NULL,
                    map_title TEXT NOT NULL,
                    publisher_or_platform TEXT NOT NULL,
                    has_hoang_sa INTEGER NOT NULL,
                    has_truong_sa INTEGER NOT NULL,
                    has_nine_dash_line INTEGER NOT NULL,
                    is_compliant INTEGER NOT NULL,
                    penalty_fine_vnd REAL NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS geodesy_licenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    license_code TEXT UNIQUE NOT NULL,
                    enterprise_name TEXT NOT NULL,
                    technical_director TEXT NOT NULL,
                    years_experience INTEGER NOT NULL,
                    certified_surveyors_count INTEGER NOT NULL,
                    has_calibrated_instruments INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    is_approved INTEGER NOT NULL,
                    deficiencies TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS cadastral_surveys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    survey_code TEXT UNIQUE NOT NULL,
                    parcel_id TEXT NOT NULL,
                    province TEXT NOT NULL,
                    map_scale TEXT NOT NULL,
                    area_type TEXT NOT NULL,
                    max_boundary_error_m REAL NOT NULL,
                    measured_boundary_error_m REAL NOT NULL,
                    status TEXT NOT NULL,
                    is_compliant INTEGER NOT NULL,
                    deficiencies TEXT,
                    created_at TEXT NOT NULL
                );
                """
            )

    # 1. Coordinate Transformation & VN-2000 System Validation
    def validate_coordinate_system(
        self,
        point_id: str,
        latitude: float,
        longitude: float,
        zone_deg: int = 3,
        province: str = "HÀ NỘI",
    ) -> Dict[str, Any]:
        """Validates coordinates against VN-2000 national datum and computes Gauss-Kruger / Transverse Mercator plane coordinates."""
        now = datetime.datetime.now()
        prov_key = province.upper().strip()
        central_meridian = self.CENTRAL_MERIDIANS.get(prov_key, 105.0)

        # Territory bounding box check for Vietnam:
        # Latitude ~ 8.0 to 23.5 N, Longitude ~ 102.0 to 117.5 E (including Spratly & Paracel archipelagos)
        is_in_vn = (8.0 <= latitude <= 23.8) and (102.0 <= longitude <= 117.5)

        # Scale factor: 0.9999 for 3-degree zone, 0.9996 for 6-degree zone
        scale_k0 = 0.9999 if zone_deg == 3 else 0.9996

        # Standard VN-2000 / WGS-84 Ellipsoid constants
        a = 6378137.0  # semi-major axis
        f = 1.0 / 298.257223563  # flattening
        e2 = 2 * f - f**2

        # Convert lat/lon differences to radians
        phi = math.radians(latitude)
        lam = math.radians(longitude)
        lam0 = math.radians(central_meridian)
        d_lam = lam - lam0

        # Meridional arc length calculation
        m0 = a * ((1 - e2 / 4 - 3 * e2**2 / 64 - 5 * e2**3 / 256) * phi
                  - (3 * e2 / 8 + 3 * e2**2 / 32 + 45 * e2**3 / 1024) * math.sin(2 * phi)
                  + (15 * e2**2 / 256 + 45 * e2**3 / 1024) * math.sin(4 * phi)
                  - (35 * e2**3 / 3072) * math.sin(6 * phi))

        # Radius of curvature in prime vertical
        nu = a / math.sqrt(1 - e2 * (math.sin(phi) ** 2))
        t = math.tan(phi) ** 2
        c = (e2 / (1 - e2)) * (math.cos(phi) ** 2)

        # Transverse Mercator Coordinates
        x_northing = scale_k0 * (m0 + nu * math.tan(phi) * (
            (d_lam**2) / 2
            + ((5 - t + 9 * c + 4 * c**2) * (d_lam**4)) / 24
            + ((61 - 58 * t + t**2 + 600 * c - 330 * (e2 / (1 - e2))) * (d_lam**6)) / 720
        ))

        false_easting = 500000.0  # 500km false easting standard
        y_easting = false_easting + scale_k0 * nu * (
            d_lam
            + ((1 - t + c) * (d_lam**3)) / 6
            + ((5 - 18 * t + t**2 + 72 * c - 58 * (e2 / (1 - e2))) * (d_lam**5)) / 120
        )

        status = "COORDINATE_VALID_VN2000" if is_in_vn else "OUTSIDE_VIETNAM_TERRITORY"
        seq = hashlib.md5(f"{point_id}:{latitude}:{longitude}:{now.timestamp()}".encode("utf-8")).hexdigest()[:6].upper()
        conv_code = f"VN2K-{now.year}-{seq}"

        result = {
            "conversion_code": conv_code,
            "point_id": point_id,
            "latitude": round(latitude, 7),
            "longitude": round(longitude, 7),
            "zone_deg": zone_deg,
            "province": prov_key,
            "central_meridian_deg": central_meridian,
            "scale_factor_k0": scale_k0,
            "x_northing_m": round(x_northing, 3),
            "y_easting_m": round(y_easting, 3),
            "false_easting_m": false_easting,
            "is_in_vietnam": is_in_vn,
            "datum": "VN-2000 (Ellipsoid WGS-84)",
            "status": status,
            "statutory_basis": "Quyết định 83/2000/QĐ-TTg & Thông tư 973/2001/TT-TCĐC",
            "created_at": now.isoformat(),
        }

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO coordinate_conversions
                (conversion_code, point_id, latitude, longitude, zone_deg,
                 central_meridian_deg, x_northing_m, y_easting_m, is_in_vietnam,
                 status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    conv_code,
                    point_id,
                    latitude,
                    longitude,
                    zone_deg,
                    central_meridian,
                    result["x_northing_m"],
                    result["y_easting_m"],
                    1 if is_in_vn else 0,
                    status,
                    result["created_at"],
                ),
            )

        return result

    # 2. Map Sovereignty & Territory Integrity Audit
    def audit_map_sovereignty(
        self,
        map_title: str,
        publisher_or_platform: str,
        has_hoang_sa: bool = True,
        has_truong_sa: bool = True,
        has_nine_dash_line: bool = False,
        map_type: str = "DIGITAL_WEB",
    ) -> Dict[str, Any]:
        """Audits published/online maps for national sovereignty integrity under Article 6 Law on Geodesy and Decree 18/2020."""
        now = datetime.datetime.now()
        deficiencies = []
        fine_vnd = 0.0

        if has_nine_dash_line:
            status = "MAP_PROHIBITED_VIOLATION"
            fine_vnd = 50_000_000.0
            deficiencies.append("NGHIÊM CẤM: Bản đồ thể hiện đường chín đoạn (đường lưỡi bò) phi pháp vi phạm chủ quyền lãnh thổ Việt Nam")
        elif not has_hoang_sa or not has_truong_sa:
            status = "SOVEREIGNTY_DEFICIENT_MAP"
            fine_vnd = 40_000_000.0
            if not has_hoang_sa:
                deficiencies.append("Thiếu hoặc không thể hiện quần đảo Hoàng Sa thuộc chủ quyền Việt Nam")
            if not has_truong_sa:
                deficiencies.append("Thiếu hoặc không thể hiện quần đảo Trường Sa thuộc chủ quyền Việt Nam")
        else:
            status = "SOVEREIGNTY_COMPLIANT_MAP"
            fine_vnd = 0.0

        is_compliant = (status == "SOVEREIGNTY_COMPLIANT_MAP")
        seq = hashlib.md5(f"{map_title}:{publisher_or_platform}:{now.timestamp()}".encode("utf-8")).hexdigest()[:6].upper()
        audit_code = f"SOV-{now.year}-{seq}"

        result = {
            "audit_code": audit_code,
            "map_title": map_title,
            "publisher_or_platform": publisher_or_platform,
            "map_type": map_type.upper().strip(),
            "has_hoang_sa": has_hoang_sa,
            "has_truong_sa": has_truong_sa,
            "has_nine_dash_line": has_nine_dash_line,
            "is_compliant": is_compliant,
            "penalty_fine_vnd": fine_vnd,
            "status": status,
            "deficiencies": deficiencies,
            "legal_consequence": (
                "Tịch thu tang vật, phương tiện, cấm lưu hành và xử phạt theo Nghị định 18/2020/NĐ-CP"
                if not is_compliant
                else "Bản đồ thể hiện đầy đủ, chính xác chủ quyền biển đảo và biên giới quốc gia Việt Nam"
            ),
            "statutory_basis": "Điều 6 Luật Đo đạc và bản đồ 2018 & Điều 11 Nghị định 18/2020/NĐ-CP",
            "created_at": now.isoformat(),
        }

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO map_sovereignty_audits
                (audit_code, map_title, publisher_or_platform, has_hoang_sa,
                 has_truong_sa, has_nine_dash_line, is_compliant, penalty_fine_vnd,
                 status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    audit_code,
                    map_title,
                    publisher_or_platform,
                    1 if has_hoang_sa else 0,
                    1 if has_truong_sa else 0,
                    1 if has_nine_dash_line else 0,
                    1 if is_compliant else 0,
                    fine_vnd,
                    status,
                    result["created_at"],
                ),
            )

        return result

    # 3. Geodesy & Cartography Business Licensing
    def license_geodesy_activity(
        self,
        enterprise_name: str,
        technical_director: str,
        years_experience: int,
        certified_surveyors_count: int,
        has_calibrated_instruments: bool = True,
        scope: str = "CADASTRAL_AND_TOPOGRAPHIC",
    ) -> Dict[str, Any]:
        """Evaluates enterprise qualification for Geodesy & Cartography Operating License under Articles 51 & 52."""
        now = datetime.datetime.now()
        deficiencies = []

        if years_experience < 5:
            deficiencies.append(
                f"Người phụ trách kỹ thuật ({technical_director}) chỉ có {years_experience} năm kinh nghiệm (Yêu cầu >= 5 năm theo Điều 52)"
            )

        if certified_surveyors_count < 2:
            deficiencies.append(
                f"Doanh nghiệp chỉ có {certified_surveyors_count} kỹ thuật viên có chứng chỉ hành nghề (Yêu cầu tối thiểu 02 nhân sự có chứng chỉ)"
            )

        if not has_calibrated_instruments:
            deficiencies.append("Thiết bị đo đạc chưa được kiểm định, hiệu chuẩn theo quy chuẩn kỹ thuật hoặc giấy kiểm định đã hết hạn")

        is_approved = (len(deficiencies) == 0)
        status = "LICENSE_APPROVED" if is_approved else "LICENSE_REJECTED"
        seq = hashlib.md5(f"{enterprise_name}:{technical_director}:{now.timestamp()}".encode("utf-8")).hexdigest()[:6].upper()
        lic_code = f"GP-DDBĐ-{now.year}-{seq}"

        result = {
            "license_code": lic_code,
            "enterprise_name": enterprise_name,
            "technical_director": technical_director,
            "years_experience": years_experience,
            "certified_surveyors_count": certified_surveyors_count,
            "has_calibrated_instruments": has_calibrated_instruments,
            "scope": scope.upper().strip(),
            "is_approved": is_approved,
            "status": status,
            "deficiencies": deficiencies,
            "validity_years": 5 if is_approved else 0,
            "statutory_basis": "Điều 51, 52 Luật Đo đạc và bản đồ 2018 & Nghị định 27/2019/NĐ-CP",
            "created_at": now.isoformat(),
        }

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO geodesy_licenses
                (license_code, enterprise_name, technical_director, years_experience,
                 certified_surveyors_count, has_calibrated_instruments, status,
                 is_approved, deficiencies, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    lic_code,
                    enterprise_name,
                    technical_director,
                    years_experience,
                    certified_surveyors_count,
                    1 if has_calibrated_instruments else 0,
                    status,
                    1 if is_approved else 0,
                    json.dumps(deficiencies, ensure_ascii=False),
                    result["created_at"],
                ),
            )

        return result

    # 4. Cadastral Survey Error Tolerance Audit
    def inspect_cadastral_survey(
        self,
        parcel_id: str,
        province: str,
        map_scale: str = "1:500",
        area_type: str = "URBAN",
        measured_boundary_error_m: float = 0.05,
    ) -> Dict[str, Any]:
        """Audits boundary point coordinate accuracy against Circular 25/2014/TT-BTNMT standards."""
        now = datetime.datetime.now()
        scale = map_scale.strip()
        area = area_type.upper().strip()

        # Maximum allowable boundary point mean square error (meters)
        # Based on Article 8 Circular 25/2014/TT-BTNMT
        if area == "URBAN":
            scale_limits = {
                "1:500": 0.07,
                "1:1000": 0.10,
                "1:2000": 0.20,
                "1:5000": 0.50,
            }
        else:  # RURAL / MOUNTAINOUS
            scale_limits = {
                "1:500": 0.10,
                "1:1000": 0.15,
                "1:2000": 0.30,
                "1:5000": 0.70,
            }

        max_allowed_error = scale_limits.get(scale, 0.10)
        deficiencies = []

        if measured_boundary_error_m > max_allowed_error:
            deficiencies.append(
                f"Sai số vị trí điểm ranh đất ({measured_boundary_error_m}m) vượt quá hạn mức cho phép ({max_allowed_error}m) tại tỷ lệ {scale} khu vực {area}"
            )

        if measured_boundary_error_m < 0:
            deficiencies.append("Sai số đo đạc không hợp lệ (nhỏ hơn 0)")

        is_compliant = (len(deficiencies) == 0)
        status = "SURVEY_APPROVED_COMPLIANT" if is_compliant else "SURVEY_ERROR_EXCEEDED"
        seq = hashlib.md5(f"{parcel_id}:{province}:{now.timestamp()}".encode("utf-8")).hexdigest()[:6].upper()
        survey_code = f"CAD-{now.year}-{seq}"

        result = {
            "survey_code": survey_code,
            "parcel_id": parcel_id,
            "province": province.upper().strip(),
            "map_scale": scale,
            "area_type": area,
            "max_boundary_error_m": max_allowed_error,
            "measured_boundary_error_m": measured_boundary_error_m,
            "is_compliant": is_compliant,
            "status": status,
            "deficiencies": deficiencies,
            "statutory_basis": "Điều 8 Thông tư 25/2014/TT-BTNMT về bản đồ địa chính",
            "created_at": now.isoformat(),
        }

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO cadastral_surveys
                (survey_code, parcel_id, province, map_scale, area_type,
                 max_boundary_error_m, measured_boundary_error_m, status,
                 is_compliant, deficiencies, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    survey_code,
                    parcel_id,
                    result["province"],
                    scale,
                    area,
                    max_allowed_error,
                    measured_boundary_error_m,
                    status,
                    1 if is_compliant else 0,
                    json.dumps(deficiencies, ensure_ascii=False),
                    result["created_at"],
                ),
            )

        return result

    # 5. List Records
    def list_records(self, category: str = "coordinates", limit: int = 20) -> List[Dict[str, Any]]:
        """Queries stored coordinate conversions, sovereignty audits, licenses, or cadastral surveys."""
        cat = category.lower().strip()
        with self._get_connection() as conn:
            if cat in ["sovereignty", "maps", "bien_gioi", "chu_quyen"]:
                cursor = conn.execute("SELECT * FROM map_sovereignty_audits ORDER BY id DESC LIMIT ?", (limit,))
            elif cat in ["licenses", "enterprises", "giay_phep"]:
                cursor = conn.execute("SELECT * FROM geodesy_licenses ORDER BY id DESC LIMIT ?", (limit,))
            elif cat in ["surveys", "cadastral", "dia_chinh"]:
                cursor = conn.execute("SELECT * FROM cadastral_surveys ORDER BY id DESC LIMIT ?", (limit,))
            else:
                cursor = conn.execute("SELECT * FROM coordinate_conversions ORDER BY id DESC LIMIT ?", (limit,))

            return [dict(row) for row in cursor.fetchall()]

    # 6. Telemetry & Summary Status
    def get_status(self) -> Dict[str, Any]:
        """Aggregates system-wide Geodesy, Map Sovereignty and Cadastral GIS telemetry."""
        with self._get_connection() as conn:
            total_coords = conn.execute("SELECT COUNT(*) FROM coordinate_conversions").fetchone()[0]
            vn_coords = conn.execute("SELECT COUNT(*) FROM coordinate_conversions WHERE is_in_vietnam = 1").fetchone()[0]
            total_maps = conn.execute("SELECT COUNT(*) FROM map_sovereignty_audits").fetchone()[0]
            prohibited_maps = conn.execute("SELECT COUNT(*) FROM map_sovereignty_audits WHERE status = 'MAP_PROHIBITED_VIOLATION'").fetchone()[0]
            total_fines = conn.execute("SELECT COALESCE(SUM(penalty_fine_vnd), 0.0) FROM map_sovereignty_audits").fetchone()[0]
            total_lics = conn.execute("SELECT COUNT(*) FROM geodesy_licenses").fetchone()[0]
            approved_lics = conn.execute("SELECT COUNT(*) FROM geodesy_licenses WHERE is_approved = 1").fetchone()[0]
            total_surveys = conn.execute("SELECT COUNT(*) FROM cadastral_surveys").fetchone()[0]
            compliant_surveys = conn.execute("SELECT COUNT(*) FROM cadastral_surveys WHERE is_compliant = 1").fetchone()[0]

        return {
            "status": "HEALTHY",
            "statutory_law": "Luật Đo đạc và bản đồ 2018 (Luật số 27/2018/QH14) & Quyết định 83/2000/QĐ-TTg",
            "national_coordinate_system": "VN-2000 (Ellipsoid WGS-84, Transverse Mercator)",
            "total_coordinate_points_transformed": total_coords,
            "valid_vietnam_territory_points": vn_coords,
            "total_map_sovereignty_inspections": total_maps,
            "prohibited_maps_detected": prohibited_maps,
            "total_sovereignty_penalties_vnd": total_fines,
            "total_geodesy_licenses_processed": total_lics,
            "active_geodesy_operating_licenses": approved_lics,
            "total_cadastral_surveys_audited": total_surveys,
            "compliant_cadastral_surveys": compliant_surveys,
            "timestamp": datetime.datetime.now().isoformat(),
        }
