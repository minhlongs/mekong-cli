"""Vietnamese Mobile 1-Tap Approval Card HTML (<15KB) & Zalo/LarkSuite Interactive Card Builders."""
from __future__ import annotations

from html import escape as html_escape
import json
from typing import Any

from src.opc.accounting_draft import DRAFT_STATUS_PENDING_TVAN


def build_owner_notification_cards(
    *,
    run_id: str,
    client_name: str,
    project_title: str,
    total_amount_vnd: int,
    action_digest: str,
    card_url: str,
    vietqr_memo: str,
) -> dict[str, Any]:
    """Build Zalo OA & LarkSuite interactive notification payloads bound to payload_sha256."""
    amount_fmt = f"{int(total_amount_vnd):,} VNĐ".replace(",", ".")
    short_sha = action_digest[:16]
    summary_vi = (
        f"[MEKONG PILOT A] Báo giá nháp cho {client_name}: {project_title} — "
        f"Tổng: {amount_fmt} | Nội dung CK: {vietqr_memo} | SHA-256: {short_sha}..."
    )
    return {
        "zalo_oa_card": {
            "recipient_role": "shop_owner",
            "message": {
                "attachment": {
                    "type": "template",
                    "payload": {
                        "template_type": "request_user_info_or_action",
                        "elements": [
                            {
                                "title": f"Duyệt báo giá 1 chạm — {amount_fmt}",
                                "subtitle": f"Khách: {client_name} | Dự án: {project_title} | CK: {vietqr_memo}",
                            }
                        ],
                        "buttons": [
                            {
                                "title": "Mở Thẻ Duyệt & Gửi VietQR",
                                "type": "oa.open.url",
                                "payload": {"url": card_url},
                            }
                        ],
                    },
                }
            },
            "payload_sha256": action_digest,
        },
        "larksuite_card": {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {"tag": "plain_text", "content": f"🟢 Duyệt Báo Giá Zalo — {amount_fmt}"},
                    "template": "green",
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {"tag": "lark_md", "content": summary_vi},
                    },
                    {
                        "tag": "action",
                        "actions": [
                            {
                                "tag": "button",
                                "text": {"tag": "plain_text", "content": "Duyệt & Gửi Zalo + VietQR"},
                                "type": "primary",
                                "url": card_url,
                                "value": {
                                    "run_id": run_id,
                                    "decision": "approve",
                                    "action_digest": action_digest,
                                },
                            },
                            {
                                "tag": "button",
                                "text": {"tag": "plain_text", "content": "Chuyển Chat Tay Zalo OA"},
                                "type": "default",
                                "url": card_url,
                                "value": {
                                    "run_id": run_id,
                                    "decision": "handoff",
                                    "action_digest": action_digest,
                                },
                            },
                        ],
                    },
                ],
            },
        },
    }


