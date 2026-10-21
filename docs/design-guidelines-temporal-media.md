# Hướng dẫn Thiết kế — Phương tiện Truyền thông Theo Thời gian (TTS + Video)
# Design Guidelines — Temporal Media (TTS + Video)

> **Mục đích / Purpose:** Quy tắc này điều chỉnh phương tiện theo thời gian đã được dựng (lời dọc kịch bản phủ lên video đã kết xuất) — không điều chỉnh giao diện tĩnh.
> This rule governs *composed temporal media* — scripted narration laid over rendered video. It does **not** govern static UI.

---

# PHẦN 1 — TIẾNG VIỆT

## 1. Vì sao quy tắc này tồn tại

Mô hình chấm điểm 9 trục trong `src/design_intelligence/scoring.py` không có ô dành cho kênh lời nói tuần tự. `_AXIS_FOR_CATEGORY` gom MOTION, COMPONENTS, INTERACTION về trục `interaction`, và CONTENT về trục `hierarchy` — cả hai đều là mô hình không gian, dựa trên trang. TTS bổ sung một kênh *tuần tự và bằng lời*: người nghe bị buộc phải theo trình tự thời gian và không thể quét ngẫu nhiên như đọc trang.

Quy tắc này **không** ghi đè bất kỳ thứ bậc hay trục hiện có. Nó chỉ tuyên bố kênh nào dẫn dắt trong từng cảnh — đây là khái niệm mà mã hiện tại chưa có, và ở đây được giới thiệu.

## 2. Khai báo kênh dẫn dắt (RULE-P1 — bắt buộc)

Mỗi cảnh đã kết xuất **PHẢI** tuyên bố đúng **một** trong ba giá trị, và khai báo đó **PHẢI** được ghi nhận trên yêu cầu kết xuất. Trường tự nhiên là `leading_channel` trên `VideoRenderRequest`, đặt cạnh `script` và `avatar_id`. Không có giá trị mặc định ngầm: không khai báo là lỗi, không phải "mặc định VOICE-LEADING".

| Giá trị | Định nghĩa |
|---|---|
| `VOICE-LEADING` | Lời dọc mang ý nghĩa. Hình ảnh chỉ có tính chất không khí và **không được** là điều kiện bắt buộc để hiểu được audio. Kiểm thử: nghe với màn hình tắt, vẫn đủ toàn bộ nội dung. |
| `IMAGE-LEADING` | Hình ảnh mang ý nghĩa. Lời nói chỉ là bình luận và cảnh **phải** vẫn đứng vững khi tắt tiếng. Kiểm thử: xem với âm lượng bằng 0. |
| `DUAL-LOCK` | Cả hai cố ý dư thừa. Chỉ cho phép ở chỗ sự dư thừa **chính là** mục đích: một con số quyết định duy nhất, tổng tiền hóa đơn, mốc thời hạn pháp lý. |

## 3. Trần DUAL-LOCK (RULE-P2 — bắt buộc, định lượng)

Tối đa **20%** cảnh trong một lần kết xuất được phép là `DUAL-LOCK`. Đây là trần cứng, không phải khuyến nghị.

20% là quyết định thiết kế đã được phê duyệt và được ghi nhận tại đây. Lý do: sự dư thừa kéo dài đọc như nói chuyện với người nghe bằng giọng hạ cấp và phá hủy mật độ thông tin — khán giả bỏ qua cả hai kênh thay vì nghe một kênh trọn vẹn.

## 4. Hợp đồng phụ đề (RULE-P3)

Khi `subtitles_enabled` là `true` (mặc định hiện tại):

- Phụ đề mang **nguyên văn** lời dọc. Không diễn giải lại, không rút gọn thành từ khóa.
- Chữ trên màn hình mang thứ mà audio **không** nói — tên biểu đồ, đơn vị, số liệu tham chiếu, nguồn trích dẫn.
- Nếu cùng một từ xuất hiện trong audio **và** trong một phần tử chữ burned-in, đó là một DUAL-LOCK ngoài ý muốn. Nó vẫn bị tính vào trần 20% của RULE-P2.

