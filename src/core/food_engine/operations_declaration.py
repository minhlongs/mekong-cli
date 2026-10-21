# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Product declaration operations for FoodEngine under Decree 15/2018/NĐ-CP."""

from __future__ import annotations

import datetime
import json
import typing
import uuid

from .constants import FOOD_PRODUCT_CATEGORIES
from .db import get_connection

if typing.TYPE_CHECKING:
    import pathlib


def declare_product_record(
    db_path: pathlib.Path,
    product_name: str,
    product_category: str,
    enterprise_name: str,
    tax_id: str,
    manufacturer_name: str,
    origin_country: str,
    ingredients: list[str],
    shelf_life_months: int,
    lab_test_cert: str,
    gmp_cert_number: str | None = None,
    custom_number: str | None = None,
    metadata: dict[str, typing.Any] | None = None,
) -> dict[str, typing.Any]:
    """Declare or register a food product according to Decree 15/2018/NĐ-CP."""
    category_clean = product_category.strip().upper()
    if category_clean not in FOOD_PRODUCT_CATEGORIES:
        valid_cats = list(FOOD_PRODUCT_CATEGORIES.keys())
        raise ValueError(f"Danh mục thực phẩm không hợp lệ: '{product_category}'. Hỗ trợ: {valid_cats}")

    cat_info = FOOD_PRODUCT_CATEGORIES[category_clean]
    declaration_path = cat_info["declaration_path"]

    if cat_info["gmp_required"] and not gmp_cert_number:
        raise ValueError(
            f"Sản phẩm nhóm {cat_info['name_vi']} bắt buộc phải có Giấy chứng nhận GMP "
            f"theo quy định tại Nghị định 15/2018/NĐ-CP (Điều 28)."
        )

    today_date = datetime.date.today()
    year = today_date.year
    seq = uuid.uuid4().hex[:6].upper()
    if custom_number:
        decl_number = custom_number
    else:
        if declaration_path == "REGISTRATION":
            decl_number = f"{seq}/{year}/ĐKSP"
        else:
            decl_number = f"{seq}/{year}/TCB-MK"

    decl_id = f"decl-{uuid.uuid4().hex[:12]}"
    submission_date = today_date.isoformat()
    approval_date = today_date.isoformat()
    expiry_date = None
    status = "APPROVED" if declaration_path == "REGISTRATION" else "PUBLISHED"

    with get_connection(db_path) as conn:
        conn.execute(
            """
            INSERT INTO food_declarations (
                declaration_id, declaration_number, product_name, product_category,
                declaration_path, enterprise_name, tax_id, manufacturer_name, origin_country,
                ingredients_json, shelf_life_months, lab_test_cert, gmp_cert_number,
                status, submission_date, approval_date, expiry_date, metadata_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                decl_id,
                decl_number,
                product_name.strip(),
                category_clean,
                declaration_path,
                enterprise_name.strip(),
                tax_id.strip(),
                manufacturer_name.strip(),
                origin_country.strip(),
                json.dumps(ingredients, ensure_ascii=False),
                shelf_life_months,
                lab_test_cert.strip(),
                gmp_cert_number.strip() if gmp_cert_number else None,
                status,
                submission_date,
                approval_date,
                expiry_date,
                json.dumps(metadata or {}, ensure_ascii=False),
                datetime.datetime.now(datetime.timezone.utc).isoformat(),
            ),
        )
        conn.commit()

    return {
        "declaration_id": decl_id,
        "declaration_number": decl_number,
        "product_name": product_name,
        "product_category": category_clean,
        "category_name_vi": cat_info["name_vi"],
        "declaration_path": declaration_path,
        "authority": cat_info["authority"],
        "enterprise_name": enterprise_name,
        "status": status,
        "submission_date": submission_date,
        "message": (
            f"Đã đăng ký thành công bản công bố sản phẩm ({declaration_path}) "
            f"với số hiệu {decl_number} gửi cơ quan có thẩm quyền: {cat_info['authority']}."
        ),
    }


__all__ = ["declare_product_record"]
