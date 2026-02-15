# Project Overview & PDR - Algo Trader

## Project Description
Algo Trader là một hệ thống giao dịch tự động (Trading Bot) được xây dựng trên nền tảng Node.js và TypeScript. Bot được thiết kế theo kiến trúc modular, cho phép dễ dàng tích hợp các sàn giao dịch mới, chiến thuật mới và các phương pháp quản lý rủi ro khác nhau.

## Functional Requirements
- **Data Acquisition**: Thu thập dữ liệu nến (OHLCV) từ các sàn giao dịch qua `ExchangeClient` hoặc `MockDataProvider`.
- **Strategy Execution**: Hỗ trợ thực thi nhiều chiến thuật đồng thời hoặc độc lập.
- **Arbitrage Support**:
    - **Cross-Exchange**: So sánh chênh lệch giá (spread) giữa 2 sàn giao dịch khác nhau cho cùng một tài sản.
    - **Triangular**: Khai thác vòng lặp giá giữa 3 cặp tiền tệ (ví dụ: USDT -> BTC -> ETH -> USDT) để tìm lợi nhuận phi rủi ro.
    - **Statistical**: Giao dịch cặp (Pairs Trading) dựa trên độ tương quan và Z-Score để bắt các điểm hồi quy về giá trị trung bình (Mean Reversion).
- **Technical Analysis**: Tích hợp bộ công cụ tính toán thống kê (Standard Deviation, Z-Score, Correlation).
- **Order Management**: Quản lý vòng đời lệnh (Mua, Bán, Theo dõi trạng thái).
- **Risk Management**: Tính toán position size dựa trên số dư và tỷ lệ rủi ro cấu hình.
- **Reporting**: Xuất báo cáo hiệu suất dưới dạng Console hoặc HTML.

## Non-Functional Requirements
- **Performance**: Xử lý tín hiệu và thực thi lệnh với độ trễ thấp.
- **Reliability**: Khả năng tự kết nối lại khi mất mạng hoặc API lỗi.
- **Extensibility**: Interface rõ ràng (`IStrategy`, `IDataProvider`, `IExchange`) để mở rộng.
- **Type Safety**: Sử dụng TypeScript nghiêm ngặt, không dùng `any`.

## Technical Constraints
- Ngôn ngữ: TypeScript.
- Runtime: Node.js.
- Thư viện chính: CCXT, technicalindicators.
- Data format: OHLCV (Open, High, Low, Close, Volume).

## Acceptance Criteria
- Bot có thể khởi chạy và kết nối với sàn giao dịch.
- Các chiến thuật Arbitrage phát hiện được tín hiệu chính xác theo công thức.
- Lệnh được gửi thành công và trừ số dư tương ứng (trong môi trường mock hoặc live).
- Báo cáo HTML được sinh ra sau khi kết thúc backtest hoặc phiên giao dịch.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