## 5. Ngăn "khóa khuôn mặt" (RULE-P4)

Avatar trình bày là mặc định (`avatar_id="sophia-anchor-vi-01"`), nên một khuôn mặt nói liên tục **luôn** xuất hiện trừ khi thiết kế tắt nó. Khuôn mặt liên tục chiếm chú ý và bỏ đói nội dung thật — đây là lỗi chất lượng phổ biến nhất trong video có avatar.

- Trong cảnh `IMAGE-LEADING`: avatar **không được** chiếm quá **50%** diện tích khung hình. Ngưỡng 50% là quyết định thiết kế đã được phê duyệt.
- Trong cảnh `VOICE-LEADING`: khuôn mặt chỉ được giữ chú ý trong lúc chính nó mang ý nghĩa. Khi audio đang mang nội dung, khuôn mặt không được cạnh tranh với nó.
- Khi chủ thể là biểu đồ, hóa đơn, tài liệu hoặc bảng số liệu: avatar **phải** lùi lại (giảm tỷ lệ hoặc ra ngoài khung) trong suốt thời gian nó được trình chiếu.

## 6. Trung thực mức bằng chứng (RULE-P5)

Mọi kết luận thuộc quy tắc này **phải** nêu rõ mức của nó, và không được nâng cấp mức để đạt kết quả đẹp hơn:

| Mức | Phạm vi |
|---|---|
| OBJECTIVE | Kiểm định được từ yêu cầu kết xuất + kịch bản + danh sách cảnh. Định nghĩa, có thể chạy lại. |
| HEURISTIC | Cần một bộ phán xét. Phải mang giá trị tin cậy (confidence), không bao giờ là một "pass" giả. |
| OPINION | Cần một khung hình đã kết xuất. Không được khẳng định khi chưa có. |

Đây khớp với hợp đồng hiện có của repo — trường `detection_method` trong `gates.yaml`: `automatic` = OBJECTIVE, `heuristic` = HEURISTIC kèm confidence, `visual` = OPINION cần ảnh chụp. Không làm suy yếu hợp đồng này.

## 7. Thực thi

Ba gate sau lần lượt ứng với P1, P2, P4. Cả ba gộp vào trục `interaction` sẵn có qua category MOTION — **không** mở thêm trục mới.

| Gate id | Mức đạt được thật | Trượt khi | Phạm vi |
|---|---|---|---|
| `temporal-leading-channel-declared` | OBJECTIVE | Yêu cầu kết xuất có `script` nhưng không có khai báo kênh dẫn dắt | Mọi `VideoRenderRequest` |
| `dual-lock-capped` | OBJECTIVE | Số cảnh `DUAL-LOCK` vượt 20% danh sách cảnh | Một lần kết xuất |
| `no-face-lock` | OBJECTIVE **nếu** danh sách cảnh cung cấp dữ liệu diện tích khung / vị trí; nếu không, HEURISTIC và **phải** báo cáo là UNVERIFIED, không được ghi pass | Avatar vượt ngưỡng 50% trong cảnh `IMAGE-LEADING`, hoặc khuôn mặt lấp đầy khung trong khi chủ thể là biểu đồ / tài liệu | Mọi cảnh có chủ thể là biểu đồ hoặc tài liệu |

Trạng thái thực thi sau khi đã chạy: cả ba gate đã được khai báo trong `src/design_intelligence/knowledge/gates.yaml` ở khối TEMPORAL MEDIA (category `MOTION`, severity `medium` cho hai gate đầu và `high` cho gate thứ ba) **và** đã đăng ký hàm trong `CHECKS` của `src/design_intelligence/checks.py` — nên chúng chạy định nghĩa được ngay hôm nay. `VideoRenderRequest` nay đã có `leading_channel` (bắt buộc — không mặc định ngầm) và `scenes`, và `src/services/sophia_temporal_media.py` giữ hợp đồng này, nên các gate đọc dữ liệu thật thay vì chuỗi viết tay.

