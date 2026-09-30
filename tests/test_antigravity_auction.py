"""
Comprehensive Unit & Integration Test Suite for Vietnamese Property Auction, Distressed Asset Liquidation & Judicial Asset Disposal Suite.
Statutory Framework:
- Luật Đấu giá tài sản 2016 (Luật số 01/2016/QH14)
- Luật sửa đổi, bổ sung một số điều của Luật Đấu giá tài sản 2024 (Luật số 37/2024/QH15)
- Nghị định số 62/2017/NĐ-CP & Nghị định số 47/2023/NĐ-CP
- Bộ luật Hình sự 2015 (Điều 218)
"""

import json
import pytest
from typer.testing import CliRunner

from src.core.auction_engine import AuctionEngine
from src.cli.commands.auction_command import auction_app
import scripts.mcp_server as mcp_script
from src.core.mcp_server import MekongMcpServer

runner = CliRunner()


@pytest.fixture
def temp_engine(tmp_path):
    db_file = str(tmp_path / "test_auction.db")
    return AuctionEngine(db_path=db_file)


class TestAuctionEngine:
    def test_register_auctioneer_valid(self, temp_engine):
        res = temp_engine.register_auctioneer(
            full_name="Đặng Quốc Bảo",
            certificate_no="BTP-ĐGV-88/2022",
            org_name="Công ty Đấu giá Hợp danh Mekong Law",
            issue_date="2022-05-18",
            is_practicing=True,
        )
        assert res["is_certified"] is True
        assert res["status"] == "CERTIFIED_PRACTICING"
        assert res["auctioneer_id"].startswith("AUC-")
        assert len(res["violations"]) == 0

    def test_register_auctioneer_invalid_cert(self, temp_engine):
        # Missing BTP prefix in certificate number
        res = temp_engine.register_auctioneer(
            full_name="Nguyễn Văn X",
            certificate_no="LOCAL-CERT-01",
            org_name="Công ty Đấu giá",
        )
        assert res["is_certified"] is False
        assert res["status"] == "PRACTICE_SUSPENDED_OR_INVALID"
        assert any("Bộ Tư pháp cấp" in v for v in res["violations"])

    def test_register_auction_asset_valid(self, temp_engine):
        res = temp_engine.register_auction_asset(
            asset_name="Trụ sở cũ Sở Công Thương (Diện tích 1,200 m2)",
            asset_type="PUBLIC_PROPERTY",
            owner_agency="UBND Tỉnh Đồng Nai",
            starting_price_vnd=45000000000.0,
            step_price_vnd=200000000.0,
            deposit_percent=10.0,
            notice_days=30,
        )
        assert res["is_valid"] is True
        assert res["status"] == "ASSET_LISTED_FOR_AUCTION"
        assert res["asset_id"].startswith("AST-")
        assert res["deposit_amount_vnd"] == 4500000000.0
        assert "tiền đặt trước 10.0%" in res["statutory_notes"]

    def test_register_auction_asset_land_deposit_bounds(self, temp_engine):
        # Under Law 37/2024/QH15, LAND_USE_RIGHT deposit must be 10% - 20%
        res_low = temp_engine.register_auction_asset(
            asset_name="Khu đất dự án thương mại dịch vụ 5,000m2",
            asset_type="LAND_USE_RIGHT",
            owner_agency="Sở Tài nguyên và Môi trường",
            starting_price_vnd=100000000000.0,
            deposit_percent=5.0,  # Below 10%
            notice_days=30,
        )
        assert res_low["is_valid"] is False
        assert res_low["status"] == "ASSET_REGISTRATION_INVALID"
        assert any("từ 10% đến 20%" in v for v in res_low["violations"])

    def test_register_auction_asset_insufficient_notice(self, temp_engine):
        # Real estate requires minimum 30 days notice under Art 35
        res = temp_engine.register_auction_asset(
            asset_name="Căn biệt thự số 18",
            asset_type="PUBLIC_PROPERTY",
            starting_price_vnd=20000000000.0,
            notice_days=14,  # Below 30 days
        )
        assert res["is_valid"] is False
        assert any("tối thiểu 30 ngày" in v for v in res["violations"])

    def test_register_bidder_valid(self, temp_engine):
        asset = temp_engine.register_auction_asset(
            asset_name="Xe ô tô công vụ Toyota Camry 2.5Q",
            asset_type="PUBLIC_PROPERTY",
            starting_price_vnd=800000000.0,
            deposit_percent=10.0,  # Required: 80,000,000 VND
            notice_days=30,
        )
        res = temp_engine.register_bidder(
            asset_id=asset["asset_id"],
            bidder_name="Công ty TNHH Vận tải Toàn Cầu",
            id_card_or_tax_code="0312345678",
            deposit_paid_vnd=80000000.0,
            has_prohibited_relation=False,
        )
        assert res["is_eligible"] is True
        assert res["status"] == "BIDDER_QUALIFIED"
        assert res["bidder_id"].startswith("BID-")

    def test_register_bidder_underpaid_deposit(self, temp_engine):
        asset = temp_engine.register_auction_asset(
            asset_name="Lô dây chuyền sản xuất",
            asset_type="DISTRESSED_DEBT",
            starting_price_vnd=1000000000.0,
            deposit_percent=10.0,  # Required: 100,000,000 VND
            notice_days=15,
        )
        res = temp_engine.register_bidder(
            asset_id=asset["asset_id"],
            bidder_name="Doanh nghiệp tư nhân Hưng Thịnh",
            id_card_or_tax_code="0309999888",
            deposit_paid_vnd=50000000.0,  # Only paid 50M < 100M
        )
        assert res["is_eligible"] is False
        assert res["status"] == "BIDDER_DISQUALIFIED"
        assert any("Tiền đặt trước đã nộp" in v for v in res["violations"])

    def test_register_bidder_prohibited_relation(self, temp_engine):
        asset = temp_engine.register_auction_asset(
            asset_name="Tài sản kê biên nhà phố",
            asset_type="ENFORCEMENT_ASSET",
            starting_price_vnd=5000000000.0,
            deposit_percent=10.0,
            notice_days=30,
        )
        res = temp_engine.register_bidder(
            asset_id=asset["asset_id"],
            bidder_name="Bà Nguyễn Thị Vợ Đấu Giá Viên",
            id_card_or_tax_code="079190001234",
            deposit_paid_vnd=500000000.0,
            has_prohibited_relation=True,  # Art 38(4) violation
        )
        assert res["is_eligible"] is False
        assert any("Khoản 4 Điều 38" in v for v in res["violations"])

    def test_conduct_auction_session_valid(self, temp_engine):
        asset = temp_engine.register_auction_asset(
            asset_name="Quyền sử dụng tần số 4G/5G Băng tần B1",
            asset_type="MINING_SPECTRUM_VEHICLE",
            starting_price_vnd=3000000000000.0,
            deposit_percent=5.0,
            notice_days=15,
        )
        auctioneer = temp_engine.register_auctioneer(
            full_name="Trần Văn Minh",
            certificate_no="BTP-ĐGV-001/2018",
        )
        res = temp_engine.conduct_auction_session(
            asset_id=asset["asset_id"],
            auctioneer_id=auctioneer["auctioneer_id"],
            winning_bidder_id="BID-VIETTEL",
            winning_price_vnd=3500000000000.0,
            auction_format="ONLINE_PORTAL",
            signed_protocol=True,
        )
        assert res["is_valid"] is True
        assert res["status"] == "AUCTION_SUCCESS_CONTRACT_PENDING"
        assert res["session_id"].startswith("SES-")
        assert res["price_increase_vnd"] == 500000000000.0
        assert "chênh lệch tăng giá" in res["statutory_notes"]

    def test_conduct_auction_session_below_reserve(self, temp_engine):
        asset = temp_engine.register_auction_asset(
            asset_name="Biệt thự nghỉ dưỡng",
            asset_type="DISTRESSED_DEBT",
            starting_price_vnd=15000000000.0,
            deposit_percent=10.0,
            notice_days=30,
        )
        res = temp_engine.conduct_auction_session(
            asset_id=asset["asset_id"],
            auctioneer_id="AUC-01",
            winning_bidder_id="BID-01",
            winning_price_vnd=12000000000.0,  # Below starting price
        )
        assert res["is_valid"] is False
        assert any("Giá khởi điểm" in v for v in res["violations"])

    def test_conduct_auction_session_unsigned_protocol(self, temp_engine):
        asset = temp_engine.register_auction_asset(
            asset_name="Lô gỗ tịch thu",
            asset_type="CONFISCATED_GOODS",
            starting_price_vnd=200000000.0,
            deposit_percent=10.0,
            notice_days=15,
        )
        res = temp_engine.conduct_auction_session(
            asset_id=asset["asset_id"],
            auctioneer_id="AUC-01",
            winning_bidder_id="BID-01",
            winning_price_vnd=220000000.0,
            signed_protocol=False,  # Unsigned
        )
        assert res["is_valid"] is False
        assert any("chưa được ký xác nhận đầy đủ" in v for v in res["violations"])

    def test_audit_collusion_risk_normal(self, temp_engine):
        bids = [
            {"bidder": "BID-A", "amount_vnd": 1000000000.0, "withdrawn": False},
            {"bidder": "BID-B", "amount_vnd": 1050000000.0, "withdrawn": False},
            {"bidder": "BID-C", "amount_vnd": 1100000000.0, "withdrawn": False},
        ]
        ips = ["118.69.10.1", "113.161.20.2", "14.162.30.3"]
        res = temp_engine.audit_collusion_risk(
            asset_id="AST-01",
            bids=bids,
            shared_network_ips=ips,
        )
        assert res["has_collusion_risk"] is False
        assert res["risk_level"] == "LOW_NORMAL"
        assert len(res["anomalies"]) == 0

    def test_audit_collusion_risk_detected(self, temp_engine):
        bids = [
            {"bidder": "BID-A", "amount_vnd": 1000000000.0, "withdrawn": True},
            {"bidder": "BID-B", "amount_vnd": 1000000000.0, "withdrawn": True},
            {"bidder": "BID-C", "amount_vnd": 1010000000.0, "withdrawn": False},
        ]
        ips = ["192.168.1.50", "192.168.1.50"]  # Duplicate IPs
        res = temp_engine.audit_collusion_risk(
            asset_id="AST-02",
            bids=bids,
            shared_network_ips=ips,
        )
        assert res["has_collusion_risk"] is True
        assert res["risk_level"] == "HIGH_COLLUSION_RISK"
        assert any("cùng một địa chỉ IP" in a for a in res["anomalies"])
        assert any("mức giá trả trùng lặp" in a for a in res["anomalies"])
        assert "Điều 218 Bộ luật Hình sự" in res["recommendation"]

    def test_list_records_and_telemetry(self, temp_engine):
        temp_engine.register_auctioneer("Võ Tấn Hùng")
        asset = temp_engine.register_auction_asset(
            asset_name="Tài sản thử nghiệm",
            starting_price_vnd=1000000000.0,
            notice_days=30,
        )
        temp_engine.register_bidder(
            asset_id=asset["asset_id"],
            bidder_name="Công ty Beta",
            id_card_or_tax_code="0300112233",
            deposit_paid_vnd=100000000.0,
        )
        temp_engine.conduct_auction_session(
            asset_id=asset["asset_id"],
            auctioneer_id="AUC-01",
            winning_bidder_id="BID-01",
            winning_price_vnd=1200000000.0,
        )

        all_records = temp_engine.list_auction_records(category="ALL")
        assert len(all_records["auctioneers"]) == 1
        assert len(all_records["auction_assets"]) == 1
        assert len(all_records["bidders"]) == 1
        assert len(all_records["auction_sessions"]) == 1

        telemetry = temp_engine.get_auction_telemetry()
        assert telemetry["total_auctioneers"] == 1
        assert telemetry["total_assets"] == 1
        assert telemetry["total_bidders"] == 1
        assert telemetry["total_sessions"] == 1
        assert telemetry["successful_sessions"] == 1
        assert telemetry["success_rate_pct"] == 100.0
        assert telemetry["total_winning_value_vnd"] == 1200000000.0
        assert telemetry["total_price_increase_vnd"] == 200000000.0


