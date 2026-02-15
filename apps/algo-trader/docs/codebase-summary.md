# Codebase Summary - Algo Trader

## Overview
Algo Trader là một modular trading bot được thiết kế để thực thi các chiến thuật giao dịch tự động. Hệ thống hỗ trợ nhiều loại chiến thuật từ các chỉ báo kỹ thuật truyền thống (RSI, SMA) đến các chiến thuật Arbitrage phức tạp.

## Project Structure
- `src/core/`: Chứa các thành phần cốt lõi của bot (`BotEngine`, `RiskManager`, `OrderManager`).
- `src/strategies/`: Chứa các triển khai chiến thuật giao dịch.
- `src/interfaces/`: Định nghĩa các contracts cho hệ thống.
- `src/data/`: Các data providers (`MockDataProvider`).
- `src/execution/`: Xử lý tương tác với các sàn giao dịch (`ExchangeClient`).
- `src/analysis/`: Các công cụ tính toán chỉ báo kỹ thuật (`Indicators`).
- `src/reporting/`: Các công cụ báo cáo và phân tích hiệu suất.
- `src/ui/`: Giao diện dòng lệnh (CLI).

## Key Components
- **BotEngine**: Điều phối luồng dữ liệu từ `IDataProvider` qua `IStrategy` đến `IExchange`.
- **RiskManager**: Quản lý rủi ro và tính toán khối lượng lệnh dựa trên số dư khả dụng.
- **OrderManager**: Theo dõi và quản lý trạng thái các lệnh (Pending, Executed, Canceled).
- **StrategyLoader**: Tải linh hoạt các chiến thuật từ file cấu hình.
- **Indicators**: Thư viện tính toán toán học/tài chính tùy chỉnh (SMA, RSI, StdDev, Z-Score, Correlation).

## Implementation Details: Arbitrage Strategies
Hệ thống đã triển khai đầy đủ 3 chiến thuật Arbitrage cốt lõi:
1. **Cross-Exchange Arbitrage** (`src/strategies/CrossExchangeArbitrage.ts`):
   - So sánh `candle.close` với `metadata.exchangeBPrice`.
   - Ngưỡng kích hoạt mặc định: 0.1% spread.
2. **Triangular Arbitrage** (`src/strategies/TriangularArbitrage.ts`):
   - Tính toán tỷ giá chéo Forward/Backward qua 3 cặp tiền.
   - Ngưỡng lợi nhuận mặc định: 0.05% per loop.
3. **Statistical Arbitrage** (`src/strategies/StatisticalArbitrage.ts`):
   - Theo dõi tương quan giữa 2 tài sản.
   - Sử dụng Lookback Period = 100 nến để tính Z-Score.
   - Entry: Z-Score > 2.0 hoặc < -2.0. Exit: Z-Score < 0.5.

## Tech Stack
- TypeScript
- Node.js
- CCXT (Exchange connectivity)
- TechnicalIndicators (Math/Finance indicators)
- Jest (Testing framework)

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