Hai giới hạn được ghi nhận thay vì giấu đi:

- Gate 58 và 59 chỉ đọc được văn bản của yêu cầu kết xuất và danh sách cảnh. Chúng không thể xem một bức ảnh, nên phạm vi đúng là đúng những trường đã khai báo — không mở rộng thêm.
- Gate 60 đọc được `avatar_scale` — nay là trường khai báo thật — nên nửa "diện tích" của nó là OBJECTIVE và kiểm định được tại ngưỡng 50%. Phần còn lại không đo được từ văn bản là nửa "quan sát" của lỗi: ánh mắt người xem có thực sự bị khóa vào khuôn mặt hay không. Phần đó vẫn là OPINION, cần một khung hình đã kết xuất, và không bao giờ được khai từ phân tích tĩnh.

Theo RULE-P5, đây là lý do gate khai báo `automatic` cho phần dữ liệu với tới, và nửa cảm nhận được để lại ở OPINION thay vì cải trang thành một lần pass định nghĩa.

## 8. Mã và quy tắc liên quan

- `src/services/sophia_video_models.py` — `VideoRenderRequest`: nơi `leading_channel` được thêm vào.
- `src/services/sophia_video_pipeline.py`, `src/services/sophia_video_providers.py` — nơi dựng và kết xuất cảnh; nơi danh sách cảnh được hình thành.
- `src/design_intelligence/knowledge/gates.yaml` — khối TEMPORAL MEDIA hiện có (id 58, 59, 60).
- `src/design_intelligence/checks.py` — `CHECKS: dict[str, Check]`, kiểm định OBJECTIVE.
- `docs/design-intelligence.md` — mô hình chấm điểm và hợp đồng mức bằng chứng.

---

# PART 2 — ENGLISH

## 1. Why this rule exists

The 9-axis scoring model in `src/design_intelligence/scoring.py` has no slot for a sequential verbal channel. `_AXIS_FOR_CATEGORY` maps MOTION, COMPONENTS, and INTERACTION to the `interaction` axis, and CONTENT to `hierarchy` — both are spatial, page-shaped models. TTS adds a *sequential and verbal* channel: the listener is forced along a timeline and cannot scan randomly the way a page is read.

This rule does **not** override any existing hierarchy or axis. It declares which channel leads in each scene — a concept the codebase does not yet have, introduced here.

## 2. Leading-channel declaration (RULE-P1 — normative)

Every rendered scene **MUST** declare exactly **one** of three values, and the declaration **MUST** be recorded on the render request. The natural field is `leading_channel` on `VideoRenderRequest`, alongside `script` and `avatar_id`. There is no implicit default: no declaration is a defect, not "defaults to VOICE-LEADING".

| Value | Definition |
|---|---|
| `VOICE-LEADING` | Narration carries the meaning. Picture is atmospheric and must **not** be required to understand the audio. Test: listen with the screen dark; the content still stands complete. |
| `IMAGE-LEADING` | The visual carries the meaning. Voice is commentary and the scene **MUST** still work muted. Test: watch with volume at zero. |
| `DUAL-LOCK` | Both intentionally redundant. Permitted only where redundancy **is** the point — a single decisive statistic, an invoice total, a legal deadline. |

## 3. DUAL-LOCK cap (RULE-P2 — normative, quantitative)

At most **20%** of scenes in one render may be `DUAL-LOCK`. This is a hard cap, not guidance.

The 20% figure is an approved design decision, recorded here. Rationale: sustained redundancy reads as patronizing and destroys information density — the audience skips both channels instead of attending to one intact.

## 4. Captions contract (RULE-P3)

When `subtitles_enabled` is `true` (the current default):

- Captions carry the narration **verbatim**. No paraphrasing, no keyword extraction.
- On-screen text carries what the audio does **not** say — chart names, units, reference figures, citation sources.
- If the same words appear in the audio **and** as a burned-in text element, that is an accidental DUAL-LOCK. It still counts against the 20% cap of RULE-P2.

