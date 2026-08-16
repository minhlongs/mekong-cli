# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""VietQR data string generator — pure computation, zero external deps."""
from __future__ import annotations
import logging
logger = logging.getLogger(__name__)
_PAYLOAD_FORMAT_INDICATOR = "000201"
_SERVICE_ID = "0010A00000072701"
_MERCHANT_ACCOUNT_TAG = "38"
_GUI_TAG = "00"
_BIN_TAG = "01"
_ACCOUNT_TAG = "02"
_CURRENCY_TAG = "53"
_COUNTRY_TAG = "58"
_CRC_TAG = "6304"
_VND = "704"
_VN = "VN"
def _crc16_ccitt(data: str) -> str:
    crc = 0xFFFF
    for ch in data.encode("ascii"):
        crc ^= ch << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
            crc &= 0xFFFF
    return f"{crc:04X}"
def _tlv(tag: str, value: str) -> str:
    return f"{tag}{len(value):02d}{value}"
def build_qr_payload(bin_code: str, account: str, account_name: str, amount_vnd: int = 0, memo: str = "") -> str:
    merchant = _tlv(_GUI_TAG, _SERVICE_ID) + _tlv(_BIN_TAG, bin_code) + _tlv(_ACCOUNT_TAG, account)
    merchant_field = _tlv(_MERCHANT_ACCOUNT_TAG, merchant)
    parts = [_PAYLOAD_FORMAT_INDICATOR, merchant_field]
    if amount_vnd and amount_vnd > 0:
        parts.append(_tlv(_CURRENCY_TAG, _VND) + _tlv(_CRC_TAG, ""))
    parts.append(_tlv(_COUNTRY_TAG, _VN))
    payload = "".join(parts)
    if len(memo) > 1:
        payload = payload + _tlv("62", _tlv("01", memo))
    checksum = _crc16_ccitt(payload + _CRC_TAG)
    return payload + _CRC_TAG + checksum
