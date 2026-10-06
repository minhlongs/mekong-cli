"""
Vietnamese National Reserves, Strategic Stockpiling & Emergency Relief Allocations Suite.
Governed by:
- Law on National Reserve 2012 (Law No. 22/2012/QH13 - Luật Dự trữ quốc gia 2012)
- Decree No. 94/2013/NĐ-CP (Implementation of the Law on National Reserve)
- Decree No. 128/2020/NĐ-CP (Penalties in National Reserve Management)
- Circular No. 131/2013/TT-BTC & National Technical Regulations (QCVN) on State Reserve Commodities

Pure standard library implementation adhering to the core boundary invariant.
Thread-safe SQLite backend with WAL mode enabled.
"""

from __future__ import annotations

import datetime
import os
import pathlib
import sqlite3
import typing
from typing import Any, Dict, List, Optional, Tuple

DEFAULT_DB_PATH = os.path.expanduser(
    os.getenv("MEKONG_NATIONALRESERVE_DB", "~/.mekong/nationalreserve.db")
)

# Standard statutory categories under Art 27 of Law 22/2012/QH13
VALID_CATEGORIES = {
    "GRAIN_FOOD",            # Lương thực: gạo, thóc
    "RESCUE_EQUIPMENT",       # Vật tư thiết bị cứu hộ, cứu nạn (xuồng, bè, máy bơm, nhà bạt)
    "PETROLEUM_ENERGY",       # Xăng dầu, nhiên liệu chiến lược
    "MEDICAL_SUPPLIES",       # Vật tư y tế, vắc-xin, hóa chất khử trùng
    "AGRICULTURAL_SEEDS",     # Hạt giống cây trồng, giống vật nuôi, thuốc BVTV
    "DEFENSE_SECURITY",       # Thiết bị đặc chủng phục vụ quốc phòng, an ninh
}

# Standard warehouse regions
VALID_REGIONS = {
    "NORTH",
    "CENTRAL",
    "SOUTH",
    "CENTRAL_HIGHLANDS",
    "MEKONG_DELTA",
}

# Storage technical types under QCVN
VALID_STORAGE_TYPES = {
    "REGULAR_STORAGE",
    "CONTROLLED_ATMOSPHERE_N2",
    "HERMETIC_SILO",
    "UNDERGROUND_TANK",
}

# Quality status under technical inspection
VALID_QUALITY_STATUSES = {
    "PASSED",
    "WARNING",
    "SUBSTANDARD",
}

# Relief allocation purposes under Art 35
VALID_RELIEF_PURPOSES = {
    "DISASTER_RELIEF",          # Cứu trợ thiên tai, bão lũ
    "HUNGER_RELIEF_TET",        # Hỗ trợ cứu đói Tết & giáp hạt
    "EPIDEMIC_CONTROL",         # Phòng chống dịch bệnh
    "DEFENSE_SECURITY_MISSION", # Quốc phòng, an ninh khẩn cấp
    "MARKET_STABILIZATION",     # Xuất bán bình ổn giá thị trường
}

# Authorities authorized to order release under Art 36
VALID_AUTHORITIES = {
    "PRIME_MINISTER",
    "MINISTER_OF_FINANCE",
    "MINISTER_OF_DEFENSE",
    "MINISTER_OF_PUBLIC_SECURITY",
}

# Stock rotation modes
VALID_ROTATION_TYPES = {
    "AUCTION_SALE",
    "DIRECT_PURCHASE_REPLACEMENT",
    "EMERGENCY_REPURCHASE",
}