class TestAuctionCli:
    def test_cli_auctioneer_json(self):
        result = runner.invoke(auction_app, [
            "auctioneer",
            "Lê Thái Hoàng",
            "--cert", "BTP-ĐGV-2024/09",
            "--org", "Văn phòng Đấu giá Quốc tế",
            "--date", "2024-01-10",
            "--json",
        ])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["is_certified"] is True
        assert data["auctioneer_id"].startswith("AUC-")

    def test_cli_auctioneer_console(self):
        result = runner.invoke(auction_app, [
            "auctioneer",
            "Ngô Bá Khá",
            "--cert", "BTP-ĐGV-99/2023",
        ])
        assert result.exit_code == 0
        assert "Hồ Sơ Đấu Giá Viên" in result.stdout

    def test_cli_asset_json(self):
        result = runner.invoke(auction_app, [
            "asset",
            "Khu đất công nghiệp 20ha",
            "--type", "LAND_USE_RIGHT",
            "--owner", "Ban Quản lý KCN Long Đức",
            "--price", "500000000000",
            "--step", "2000000000",
            "--deposit", "12",
            "--notice", "35",
            "--json",
        ])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["asset_id"].startswith("AST-")
        assert data["is_valid"] is True

    def test_cli_asset_console(self):
        result = runner.invoke(auction_app, [
            "asset",
            "Xe ô tô BMW 730Li",
            "--type", "PUBLIC_PROPERTY",
            "--price", "2500000000",
            "--deposit", "10",
            "--notice", "30",
        ])
        assert result.exit_code == 0
        assert "Hồ Sơ Niêm Yết Tài Sản Đấu Giá" in result.stdout

    def test_cli_bidder_json(self):
        result = runner.invoke(auction_app, [
            "bidder",
            "AST-DEMO-01",
            "Tập đoàn Nam Thắng",
            "0109988776",
            "--deposit", "60000000000",
            "--json",
        ])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["bidder_id"].startswith("BID-")

    def test_cli_bidder_console(self):
        result = runner.invoke(auction_app, [
            "bidder",
            "AST-DEMO-02",
            "Bà Mai Phương",
            "079192000888",
            "--deposit", "50000000",
        ])
        assert result.exit_code == 0
        assert "Thẩm Tra Điều Kiện Người Tham Gia Đấu Giá" in result.stdout

    def test_cli_session_json(self):
        result = runner.invoke(auction_app, [
            "session",
            "AST-DEMO-01",
            "AUC-01",
            "BID-01",
            "520000000000",
            "--format", "ONLINE_PORTAL",
            "--protocol",
            "--json",
        ])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["session_id"].startswith("SES-")
        assert data["is_valid"] is True

    def test_cli_session_console(self):
        result = runner.invoke(auction_app, [
            "session",
            "AST-DEMO-02",
            "AUC-02",
            "BID-02",
            "2800000000",
            "--format", "DIRECT_VOTING",
        ])
        assert result.exit_code == 0
        assert "Biên Bản Cuộc Đấu Giá Tài Sản" in result.stdout

    def test_cli_audit_json(self):
        result = runner.invoke(auction_app, [
            "audit",
            "AST-DEMO-01",
            "--bids", '[{"amount_vnd": 1000000000, "withdrawn": false}]',
            "--ips", '["14.161.0.1"]',
            "--json",
        ])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["audit_id"].startswith("AUD-")
        assert data["has_collusion_risk"] is False

    def test_cli_audit_console(self):
        result = runner.invoke(auction_app, [
            "audit",
            "AST-DEMO-02",
        ])
        assert result.exit_code == 0
        assert "Báo Cáo Thẩm Tra Chống Dìm Giá & Thông Đồng" in result.stdout

    def test_cli_list_json(self):
        result = runner.invoke(auction_app, ["list", "--category", "ALL", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "auctioneers" in data
        assert "auction_assets" in data

    def test_cli_status_json(self):
        result = runner.invoke(auction_app, ["status", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "total_auctioneers" in data
        assert "success_rate_pct" in data

    def test_cli_status_console(self):
        result = runner.invoke(auction_app, ["status"])
        assert result.exit_code == 0
        assert "Chỉ Số Telemetry Đấu Giá Tài Sản Quốc Gia" in result.stdout

    def test_cli_main_callback(self):
        result = runner.invoke(auction_app, [])
        assert result.exit_code == 0
        assert "HỆ THỐNG ĐẤU GIÁ TÀI SẢN, XỬ LÝ NỢ XẤU & TÀI SẢN THI HÀNH ÁN DÂN SỰ" in result.stdout


class TestAuctionMcp:
    def test_core_mcp_server_handlers(self):
        srv = MekongMcpServer()
        # auctioneer
        res_auc = json.loads(srv._handle_auction_auctioneer(
            full_name="Đặng Quốc Bảo",
            certificate_no="BTP-ĐGV-88/2022",
        ))
        assert res_auc["is_certified"] is True

        # asset
        res_ast = json.loads(srv._handle_auction_asset(
            asset_name="Trụ sở số 10 Phan Bội Châu",
            asset_type="PUBLIC_PROPERTY",
            starting_price_vnd=25000000000.0,
            notice_days=30,
        ))
        assert res_ast["asset_id"].startswith("AST-")

        # bidder
        res_bid = json.loads(srv._handle_auction_bidder(
            asset_id=res_ast["asset_id"],
            bidder_name="Công ty Hải Nam",
            id_card_or_tax_code="0301122334",
            deposit_paid_vnd=2500000000.0,
        ))
        assert res_bid["is_eligible"] is True

        # session
        res_ses = json.loads(srv._handle_auction_session(
            asset_id=res_ast["asset_id"],
            auctioneer_id=res_auc["auctioneer_id"],
            winning_bidder_id=res_bid["bidder_id"],
            winning_price_vnd=27000000000.0,
        ))
        assert res_ses["is_valid"] is True

        # audit
        res_aud = json.loads(srv._handle_auction_audit(
            asset_id=res_ast["asset_id"],
            bids_json='[{"amount_vnd": 25000000000}]',
        ))
        assert res_aud["audit_id"].startswith("AUD-")

        # list
        res_list = json.loads(srv._handle_auction_list(category="ALL"))
        assert "auctioneers" in res_list

        # status
        res_stat = json.loads(srv._handle_auction_status())
        assert res_stat["total_auctioneers"] >= 1

    def test_scripts_mcp_server_handlers(self):
        # auctioneer
        res_auc = json.loads(mcp_script.handle_auction_auctioneer({
            "full_name": "Lê Văn Tám",
            "certificate_no": "BTP-ĐGV-77/2020",
        }))
        assert res_auc["is_certified"] is True

        # asset
        res_ast = json.loads(mcp_script.handle_auction_asset({
            "asset_name": "Xe biển số đẹp 51K-888.88",
            "asset_type": "MINING_SPECTRUM_VEHICLE",
            "starting_price_vnd": 40000000.0,
            "deposit_percent": 10.0,
            "notice_days": 15,
        }))
        assert res_ast["asset_id"].startswith("AST-")

        # bidder
        res_bid = json.loads(mcp_script.handle_auction_bidder({
            "asset_id": res_ast["asset_id"],
            "bidder_name": "Nguyễn Hoàng Long",
            "id_card_or_tax_code": "079195000111",
            "deposit_paid_vnd": 4000000.0,
        }))
        assert res_bid["is_eligible"] is True

        # session
        res_ses = json.loads(mcp_script.handle_auction_session({
            "asset_id": res_ast["asset_id"],
            "auctioneer_id": res_auc["auctioneer_id"],
            "winning_bidder_id": res_bid["bidder_id"],
            "winning_price_vnd": 1520000000.0,
            "auction_format": "ONLINE_PORTAL",
        }))
        assert res_ses["is_valid"] is True

        # audit
        res_aud = json.loads(mcp_script.handle_auction_audit({
            "asset_id": res_ast["asset_id"],
            "bids_json": '[{"amount_vnd": 1520000000}]',
        }))
        assert res_aud["audit_id"].startswith("AUD-")

        # list
        res_list = json.loads(mcp_script.handle_auction_list({"category": "ALL"}))
        assert "auctioneers" in res_list

        # status
        res_stat = json.loads(mcp_script.handle_auction_status({}))
        assert res_stat["total_auctioneers"] >= 1

    def test_scripts_mcp_registration_and_spec_parity(self):
        assert "mekong_auction_auctioneer" in mcp_script.CORE_HANDLERS
        assert "mekong_auction_asset" in mcp_script.CORE_HANDLERS
        assert "mekong_auction_bidder" in mcp_script.CORE_HANDLERS
        assert "mekong_auction_session" in mcp_script.CORE_HANDLERS
        assert "mekong_auction_audit" in mcp_script.CORE_HANDLERS
        assert "mekong_auction_list" in mcp_script.CORE_HANDLERS
        assert "mekong_auction_status" in mcp_script.CORE_HANDLERS

        assert "auction_auctioneer" in mcp_script.CORE_HANDLERS
        assert "auction_asset" in mcp_script.CORE_HANDLERS
        assert "auction_bidder" in mcp_script.CORE_HANDLERS
        assert "auction_session" in mcp_script.CORE_HANDLERS
        assert "auction_audit" in mcp_script.CORE_HANDLERS
        assert "auction_list" in mcp_script.CORE_HANDLERS
        assert "auction_status" in mcp_script.CORE_HANDLERS

        spec_names = {t["name"] for t in mcp_script.CORE_TOOLS_SPEC}
        assert "mekong_auction_auctioneer" in spec_names
        assert "mekong_auction_asset" in spec_names
        assert "mekong_auction_bidder" in spec_names
        assert "mekong_auction_session" in spec_names
        assert "mekong_auction_audit" in spec_names
        assert "mekong_auction_list" in spec_names
        assert "mekong_auction_status" in spec_names
