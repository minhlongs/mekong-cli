"""
Mekong IDE - vnstock MCP Server

Wraps the vnstock3 library to expose Vietnamese stock financial data
as MCP tools callable by the Rust Orchestrator.

Transport: stdio (default) or HTTP via --http flag
"""

import sys
import json
import argparse
from typing import Any

import mcp.server.stdio
import mcp.types as types
from mcp.server import Server
from mcp.server.models import InitializationOptions

try:
    from vnstock3 import Vnstock
    VNSTOCK_AVAILABLE = True
except ImportError:
    VNSTOCK_AVAILABLE = False


# ---------------------------------------------------------------------------
# Server instance
# ---------------------------------------------------------------------------

app = Server("vnstock-oracle")


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _df_to_records(df) -> list[dict]:
    """Convert a pandas DataFrame to a list of plain dicts."""
    return df.reset_index().to_dict(orient="records")


def _error_response(msg: str) -> list[types.TextContent]:
    return [types.TextContent(type="text", text=json.dumps({"error": msg}))]


import re
from datetime import datetime


def _validate_ticker(ticker: str) -> str:
    """Validate and normalize ticker symbol."""
    t = ticker.strip().upper()
    if not re.match(r"^[A-Z0-9]{1,10}$", t):
        raise ValueError(f"Invalid ticker format: {ticker!r}")
    return t


def _validate_date(date_str: str) -> str:
    """Validate YYYY-MM-DD date format."""
    datetime.strptime(date_str, "%Y-%m-%d")
    return date_str


def _ok_response(data: Any) -> list[types.TextContent]:
    return [types.TextContent(type="text", text=json.dumps(data, default=str))]


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_financial_report",
            description=(
                "Returns quarterly income statement, balance sheet, and cash flow "
                "for a Vietnamese stock ticker (e.g. VNM, FPT, VCB). "
                "Specify year and quarter to narrow the result range."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Stock ticker symbol (uppercase), e.g. 'VNM'",
                    },
                    "year": {
                        "type": "integer",
                        "description": "Target year, e.g. 2024",
                    },
                    "quarter": {
                        "type": "integer",
                        "description": "Target quarter 1-4, e.g. 3",
                    },
                },
                "required": ["ticker", "year", "quarter"],
            },
        ),
        types.Tool(
            name="get_credit_score_data",
            description=(
                "Returns key financial ratios used for SME credit scoring: "
                "ROE, ROA, debt-to-equity, current ratio, quick ratio, and more."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Stock ticker symbol (uppercase), e.g. 'VNM'",
                    },
                },
                "required": ["ticker"],
            },
        ),
        types.Tool(
            name="get_stock_price",
            description=(
                "Returns historical OHLCV (open/high/low/close/volume) price data "
                "for a Vietnamese stock ticker within the given date range."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Stock ticker symbol (uppercase), e.g. 'VNM'",
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Start date in YYYY-MM-DD format, e.g. '2024-01-01'",
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date in YYYY-MM-DD format, e.g. '2024-12-31'",
                    },
                },
                "required": ["ticker", "start_date", "end_date"],
            },
        ),
    ]


# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------

@app.call_tool()
async def call_tool(
    name: str, arguments: dict
) -> list[types.TextContent]:
    if not VNSTOCK_AVAILABLE:
        return _error_response("vnstock3 library is not installed. Run: pip install vnstock3")

    if name == "get_financial_report":
        return await _get_financial_report(**arguments)
    elif name == "get_credit_score_data":
        return await _get_credit_score_data(**arguments)
    elif name == "get_stock_price":
        return await _get_stock_price(**arguments)
    else:
        return _error_response(f"Unknown tool: {name}")


async def _get_financial_report(
    ticker: str, year: int, quarter: int
) -> list[types.TextContent]:
    """Fetch income statement, balance sheet, and cash flow for the given ticker/period."""
    try:
        ticker = _validate_ticker(ticker)
        stock = Vnstock().stock(symbol=ticker, source="VCI")

        income_df = stock.finance.income_statement(period="quarter", lang="en")
        balance_df = stock.finance.balance_sheet(period="quarter", lang="en")
        cashflow_df = stock.finance.cash_flow(period="quarter", lang="en")

        # Filter to requested year/quarter when the DataFrame has a 'year'/'quarter' column
        def _filter(df):
            records = _df_to_records(df)
            filtered = [
                r for r in records
                if str(r.get("year", "")) == str(year)
                and str(r.get("quarter", "")) == str(quarter)
            ]
            # Fall back to all records if filtering produces nothing
            return filtered if filtered else records

        result = {
            "ticker": ticker.upper(),
            "year": year,
            "quarter": quarter,
            "income_statement": _filter(income_df),
            "balance_sheet": _filter(balance_df),
            "cash_flow": _filter(cashflow_df),
        }
        return _ok_response(result)

    except Exception as exc:
        return _error_response(
            f"Failed to fetch financial report for {ticker}: {exc}"
        )


async def _get_credit_score_data(ticker: str) -> list[types.TextContent]:
    """Fetch key financial ratios relevant for SME credit assessment."""
    try:
        ticker = _validate_ticker(ticker)
        stock = Vnstock().stock(symbol=ticker, source="VCI")
        ratio_df = stock.finance.ratio(period="quarter", lang="en")
        records = _df_to_records(ratio_df)

        # Extract the most recent period
        latest = records[0] if records else {}

        # Surface the ratios most relevant for credit scoring
        CREDIT_KEYS = {
            "roe", "roa", "debt_on_equity", "debt_on_asset",
            "current_ratio", "quick_ratio", "interest_coverage",
            "gross_profit_margin", "net_profit_margin",
            "asset_turnover", "revenue", "net_income",
        }
        credit_view = {
            k: v for k, v in latest.items()
            if any(ck in k.lower() for ck in CREDIT_KEYS)
        }

        result = {
            "ticker": ticker.upper(),
            "credit_ratios": credit_view,
            "all_ratios_latest": latest,
            "history": records,
        }
        return _ok_response(result)

    except Exception as exc:
        return _error_response(
            f"Failed to fetch credit score data for {ticker}: {exc}"
        )


async def _get_stock_price(
    ticker: str, start_date: str, end_date: str
) -> list[types.TextContent]:
    """Fetch OHLCV price history for the given ticker and date range."""
    try:
        ticker = _validate_ticker(ticker)
        start_date = _validate_date(start_date)
        end_date = _validate_date(end_date)
        stock = Vnstock().stock(symbol=ticker, source="VCI")
        price_df = stock.quote.history(start=start_date, end=end_date)
        records = _df_to_records(price_df)

        result = {
            "ticker": ticker.upper(),
            "start_date": start_date,
            "end_date": end_date,
            "count": len(records),
            "ohlcv": records,
        }
        return _ok_response(result)

    except Exception as exc:
        return _error_response(
            f"Failed to fetch price history for {ticker}: {exc}"
        )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def _run_stdio():
    """Run the MCP server over stdio (default for IDE integration)."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="vnstock-oracle",
                server_version="0.1.0",
                capabilities=app.get_capabilities(
                    notification_options=None,
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    import asyncio

    parser = argparse.ArgumentParser(description="vnstock MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio"],
        default="stdio",
        help="Transport mode (default: stdio)",
    )
    args = parser.parse_args()

    asyncio.run(_run_stdio())
