"""
VietQR API client — Tạo QR code thanh toán cho 40+ ngân hàng VN.
API docs: https://www.vietqr.io/danh-sach-api
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Optional

try:
    import requests
except ImportError:
    requests = None  # type: ignore

VIETQR_API = "https://api.vietqr.io/v2"

SUPPORTED_BANKS = {
    "VCB": "Vietcombank",
    "TCB": "Techcombank",
    "ACB": "ACB",
    "MB": "MB Bank",
    "BIDV": "BIDV",
    "VTB": "VietinBank",
    "AGR": "Agribank",
    "VPB": "VPBank",
    "STB": "Sacombank",
    "HDB": "HDBank",
    "TPB": "TPBank",
    "MSB": "MSB",
    "CAKE": "CAKE by VPBank",
    "UBANK": "Ubank by VPBank",
    "SEABANK": "SeABank",
    "OCB": "OCB",
    "SHB": "SHBank",
    "VIB": "VIB",
    "BAB": "BacABank",
    "VCCB": "Bản Việt",
}


@dataclass
class QRResult:
    qr_code: str  # base64 PNG
    qr_data_url: str  # data:image/png;base64,...
    payment_link: str
    bank_id: str
    account_no: str
    amount: int
    description: str

    def to_summary(self) -> str:
        bank_name = SUPPORTED_BANKS.get(self.bank_id, self.bank_id)
        return (
            f"=== VIETQR THANH TOÁN ===\n"
            f"Ngân hàng:  {bank_name} ({self.bank_id})\n"
            f"Số TK:      {self.account_no}\n"
            f"Số tiền:    {int(self.amount):,} đ\n"
            f"Nội dung:   {self.description}\n\n"
            f"Link QR: {self.payment_link}\n"
            f"(Scan bằng app ngân hàng hoặc ví điện tử)"
        ).replace(",", ".")


class VietQRClient:
    """Client cho VietQR API."""

    def __init__(
        self,
        client_id: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> None:
        self.client_id = client_id or os.getenv("VIETQR_CLIENT_ID", "")
        self.api_key = api_key or os.getenv("VIETQR_API_KEY", "")

    def _headers(self) -> dict[str, str]:
        return {
            "x-client-id": self.client_id,
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
        }

    def generate_qr(
        self,
        bank_id: str,
        account_no: str,
        amount: int,
        description: str,
        account_name: str = "",
    ) -> QRResult:
        """Tạo QR code VietQR."""
        if requests is None:
            raise ImportError("requests not installed: pip install requests")

        import requests as req
        payload = {
            "accountNo": account_no,
            "accountName": account_name,
            "acqId": self._get_bank_bin(bank_id),
            "amount": amount,
            "addInfo": description[:25],  # max 25 chars
            "format": "text",
            "template": "compact",
        }
        resp = req.post(
            f"{VIETQR_API}/generate",
            json=payload,
            headers=self._headers(),
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json().get("data", {})
        qr_code = data.get("qrCode", "")
        return QRResult(
            qr_code=qr_code,
            qr_data_url=f"data:image/png;base64,{qr_code}" if qr_code else "",
            payment_link=data.get("qrDataURL", ""),
            bank_id=bank_id,
            account_no=account_no,
            amount=amount,
            description=description,
        )

    def list_banks(self) -> list[dict[str, Any]]:
        """Lấy danh sách ngân hàng hỗ trợ."""
        if requests is None:
            raise ImportError("requests not installed")
        import requests as req
        resp = req.get(f"{VIETQR_API}/banks", headers=self._headers(), timeout=10)
        resp.raise_for_status()
        return resp.json().get("data", [])

    @staticmethod
    def _get_bank_bin(bank_id: str) -> str:
        """Map bank ID to BIN (Bank Identification Number)."""
        # Common bank BINs
        bins = {
            "VCB": "970436",
            "TCB": "970407",
            "ACB": "970416",
            "MB": "970422",
            "BIDV": "970418",
            "VTB": "970415",
            "AGR": "970405",
            "VPB": "970432",
            "STB": "970403",
            "HDB": "970437",
            "TPB": "970423",
            "MSB": "970426",
            "OCB": "970448",
            "SHB": "970443",
            "VIB": "970441",
        }
        return bins.get(bank_id.upper(), bank_id)

    def is_configured(self) -> bool:
        return bool(self.client_id and self.api_key)


def format_vnd(amount: int) -> str:
    return f"{amount:,} đ".replace(",", ".")