## 5. No-face-lock guard (RULE-P4)

A presenter avatar is the default (`avatar_id="sophia-anchor-vi-01"`), so a speaking face is **always** present unless a design turns it off. A continuously present speaking face captures attention and starves the actual content — the commonest quality failure in avatar video.

- In `IMAGE-LEADING` scenes the avatar must **not** occupy more than **50%** of frame area. The 50% threshold is an approved design decision.
- In `VOICE-LEADING` scenes the face must hold attention only while it is itself the meaning carrier. While the audio carries content, the face must not compete with it.
- When a chart, invoice, document, or table is the subject, the avatar must recede — reduced scale, or off-frame — for the entire duration it is shown.

## 6. Evidence-tier honesty (RULE-P5)

Every finding under this rule **MUST** state its tier, and must not be upgraded to reach a tidier result:

| Tier | Scope |
|---|---|
| OBJECTIVE | Checkable from the render request + script + scene list. Deterministic, re-runnable. |
| HEURISTIC | Needs a judge. Must carry confidence; never a fake pass. |
| OPINION | Needs a rendered frame. Never claimed without one. |

This matches the repo's existing contract — the `detection_method` field in `gates.yaml`: `automatic` = OBJECTIVE, `heuristic` = HEURISTIC with confidence, `visual` = OPINION requiring a screenshot. Do not weaken that contract.

## 7. Enforcement

The three gates below correspond to P1, P2, and P4. All three fold into the existing `interaction` axis via the MOTION category — **no** new axis is introduced.

| Gate id | Tier honestly achieved | Fails when | Scope |
|---|---|---|---|
| `temporal-leading-channel-declared` | OBJECTIVE | A render request carries a `script` but no leading-channel declaration | Every `VideoRenderRequest` |
| `dual-lock-capped` | OBJECTIVE | `DUAL-LOCK` scenes exceed 20% of the scene list | One render |
| `no-face-lock` | OBJECTIVE where the scene list gives frame-area/placement data; otherwise HEURISTIC and **MUST** be reported UNVERIFIED, never passed | Avatar area exceeds the 50% threshold in an `IMAGE-LEADING` scene, or the face fills the frame while the subject is a figure / document | Every scene whose subject is a figure or document |

Enforcement status after execution: all three gates are declared in `src/design_intelligence/knowledge/gates.yaml` under the TEMPORAL MEDIA block (category `MOTION`, severity `medium` for the first two and `high` for the third) **and** registered in `CHECKS` in `src/design_intelligence/checks.py`, so they run deterministically today. `VideoRenderRequest` carries `leading_channel` (required — no implicit default) and `scenes`, and `src/services/sophia_temporal_media.py` owns the contract, so the gates read real data rather than hand-written payloads.

Two limits are recorded rather than hidden:

- Gates 58 and 59 operate on the render-request/scene payload text. They cannot inspect a picture, so their scope is exactly the declared fields — no more.
- Gate 60 reads `avatar_scale`, which is now a real declared field, so its *area* half is OBJECTIVE and checkable at the 50 percent boundary. What remains unmeasurable from text is the *watching* half of the failure — whether a viewer's eyes actually lock on the face. That stays OPINION and needs a rendered frame; it is never claimed from static text.

Under RULE-P5 this is why the gate is declared `automatic` for the part its data reaches, and why the perceptual half is left to OPINION rather than dressed up as a deterministic pass.

## 8. Related code / related rules

- `src/services/sophia_video_models.py` — `VideoRenderRequest`: where `leading_channel` is added.
- `src/services/sophia_video_pipeline.py`, `src/services/sophia_video_providers.py` — where scenes are composed and rendered; where the scene list is formed.
- `src/design_intelligence/knowledge/gates.yaml` — the existing TEMPORAL MEDIA block (ids 58, 59, 60).
- `src/design_intelligence/checks.py` — `CHECKS: dict[str, Check]`, OBJECTIVE checks.
- `docs/design-intelligence.md` — the scoring model and the evidence-tier contract.