def render_mobile_approval_card_html(
    *,
    run_id: str,
    status: str,
    client_name: str,
    project_title: str,
    customer_notes: str,
    line_items: list[dict[str, Any]],
    citations: list[dict[str, Any]],
    total_amount_vnd: int,
    action_digest: str,
    vietqr_memo: str,
    window_remaining_hours: float,
    tenant_id: str = "default",
    card_sig: str = "",
) -> str:
    """Render self-contained <15KB Vietnamese mobile HTML card for 10-30s owner 1-tap approval."""
    esc_run = html_escape(run_id[:64])
    esc_status = html_escape(status[:40])
    esc_client = html_escape(client_name[:120])
    esc_title = html_escape(project_title[:160])
    clipped_notes = (customer_notes or "(Đã ẩn danh thông tin nhạy cảm theo Nghị định 13/2023)")[:400]
    esc_notes = html_escape(clipped_notes)
    esc_memo = html_escape(vietqr_memo[:80])
    esc_digest = html_escape(action_digest[:80])
    fmt_total = f"{int(total_amount_vnd):,}".replace(",", ".")

    item_rows: list[str] = []
    shown_items = line_items[:12]
    for it in shown_items:
        svc = html_escape(str(it.get("service", it.get("item_name", "dịch vụ")))[:48])
        qty = html_escape(str(it.get("hours", it.get("quantity", 1)))[:12])
        rate_i = int(float(str(it.get("rate", it.get("unit_price_vnd", 0)))))
        sub_i = int(float(str(it.get("subtotal", it.get("line_subtotal_vnd", 0)))))
        rate_s = f"{rate_i:,}".replace(",", ".")
        sub_s = f"{sub_i:,}".replace(",", ".")
        item_rows.append(
            f"<li><strong>{svc}</strong>: {qty} × {rate_s}đ = <b>{sub_s}đ</b></li>"
        )
    if len(line_items) > 12:
        item_rows.append(f"<li><em>(+{len(line_items) - 12} hạng mục khác trong tổng tiền)</em></li>")
    items_html = "".join(item_rows) or "<li>Chưa có dòng hàng hóa</li>"

    cit_rows: list[str] = []
    for cit in citations[:4]:
        fn = html_escape(str(cit.get("field_name", "source_span"))[:32])
        qt = html_escape(str(cit.get("source_quote", ""))[:70])
        sc = int(cit.get("start_char", 0))
        ec = int(cit.get("end_char", 0))
        cit_rows.append(f"<li><code>{fn}</code>: &ldquo;{qt}&rdquo; <span>[{sc}..{ec}]</span></li>")
    cits_html = "".join(cit_rows) or "<li>Trích xuất tất định từ bảng giá chuẩn</li>"

    js_cfg = json.dumps({"runId": run_id, "digest": action_digest, "tenantId": tenant_id, "sig": card_sig}).replace("</", "<\\/")
    disabled_attr = "" if status in ("pending_approval", "revise_requested") and window_remaining_hours > 0 else "disabled"

    return (
        "<!doctype html><html lang='vi'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<meta name='referrer' content='no-referrer'>"
        f"<title>Mekong Pilot A — Duyệt Báo Giá {esc_run}</title>"
        "<style>"
        "body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f4f7f5;color:#102a1d;margin:0;padding:12px}"
        ".card{max-width:480px;margin:0 auto;background:#fff;border:1px solid #cce3d6;border-radius:14px;padding:16px;box-shadow:0 4px 14px rgba(0,0,0,.05)}"
        ".badge{display:inline-block;padding:4px 8px;border-radius:99px;font-size:12px;font-weight:600;background:#e6f6ec;color:#0d6832}"
        ".warn{background:#fff4e5;color:#8a4b00}"
        "h1{font-size:17px;margin:8px 0 4px}p,li{font-size:14px;line-height:1.45}"
        ".box{background:#f8faf9;border:1px solid #e2ece6;border-radius:10px;padding:10px;margin:10px 0}"
        ".tot{font-size:20px;font-weight:700;color:#0b5d2b}"
        "button{width:100%;padding:13px;border:0;border-radius:10px;font-size:15px;font-weight:700;cursor:pointer;margin-top:8px}"
        ".btn-ok{background:#0d7a3a;color:#fff}.btn-ok:disabled{background:#9eb8a8;cursor:not-allowed}"
        ".btn-ho{background:#f1f5f3;color:#1d3b2a;border:1px solid #c5d6cc}"
        "code{font-size:12px;background:#eef3f0;padding:2px 4px;border-radius:4px;word-break:break-all}"
        "#msg{margin-top:10px;font-size:14px;font-weight:600}"
        "</style></head><body><main class='card'>"
        f"<div><span class='badge'>PILOT A • ZALO OA 48H ({window_remaining_hours:.1f}g)</span> "
        f"<span class='badge warn'>{DRAFT_STATUS_PENDING_TVAN}</span></div>"
        f"<h1>Duyệt Báo Giá 1 Chạm — {esc_client}</h1>"
        f"<p>Mã phiên: <code>{esc_run}</code> • Trạng thái: <b>{esc_status}</b></p>"
        f"<div class='box'><strong>Tin nhắn khách ({esc_title}):</strong><p>{esc_notes}</p></div>"
        f"<div class='box'><strong>Bảng tính tất định (100% số học):</strong><ul>{items_html}</ul>"
        f"<div class='tot'>Tổng VietQR: {fmt_total} VNĐ</div>"
        f"<p>Nội dung CK gắn đơn: <code>{esc_memo}</code></p></div>"
        f"<div class='box'><strong>Trích dẫn nguồn (source_span):</strong><ul>{cits_html}</ul></div>"
        f"<p>Chứng từ kế toán: <b>NHÁP ({DRAFT_STATUS_PENDING_TVAN} — MISA / Sapo)</b><br>"
        f"Khóa chống sửa đổi SHA-256: <code>{esc_digest}</code></p>"
        f"<button id='bOk' class='btn-ok' {disabled_attr} onclick=\"sendDecide('approve')\">"
        "✅ DUYỆT &amp; GỬI BÁO GIÁ + VIETQR</button>"
        f"<button id='bHo' class='btn-ho' {disabled_attr} onclick=\"sendDecide('handoff')\">"
        "👤 CHUYỂN NHÂN VIÊN CHAT TAY (ZALO OA MANAGER)</button>"
        "<p><a href='#' onclick=\"dlDraft('csv');return false\">Tải nháp MISA CSV</a> • "
        "<a href='#' onclick=\"dlDraft('xml');return false\">Tải nháp MISA XML</a></p>"
        "<div id='msg' role='status'></div>"
        f"<script>const CFG={js_cfg};"
        "if(window.history&&window.history.replaceState){const u=new URL(window.location.href);"
        "u.searchParams.delete('sig');window.history.replaceState(null,'',u.pathname+u.search);}"
        "async function dlDraft(fmt){const m=document.getElementById('msg');"
        "const r=await fetch('/v1/opc/pilot-a/draft-export/'+encodeURIComponent(CFG.runId)"
        "+'?fmt='+encodeURIComponent(fmt)+'&tenant_id='+encodeURIComponent(CFG.tenantId),"
        "{headers:{'X-Card-Sig':CFG.sig},referrerPolicy:'no-referrer'});"
        "if(!r.ok){m.textContent='Từ chối tải nháp: '+r.status;return;}"
        "const b=await r.blob();const u=URL.createObjectURL(b);const a=document.createElement('a');"
        "a.href=u;a.download=CFG.runId+'.'+fmt;a.click();URL.revokeObjectURL(u);}"
        "async function sendDecide(d){const m=document.getElementById('msg');m.textContent='Đang xử lý...';"
        "const r=await fetch('/v1/opc/pilot-a/decide',{method:'POST',"
        "headers:{'Content-Type':'application/json','X-Card-Sig':CFG.sig},referrerPolicy:'no-referrer',"
        "body:JSON.stringify({run_id:CFG.runId,tenant_id:CFG.tenantId,decision:d,action_digest:CFG.digest,card_sig:CFG.sig})});"
        "const j=await r.json();if(r.ok){m.textContent='Đã xử lý: '+(j.status||d);document.getElementById('bOk').disabled=true;"
        "document.getElementById('bHo').disabled=true;}else{m.textContent='Từ chối an toàn: '+JSON.stringify(j.detail||j);}}"
        "</script></main></body></html>"
    )