def _add_months(sourcedate: datetime.date, months: int) -> datetime.date:
    """Add calendar months to date safely."""
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month // 12
    month = month % 12 + 1
    day = min(sourcedate.day, [31,
        29 if year % 4 == 0 and not year % 100 == 0 or year % 400 == 0 else 28,
        31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
    return datetime.date(year, month, day)


class NationalReserveEngine:
    """
    Core engine managing Vietnamese National Reserve stocks, strategic storage facilities,
    quality certifications, emergency relief distributions, and statutory stock rotations.
    """

    def __init__(self, db_path: Optional[str] = None):
        self._memory_conn: Optional[sqlite3.Connection] = None
        self.db_path = db_path or os.getenv("MEKONG_NATIONALRESERVE_DB") or DEFAULT_DB_PATH
        if self.db_path != ":memory:":
            self.db_path = os.path.expanduser(self.db_path)
            pathlib.Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        if self.db_path == ":memory:":
            if self._memory_conn is None:
                self._memory_conn = sqlite3.connect(":memory:")
                self._memory_conn.row_factory = sqlite3.Row
                self._memory_conn.execute("PRAGMA foreign_keys = ON")
            return self._memory_conn
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS reserve_warehouses (
                    warehouse_code TEXT PRIMARY KEY,
                    warehouse_name TEXT NOT NULL,
                    region TEXT NOT NULL,
                    managing_unit TEXT NOT NULL,
                    storage_type TEXT NOT NULL,
                    total_capacity REAL NOT NULL,
                    current_utilization REAL NOT NULL DEFAULT 0.0,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS reserve_inventories (
                    inventory_code TEXT PRIMARY KEY,
                    warehouse_code TEXT NOT NULL,
                    item_category TEXT NOT NULL,
                    item_name TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    unit TEXT NOT NULL,
                    intake_date TEXT NOT NULL,
                    max_storage_months INTEGER NOT NULL,
                    quality_status TEXT NOT NULL DEFAULT 'PASSED',
                    unit_cost_vnd REAL NOT NULL DEFAULT 0.0,
                    total_value_vnd REAL NOT NULL DEFAULT 0.0,
                    rotation_due_date TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(warehouse_code) REFERENCES reserve_warehouses(warehouse_code)
                );

                CREATE TABLE IF NOT EXISTS relief_allocations (
                    allocation_code TEXT PRIMARY KEY,
                    decision_number TEXT NOT NULL,
                    decision_authority TEXT NOT NULL,
                    purpose TEXT NOT NULL,
                    inventory_code TEXT NOT NULL,
                    beneficiary_locality TEXT NOT NULL,
                    requested_quantity REAL NOT NULL,
                    allocated_quantity REAL NOT NULL,
                    unit TEXT NOT NULL,
                    dispatch_date TEXT NOT NULL,
                    delivery_status TEXT NOT NULL DEFAULT 'DISPATCHED',
                    budget_replenishment_vnd REAL NOT NULL DEFAULT 0.0,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(inventory_code) REFERENCES reserve_inventories(inventory_code)
                );

                CREATE TABLE IF NOT EXISTS rotation_plans (
                    rotation_code TEXT PRIMARY KEY,
                    inventory_code TEXT NOT NULL,
                    plan_year INTEGER NOT NULL,
                    rotation_type TEXT NOT NULL,
                    outgoing_quantity REAL NOT NULL,
                    replacement_deadline TEXT NOT NULL,
                    realized_proceeds_vnd REAL NOT NULL DEFAULT 0.0,
                    reacquisition_budget_vnd REAL NOT NULL DEFAULT 0.0,
                    status TEXT NOT NULL DEFAULT 'PLANNED',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(inventory_code) REFERENCES reserve_inventories(inventory_code)
                );

                CREATE INDEX IF NOT EXISTS idx_inv_warehouse ON reserve_inventories(warehouse_code);
                CREATE INDEX IF NOT EXISTS idx_inv_category ON reserve_inventories(item_category);
                CREATE INDEX IF NOT EXISTS idx_relief_inv ON relief_allocations(inventory_code);
                CREATE INDEX IF NOT EXISTS idx_rot_inv ON rotation_plans(inventory_code);
                """
            )

    def register_warehouse(
        self,
        warehouse_code: str,
        warehouse_name: str,
        region: str,
        managing_unit: str,
        storage_type: str,
        total_capacity: float,
    ) -> Dict[str, Any]:
        """
        Register a state reserve strategic storage depot / warehouse.
        """
        code = warehouse_code.strip()
        name = warehouse_name.strip()
        reg = region.strip().upper()
        unit_str = managing_unit.strip()
        stype = storage_type.strip().upper()

        if not code or not name or not unit_str:
            raise ValueError("warehouse_code, warehouse_name, and managing_unit cannot be empty.")
        if reg not in VALID_REGIONS:
            raise ValueError(f"Invalid region '{reg}'. Must be one of: {sorted(VALID_REGIONS)}")
        if stype not in VALID_STORAGE_TYPES:
            raise ValueError(f"Invalid storage_type '{stype}'. Must be one of: {sorted(VALID_STORAGE_TYPES)}")
        if total_capacity <= 0:
            raise ValueError("total_capacity must be strictly positive.")

        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT warehouse_code FROM reserve_warehouses WHERE warehouse_code = ?", (code,))
            if cur.fetchone():
                raise ValueError(f"Warehouse '{code}' already exists.")

            cur.execute(
                """
                INSERT INTO reserve_warehouses (
                    warehouse_code, warehouse_name, region, managing_unit,
                    storage_type, total_capacity, current_utilization, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, 0.0, ?)
                """,
                (code, name, reg, unit_str, stype, float(total_capacity), created_at),
            )
            conn.commit()

        return {
            "warehouse_code": code,
            "warehouse_name": name,
            "region": reg,
            "managing_unit": unit_str,
            "storage_type": stype,
            "total_capacity": float(total_capacity),
            "current_utilization": 0.0,
            "utilization_pct": 0.0,
            "created_at": created_at,
        }

    def intake_inventory(
        self,
        inventory_code: str,
        warehouse_code: str,
        item_category: str,
        item_name: str,
        quantity: float,
        unit: str,
        intake_date: str,
        max_storage_months: int,
        unit_cost_vnd: float = 0.0,
        quality_status: str = "PASSED",
    ) -> Dict[str, Any]:
        """
        Record commodity intake into national reserve inventory.
        Calculates rotation deadline based on max allowable storage time (QCVN standard).
        """
        code = inventory_code.strip()
        wh_code = warehouse_code.strip()
        cat = item_category.strip().upper()
        name = item_name.strip()
        unit_str = unit.strip().upper()
        qstatus = quality_status.strip().upper()

        if not code or not name or not unit_str:
            raise ValueError("inventory_code, item_name, and unit cannot be empty.")
        if cat not in VALID_CATEGORIES:
            raise ValueError(f"Invalid item_category '{cat}'. Must be one of: {sorted(VALID_CATEGORIES)}")
        if qstatus not in VALID_QUALITY_STATUSES:
            raise ValueError(f"Invalid quality_status '{qstatus}'. Must be one of: {sorted(VALID_QUALITY_STATUSES)}")
        if quantity <= 0:
            raise ValueError("quantity must be strictly positive.")
        if max_storage_months <= 0:
            raise ValueError("max_storage_months must be strictly positive.")
        if unit_cost_vnd < 0:
            raise ValueError("unit_cost_vnd cannot be negative.")

        try:
            intake_dt = datetime.date.fromisoformat(intake_date.strip())
        except ValueError:
            raise ValueError(f"intake_date must be in YYYY-MM-DD format, got '{intake_date}'.")

        rotation_due = _add_months(intake_dt, max_storage_months).isoformat()
        total_value = float(quantity * unit_cost_vnd)
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT total_capacity, current_utilization FROM reserve_warehouses WHERE warehouse_code = ?", (wh_code,))
            wh = cur.fetchone()
            if not wh:
                raise ValueError(f"Warehouse '{wh_code}' does not exist.")

            new_util = float(wh["current_utilization"]) + float(quantity)
            if new_util > float(wh["total_capacity"]):
                raise ValueError(
                    f"Warehouse capacity exceeded: capacity={wh['total_capacity']}, "
                    f"current={wh['current_utilization']}, requested={quantity}."
                )

            cur.execute("SELECT inventory_code FROM reserve_inventories WHERE inventory_code = ?", (code,))
            if cur.fetchone():
                raise ValueError(f"Inventory item '{code}' already exists.")

            cur.execute(
                """
                INSERT INTO reserve_inventories (
                    inventory_code, warehouse_code, item_category, item_name,
                    quantity, unit, intake_date, max_storage_months,
                    quality_status, unit_cost_vnd, total_value_vnd,
                    rotation_due_date, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    code, wh_code, cat, name, float(quantity), unit_str,
                    intake_dt.isoformat(), int(max_storage_months), qstatus,
                    float(unit_cost_vnd), total_value, rotation_due, created_at,
                ),
            )

            cur.execute(
                "UPDATE reserve_warehouses SET current_utilization = ? WHERE warehouse_code = ?",
                (new_util, wh_code),
            )
            conn.commit()

        return {
            "inventory_code": code,
            "warehouse_code": wh_code,
            "item_category": cat,
            "item_name": name,
            "quantity": float(quantity),
            "unit": unit_str,
            "intake_date": intake_dt.isoformat(),
            "max_storage_months": int(max_storage_months),
            "quality_status": qstatus,
            "unit_cost_vnd": float(unit_cost_vnd),
            "total_value_vnd": total_value,
            "rotation_due_date": rotation_due,
            "warehouse_utilization_now": new_util,
            "created_at": created_at,
        }

    def inspect_inventory_quality(
        self,
        inventory_code: str,
        quality_status: str,
    ) -> Dict[str, Any]:
        """
        Record inspection results of state reserve commodity per QCVN standards.
        """
        code = inventory_code.strip()
        qstatus = quality_status.strip().upper()

        if qstatus not in VALID_QUALITY_STATUSES:
            raise ValueError(f"Invalid quality_status '{qstatus}'. Must be one of: {sorted(VALID_QUALITY_STATUSES)}")

        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT inventory_code, quality_status, item_name FROM reserve_inventories WHERE inventory_code = ?", (code,))
            row = cur.fetchone()
            if not row:
                raise ValueError(f"Inventory item '{code}' not found.")

            cur.execute(
                "UPDATE reserve_inventories SET quality_status = ? WHERE inventory_code = ?",
                (qstatus, code),
            )
            conn.commit()

        return {
            "inventory_code": code,
            "item_name": row["item_name"],
            "previous_status": row["quality_status"],
            "quality_status": qstatus,
            "status_updated": True,
        }

    def allocate_relief(
        self,
        allocation_code: str,
        decision_number: str,
        decision_authority: str,
        purpose: str,
        inventory_code: str,
        beneficiary_locality: str,
        allocated_quantity: float,
        dispatch_date: str,
        requested_quantity: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Execute emergency dispatch & relief allocation of national reserve commodities
        under decision by Prime Minister or authorized Minister.
        Deducts allocated inventory quantity and updates warehouse utilization.
        """
        code = allocation_code.strip()
        dec_no = decision_number.strip()
        auth = decision_authority.strip().upper()
        purp = purpose.strip().upper()
        inv_code = inventory_code.strip()
        beneficiary = beneficiary_locality.strip()

        if not code or not dec_no or not beneficiary:
            raise ValueError("allocation_code, decision_number, and beneficiary_locality cannot be empty.")
        if auth not in VALID_AUTHORITIES:
            raise ValueError(f"Invalid decision_authority '{auth}'. Must be one of: {sorted(VALID_AUTHORITIES)}")
        if purp not in VALID_RELIEF_PURPOSES:
            raise ValueError(f"Invalid purpose '{purp}'. Must be one of: {sorted(VALID_RELIEF_PURPOSES)}")
        if allocated_quantity <= 0:
            raise ValueError("allocated_quantity must be strictly positive.")

        req_qty = float(requested_quantity if requested_quantity is not None else allocated_quantity)
        if req_qty < allocated_quantity:
            req_qty = allocated_quantity

        try:
            disp_dt = datetime.date.fromisoformat(dispatch_date.strip())
        except ValueError:
            raise ValueError(f"dispatch_date must be in YYYY-MM-DD format, got '{dispatch_date}'.")

        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT allocation_code FROM relief_allocations WHERE allocation_code = ?", (code,))
            if cur.fetchone():
                raise ValueError(f"Relief allocation '{code}' already exists.")

            cur.execute(
                """
                SELECT warehouse_code, quantity, unit, unit_cost_vnd, item_name
                FROM reserve_inventories WHERE inventory_code = ?
                """,
                (inv_code,),
            )
            inv = cur.fetchone()
            if not inv:
                raise ValueError(f"Inventory item '{inv_code}' not found.")

            curr_qty = float(inv["quantity"])
            if allocated_quantity > curr_qty:
                raise ValueError(
                    f"Insufficient stock for inventory '{inv_code}': available={curr_qty}, "
                    f"requested_allocation={allocated_quantity}."
                )

            wh_code = inv["warehouse_code"]
            unit_str = inv["unit"]
            unit_cost = float(inv["unit_cost_vnd"])
            replenishment_vnd = float(allocated_quantity * unit_cost)
            rem_qty = curr_qty - float(allocated_quantity)
            rem_val = rem_qty * unit_cost

            cur.execute(
                "SELECT current_utilization FROM reserve_warehouses WHERE warehouse_code = ?",
                (wh_code,),
            )
            wh = cur.fetchone()
            wh_util = max(0.0, float(wh["current_utilization"]) - float(allocated_quantity))

            cur.execute(
                """
                INSERT INTO relief_allocations (
                    allocation_code, decision_number, decision_authority, purpose,
                    inventory_code, beneficiary_locality, requested_quantity,
                    allocated_quantity, unit, dispatch_date, delivery_status,
                    budget_replenishment_vnd, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'DISPATCHED', ?, ?)
                """,
                (
                    code, dec_no, auth, purp, inv_code, beneficiary,
                    req_qty, float(allocated_quantity), unit_str,
                    disp_dt.isoformat(), replenishment_vnd, created_at,
                ),
            )

            cur.execute(
                """
                UPDATE reserve_inventories
                SET quantity = ?, total_value_vnd = ?
                WHERE inventory_code = ?
                """,
                (rem_qty, rem_val, inv_code),
            )

            cur.execute(
                "UPDATE reserve_warehouses SET current_utilization = ? WHERE warehouse_code = ?",
                (wh_util, wh_code),
            )
            conn.commit()

        return {
            "allocation_code": code,
            "decision_number": dec_no,
            "decision_authority": auth,
            "purpose": purp,
            "inventory_code": inv_code,
            "item_name": inv["item_name"],
            "beneficiary_locality": beneficiary,
            "requested_quantity": req_qty,
            "allocated_quantity": float(allocated_quantity),
            "unit": unit_str,
            "dispatch_date": disp_dt.isoformat(),
            "delivery_status": "DISPATCHED",
            "budget_replenishment_vnd": replenishment_vnd,
            "remaining_inventory_quantity": rem_qty,
            "warehouse_utilization_now": wh_util,
            "created_at": created_at,
        }

    def plan_stock_rotation(
        self,
        rotation_code: str,
        inventory_code: str,
        plan_year: int,
        rotation_type: str,
        outgoing_quantity: float,
        replacement_deadline: str,
        realized_proceeds_vnd: float = 0.0,
        reacquisition_budget_vnd: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Schedule statutory stock rotation (xuất đổi hàng/xoay vòng) under Art 45 of Law 22/2012/QH13
        to prevent quality degradation past allowable storage thresholds.
        """
        code = rotation_code.strip()
        inv_code = inventory_code.strip()
        rtype = rotation_type.strip().upper()

        if not code:
            raise ValueError("rotation_code cannot be empty.")
        if rtype not in VALID_ROTATION_TYPES:
            raise ValueError(f"Invalid rotation_type '{rtype}'. Must be one of: {sorted(VALID_ROTATION_TYPES)}")
        if outgoing_quantity <= 0:
            raise ValueError("outgoing_quantity must be strictly positive.")
        if plan_year < 2000 or plan_year > 2100:
            raise ValueError(f"Invalid plan_year '{plan_year}'.")

        try:
            deadline_dt = datetime.date.fromisoformat(replacement_deadline.strip())
        except ValueError:
            raise ValueError(f"replacement_deadline must be in YYYY-MM-DD format, got '{replacement_deadline}'.")

        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT rotation_code FROM rotation_plans WHERE rotation_code = ?", (code,))
            if cur.fetchone():
                raise ValueError(f"Rotation plan '{code}' already exists.")

            cur.execute(
                "SELECT quantity, unit, rotation_due_date, item_name FROM reserve_inventories WHERE inventory_code = ?",
                (inv_code,),
            )
            inv = cur.fetchone()
            if not inv:
                raise ValueError(f"Inventory item '{inv_code}' not found.")

            if outgoing_quantity > float(inv["quantity"]):
                raise ValueError(
                    f"Outgoing quantity exceeds available stock: available={inv['quantity']}, "
                    f"requested_outgoing={outgoing_quantity}."
                )

            cur.execute(
                """
                INSERT INTO rotation_plans (
                    rotation_code, inventory_code, plan_year, rotation_type,
                    outgoing_quantity, replacement_deadline, realized_proceeds_vnd,
                    reacquisition_budget_vnd, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'PLANNED', ?)
                """,
                (
                    code, inv_code, int(plan_year), rtype, float(outgoing_quantity),
                    deadline_dt.isoformat(), float(realized_proceeds_vnd),
                    float(reacquisition_budget_vnd), created_at,
                ),
            )
            conn.commit()

        return {
            "rotation_code": code,
            "inventory_code": inv_code,
            "item_name": inv["item_name"],
            "unit": inv["unit"],
            "plan_year": int(plan_year),
            "rotation_type": rtype,
            "outgoing_quantity": float(outgoing_quantity),
            "replacement_deadline": deadline_dt.isoformat(),
            "rotation_due_date": inv["rotation_due_date"],
            "realized_proceeds_vnd": float(realized_proceeds_vnd),
            "reacquisition_budget_vnd": float(reacquisition_budget_vnd),
            "status": "PLANNED",
            "created_at": created_at,
        }

    def execute_rotation_replenishment(
        self,
        rotation_code: str,
        replenished_quantity: float,
        unit_cost_vnd: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Record completion of stock rotation by replenishing fresh inventory.
        """
        code = rotation_code.strip()
        if replenished_quantity <= 0:
            raise ValueError("replenished_quantity must be strictly positive.")

        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT r.rotation_code, r.inventory_code, r.outgoing_quantity, r.status,
                       i.warehouse_code, i.quantity, i.unit_cost_vnd, i.item_name
                FROM rotation_plans r
                JOIN reserve_inventories i ON r.inventory_code = i.inventory_code
                WHERE r.rotation_code = ?
                """,
                (code,),
            )
            row = cur.fetchone()
            if not row:
                raise ValueError(f"Rotation plan '{code}' not found.")

            inv_code = row["inventory_code"]
            wh_code = row["warehouse_code"]
            current_inv_qty = float(row["quantity"])
            cost = float(unit_cost_vnd if unit_cost_vnd > 0 else row["unit_cost_vnd"])

            new_inv_qty = current_inv_qty + float(replenished_quantity)
            new_inv_val = new_inv_qty * cost

            cur.execute(
                "SELECT current_utilization, total_capacity FROM reserve_warehouses WHERE warehouse_code = ?",
                (wh_code,),
            )
            wh = cur.fetchone()
            new_util = float(wh["current_utilization"]) + float(replenished_quantity)
            if new_util > float(wh["total_capacity"]):
                raise ValueError(f"Replenishment exceeds warehouse capacity: {new_util} > {wh['total_capacity']}.")

            cur.execute(
                "UPDATE rotation_plans SET status = 'COMPLETED' WHERE rotation_code = ?",
                (code,),
            )
            cur.execute(
                """
                UPDATE reserve_inventories
                SET quantity = ?, total_value_vnd = ?, unit_cost_vnd = ?
                WHERE inventory_code = ?
                """,
                (new_inv_qty, new_inv_val, cost, inv_code),
            )
            cur.execute(
                "UPDATE reserve_warehouses SET current_utilization = ? WHERE warehouse_code = ?",
                (new_util, wh_code),
            )
            conn.commit()

        return {
            "rotation_code": code,
            "inventory_code": inv_code,
            "item_name": row["item_name"],
            "replenished_quantity": float(replenished_quantity),
            "updated_inventory_quantity": new_inv_qty,
            "warehouse_utilization_now": new_util,
            "status": "COMPLETED",
        }

    def list_records(
        self,
        record_type: str = "all",
        limit: int = 50,
    ) -> Dict[str, Any]:
        """
        List warehouses, reserve inventories, relief allocations, and rotation plans.
        """
        rtype = record_type.strip().lower()
        lim = max(1, min(limit, 500))
        res: Dict[str, Any] = {}

        with self._get_connection() as conn:
            cur = conn.cursor()
            if rtype in ("warehouses", "all"):
                cur.execute("SELECT * FROM reserve_warehouses ORDER BY warehouse_code ASC LIMIT ?", (lim,))
                res["warehouses"] = [dict(r) for r in cur.fetchall()]

            if rtype in ("inventories", "all"):
                cur.execute("SELECT * FROM reserve_inventories ORDER BY intake_date DESC LIMIT ?", (lim,))
                res["inventories"] = [dict(r) for r in cur.fetchall()]

            if rtype in ("allocations", "all"):
                cur.execute("SELECT * FROM relief_allocations ORDER BY dispatch_date DESC LIMIT ?", (lim,))
                res["allocations"] = [dict(r) for r in cur.fetchall()]

            if rtype in ("rotations", "all"):
                cur.execute("SELECT * FROM rotation_plans ORDER BY created_at DESC LIMIT ?", (lim,))
                res["rotations"] = [dict(r) for r in cur.fetchall()]

        return res

    def get_telemetry_status(self) -> Dict[str, Any]:
        """
        Generate comprehensive strategic telemetry regarding state reserve stockpiles,
        warehouse capacities, relief aid volumes, and impending rotation risks.
        """
        today_iso = datetime.date.today().isoformat()
        in_60_days = (datetime.date.today() + datetime.timedelta(days=60)).isoformat()

        with self._get_connection() as conn:
            cur = conn.cursor()

            cur.execute("SELECT COUNT(*) AS c, SUM(total_capacity) AS cap, SUM(current_utilization) AS util FROM reserve_warehouses")
            wh_row = cur.fetchone()
            wh_count = wh_row["c"] or 0
            total_cap = float(wh_row["cap"] or 0.0)
            total_util = float(wh_row["util"] or 0.0)
            util_rate = round((total_util / total_cap * 100.0), 2) if total_cap > 0 else 0.0

            cur.execute("SELECT COUNT(*) AS c, SUM(total_value_vnd) AS val FROM reserve_inventories")
            inv_row = cur.fetchone()
            inv_count = inv_row["c"] or 0
            total_val = float(inv_row["val"] or 0.0)

            cur.execute(
                """
                SELECT item_category, COUNT(*) AS count, SUM(quantity) AS total_qty, SUM(total_value_vnd) AS total_val
                FROM reserve_inventories
                GROUP BY item_category
                """
            )
            cat_breakdown = {r["item_category"]: {"count": r["count"], "quantity": r["total_qty"], "value_vnd": r["total_val"]} for r in cur.fetchall()}

            cur.execute(
                """
                SELECT COUNT(*) AS c FROM reserve_inventories
                WHERE rotation_due_date <= ?
                """,
                (in_60_days,),
            )
            rotation_urgent_count = cur.fetchone()["c"] or 0

            cur.execute(
                """
                SELECT COUNT(*) AS c FROM reserve_inventories
                WHERE quality_status != 'PASSED'
                """
            )
            substandard_warning_count = cur.fetchone()["c"] or 0

            cur.execute(
                """
                SELECT COUNT(*) AS c, SUM(allocated_quantity) AS qty, SUM(budget_replenishment_vnd) AS comp
                FROM relief_allocations
                """
            )
            rel_row = cur.fetchone()
            relief_count = rel_row["c"] or 0
            relief_qty = float(rel_row["qty"] or 0.0)
            relief_comp_vnd = float(rel_row["comp"] or 0.0)

            cur.execute("SELECT COUNT(*) AS c FROM rotation_plans WHERE status != 'COMPLETED'")
            active_rotations = cur.fetchone()["c"] or 0

        return {
            "total_warehouses": wh_count,
            "total_capacity": total_cap,
            "total_utilized_capacity": total_util,
            "warehouse_utilization_rate_pct": util_rate,
            "total_inventory_items": inv_count,
            "total_reserve_stock_value_vnd": total_val,
            "inventory_by_category": cat_breakdown,
            "urgent_rotations_needed_60d": rotation_urgent_count,
            "substandard_or_warning_items": substandard_warning_count,
            "total_relief_allocations": relief_count,
            "total_relief_quantity_dispatched": relief_qty,
            "budget_replenishment_due_vnd": relief_comp_vnd,
            "active_rotation_plans": active_rotations,
        }
