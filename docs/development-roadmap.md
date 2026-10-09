# Kế hoạch Triển khai (Roadmap) - Mekong CLI v6.0

## Phase 283–286: Maritime & Logistics D (Tháng 10/2026)
- Tình trạng: **Hoàn thành 100%**
- Nội dung: MARPOL Annex I OWS 15 ppm, MLC 2006 Wages & Escrow, TT 39/2023 Mooring & MEG4, Customs OLA ICD Transit.

## Phase 287–290: Maritime & Logistics E (Tháng 10/2026)
- Tình trạng: **Hoàn thành 100%** 
- Nội dung: MARPOL Garbage, STCW Rest, Port Wharfage & CFS E-Seal.

## Phase 291–294: Maritime & Logistics F (Tháng 10/2026)
- Tình trạng: **Hoàn thành 100%**
- Nội dung: MARPOL Annex IV Sewage Discharge, STCW I/9 Seafarer Medical Fitness, TT 39/2023 Port Stevedoring Tariffs, Customs Bonded Warehouse Supervision.

## Phase 295–298: Maritime Compliance & Operations G (Tháng 10/2026)
- Tình trạng: **Hoàn thành 100%**
- Nội dung: MARPOL VI ECA/CII Tracker, Time Charter Off-Hire & Demurrage, Circular 39/2023 Towage Dues, Customs STS Split Manifest.

## Phase 299–302: Maritime Security & Hazardous Port Ops H (Tháng 10/2026)
- Tình trạng: **Hoàn thành 100%**
- Nội dung: ISPS Port Security & DoS, Hazmat Waste Disposal, OOG Stevedoring Tariffs, Anchorage GRT Cap Booking.

## Phase 303–306: Maritime Crew, Fuel & Port Automation I (Tháng 10/2026)
- Tình trạng: **Hoàn thành 100%**
- Nội dung: MLC 2006 FAL 5 Crew Clearance, ASTM D1250 Bunkering BDN, Shore Power Cold Ironing Billing, VASSCM Customs Adapter.

## Phase 307–310: Maritime Hazmat, Containers & Port Dispatch J (Tháng 10/2026)
- Tình trạng: **Hoàn thành 100%**
- Nội dung: IMDG Segregation Table 7.2.4, Tiered Container D&D, Tugboat Quota Dispatch, Ship Chandler Quotation.

## Phase 311–314: Maritime Commercial & Technical Operations K (Tháng 10/2026)
- Tình trạng: **Hoàn thành 100%**
- Nội dung: SS 600/648 Bunker MFM Dispute & Cappuccino NoP, TT 39/2023 Seaport Tidal Pilotage, UN ECE Draft Survey Net Displacement, Reefer Temperature Claim Analysis.

## Phase 315–318: Maritime PSC, Bulk Safety & Lien Enforcement L (Tháng 10/2026)
- Tình trạng: **Hoàn thành 100%**
- Nội dung: Tokyo MoU Port State Control Ship Risk Profile & Targeting, IMSBC Bulk Cargo Liquefaction TML/FMP, BWM D-1 Exchange vs D-2 Treatment, Maritime Lien & Vessel Arrest Proceeds Waterfall (Điều 37 Bộ luật HHVN 2015).

## Phase 319–322: Maritime Navigation, GA, VGM & Insurance M (Tháng 10/2026)
- Tình trạng: **Hoàn thành 100%**
- Nội dung: COLREGs 1972 Collision Prevention & CPA/TCPA, York-Antwerp Rules 2016 General Average Adjustment, SOLAS VI/2 Container Verified Gross Mass (VGM), ITC-Hulls 1/10/83 Marine Insurance Claims & 3/4 RDC.

## Phase 323–326: Maritime Tanker COW, Chemical Prewash, LNG BOG/CTMS, Lifeboat FPD & Enclosed Space Entry N (Tháng 10/2026)
- Tình trạng: **Hoàn thành 100%**
- Nội dung: MARPOL Annex I Reg 33/35 Crude Oil Washing (COW), IBC Code Ch.16 Chemical Tanker Prewash & Stripping residue verification, IGC Code Ch.7 & GIIGNL CTMS LNG Boil-Off Gas (BOG/BOR) and Energy Custody Transfer, SOLAS III/20 & MSC.1/Circ.1327 Lifeboat Fall Preventer Device (FPD) Safety Release Mechanism, IMO Res. A.1050(27) Enclosed Space 4-Gas Clearance & 8-hour Permit System. Kiến trúc Hybrid Modular Facade (<200 LOC per file), 4 Typer CLI apps, 8 bilingual Vietnamese aliases, 5 FastMCP tools, và 21 zero-mock unit & integration tests.

## Phase 327–330: Maritime Ballast BWM/USCG, Decarb FuelEU, Port Lifting ILO 152 & Oil Spill OPRC NEBA O (Tháng 10/2026)
- Tình trạng: **Hoàn thành 100%**
- Nội dung: Quản lý Nước dằn tàu & Trầm tích tiên tiến (IMO BWM D-2 vs USCG 46 CFR 162.060 CMF/FDA, UVT >= 50%, TRO <= 0.1 mg/L neutralization, sediment stripping < 5%), Giám sát Phát thải Khí nhà kính & Nhiên liệu thay thế (EU ETS Maritime MRV phase-in surrender 2024-2026, FuelEU Maritime GHG intensity pooling & deficit penalty, IGF/IGC Code Methanol/Ammonia Dual-Fuel Bunkering Safety với N2 purge O2 < 2% và bán kính an toàn động), Kiểm định Thiết bị Nâng Cảng biển (ILO Convention 152 / QCVN 23:2010 statutory proof load piecewise curves, chu kỳ đăng kiểm năm <= 12m / 5 năm <= 60m, ISO 4309 wire rope discard criteria: đường kính giảm >= 7%, đứt sợi, rỗ ăn mòn), và Ứng phó Sự cố Tràn dầu Quốc gia (OPRC 1990 Tier 1-3 classification, NEBA Chemical Dispersant Matrix: độ sâu >= 10m, khoảng cách >= 3 NM, độ nhớt < 10,000 cSt, phao quây L = 3x LOA, skimmer recovery sizing). Kiến trúc Hybrid Modular Facade (<200 LOC per file), 4 Typer CLI apps, 8 bilingual Vietnamese aliases (`ballast`, `nuocdan`, `bwmuscg`, `decarb`, `giamphatthai`, `fueleu`, `lifting`, `thietbinang`, `cauport`, `spill`, `trandau`, `oprcneba`), 4 FastMCP tools, và 23 zero-mock tests xanh 100%.

## Phase 331–334: IALA Buoyage AtoN, VNSW FAL Port Clearance, IMSBC Group B Gas Safety & H&M Casualty Survey P (Tháng 10/2026)
- Tình trạng: **Hoàn thành 100%**
- Nội dung: Giám sát Phao tiêu Luồng hàng hải & AIS AtoN Telemetry Message 21 (IALA Maritime Buoyage System Vùng A/B, Cardinal/Lateral Marks, giám sát trôi dạt Haversine alarm >50m, điện áp ắc quy, đèn hiệu), Tự động hóa Khai báo Thủ tục Một cửa Quốc gia Hàng hải VNSW (IMO FAL Form 1-7, Nghị định 58/2017/NĐ-CP, kiểm tra Hải quan, Kiểm dịch Y tế, Biên phòng, Phí cảng vụ, cấp giấy phép rời cảng kèm SHA-256 audit digest), Kiểm soát An toàn Xếp dỡ Hàng rời Nguy hiểm & Khí hầm hàng (IMSBC Code Nhóm B, cảnh báo hiện tượng tự phát nhiệt than/quặng, bốc cháy nồng độ khí cháy CH4/H2 >= 20% LEL, khí độc Phosphine PH3 > 0.3 ppm, thiếu dưỡng khí O2 < 19.5%, khuyến nghị thông gió bề mặt hoặc niêm phong trơ hóa), và Giám định Tổn thất Thân tàu & Máy tàu (H&M Marine Casualty Damage Survey & Adjuster Apportionment, khấu trừ New for Old trượt theo tuổi tàu ITC-Hulls 1983, tổn thất toàn bộ ước tính Constructive Total Loss >= 80% giá trị bảo hiểm, tính toán trách nhiệm bồi thường thực tế). Kiến trúc Hybrid Modular Facade (<200 LOC per file), 4 Typer CLI apps, 8 bilingual Vietnamese aliases (`aton`, `phaotieu`, `iala`, `vnsw`, `motcua`, `imofal`, `imsbc`, `hangnguyhiem`, `hamhang`, `hmsurvey`, `giamdinhtau`, `tonthathm`), 4 FastMCP tools, và 18 zero-mock tests xanh 100%.

## Phase 335–338: VTS & TSS Traffic Separation, Project Cargo CSS Lashing, Electric Tug Cold Ironing & BIMCO Charterparty Arbitration Q (Tháng 10/2026)
- Tình trạng: **Hoàn thành 100%**
- Nội dung: Hệ thống Phân luồng Giao thông Hàng hải & Quản lý Luồng lạch TSS/VTS (COLREGs Rule 10, IMO Res. A.1158(32), IALA VTS Standards INS/TOS/NAS, tính toán CPA/TCPA va chạm vector radar, phát hiện tàu đi ngược luồng heading deviation > 90°, kiểm soát hành lang luồng và độ lệch tim luồng XTE), Quản lý & Giám sát Chằng buộc Hàng siêu trường siêu trọng Project Cargo & Heavy Lift OOG (IMO CSS Code Annex 13, DNV-ST-N001, tính toán gia tốc 3 trục ax/ay/az, lực ma sát lót dunnage mu=0.1-0.3, hiệu suất chằng buộc MSL 3D alpha/beta, xác thực hệ số an toàn trượt SF_sliding >= 1.25 và lật SF_tipping >= 1.25), Hệ thống Quản lý Năng lượng Tàu lai dắt Xanh & Cấp điện Cảng biển Bờ Cold Ironing (IEC/IEEE 80005-1/3, điều tiết phụ tải đỉnh trạm biến áp cảng peak shaving, dự phòng năng lượng khẩn cấp pin SoC >= 20%, chỉ số tiêu thụ năng lượng lực kéo bollard pull <= 0.15 kWh/(t-pull*h), tính toán cắt giảm khí thải CO2 và NOx theo baseline MGO), và Quản lý Hợp đồng Thuê tàu BIMCO & Phân xử Trọng tài Hàng hải (BIMCO NYPE 2015 / GENCON 2022, loại trừ thời tiết xấu Beaufort > 4 hoặc Douglas > 3, xác định vi phạm bảo đảm tốc độ và tiêu thụ nhiên liệu speed/fuel warranty, tính thưởng phạt dỡ hàng laytime demurrage & despatch, phân xử trọng tài LMAA Intermediate/Small Claims và Trung tâm Trọng tài Quốc tế Việt Nam VMAC). Kiến trúc Hybrid Modular Facade (<200 LOC per file), 4 Typer CLI apps, 8 bilingual Vietnamese aliases (`vts`, `luonghanghai`, `phanquyvts`, `csscargo`, `hangsieutruong`, `changketoog`, `electug`, `taulaidien`, `dienbencang`, `charter`, `thuetautrongtai`, `tranhchaphanghai`), 4 FastMCP tools, và 18 zero-mock unit & integration tests xanh 100%.

## Phase 339–342: Polar Code POLARIS, Hold Washwater MARPOL HME, PCTC EV Fire Safety & LOF/SCOPIC Salvage R (Tháng 10/2026)
- Tình trạng: **Hoàn thành 100%**
- Nội dung: Quản lý An toàn Tàu vùng Cực IMO Polar Code & POLARIS RIO (MSC.1/Circ.1519, tính toán RIO theo tổ hợp lớp băng và cấp tàu PC1–PC7/Non-Polar, phân định 3 trạng thái Normal/Elevated Risk/Prohibited, tính toán Polar Service Temperature PST = MDLT - 10°C, giới hạn tốc độ an toàn theo rủi ro băng), Giám sát Nước Rửa Hầm hàng & Tuân thủ MARPOL Annex V HME (Nghị quyết MEPC.295(71), phân loại cặn hàng HME vs Non-HME, kiểm soát xả biển khoảng cách >= 12 NM khi tàu đang hành trình ngoài vùng đặc biệt, liều lượng hóa chất tẩy rửa theo PPM, kiểm tra trung hòa pH nước xả 6.5–8.5, ghi nhật ký xả rác Garbage Record Book Part II), An toàn Chống Cháy Pin Lithium-ion trên Tàu Chở Ô tô PCTC Ro-Ro (SOLAS II-2 Reg 20, MSC.1/Circ.1615, ma trận cảnh báo khí thoát nhiệt CO >= 30 ppm, H2 >= 200 ppm, tốc độ tăng nhiệt >= 1.0°C/s, kiểm tra lưu lượng hệ thống chữa cháy biên làm mát màng nước deluge >= 10 L/phút/m², giới hạn tỷ lệ sạc pin vận chuyển SoC <= 50%), và Trọng tài Cứu hộ Hàng hải Quốc tế Lloyd's Open Form LOF 2024 & Điều khoản SCOPIC (Công ước Cứu hộ 1989 Articles 13 & 14, tính toán thù lao cứu tài sản Article 13 theo Salved Value và hệ số công lao cứu hộ, thù lao đặc biệt SCOPIC theo biểu giá Hội P&I + 25% uplift, khấu trừ phạt 25% phần chênh lệch khi Article 13 vượt SCOPIC, xác định trách nhiệm chi trả giữa Chủ hàng/Thân tàu và Hội P&I Club). Kiến trúc Hybrid Modular Facade (<200 LOC per file), 4 Typer CLI apps, 8 bilingual Vietnamese aliases (`polar`, `bangtuyet`, `polarisrio`, `holdwash`, `ruahamhang`, `marpolhme`, `evfire`, `chayxedien`, `pctcro`, `salvageclaim`, `cuuhohanghai`, `scopiclof`), 4 FastMCP tools, và 15 zero-mock unit & CLI/MCP tests xanh 100%.

## Phase 343–346: ECDIS Passage Planning, Bunkering MFM Coriolis, Boiler Water Chemistry & Port Agency FDA S (Tháng 10/2026)
- Tình trạng: **Hoàn thành 100%**
- Nội dung: Lập Kế hoạch Tuyến hành trình Hải đồ Điện tử ECDIS & Đường đẳng sâu An toàn Safety Contour (IMO Res. A.893(21), SOLAS V/34, IHO S-57/S-52, tính toán độ chìm do hiệu ứng lòng cạn Squat theo công thức Barrass cho luồng hẹp và vùng nước rộng, dung sai độ sâu CATZOC A1–U, tính Safety Depth và tự động làm tròn lên Safety Contour ENC [5, 10, 15, 20, 30, 50m], kiểm soát hành lang lệch tuyến XTL 50–500m và thời gian cảnh báo Look-Ahead 6–15 phút), Hệ thống Cân bằng Khối lượng Đo lưu lượng Kép Coriolis MFM & Cảnh báo Nhiên liệu Bọt khí Cappuccino (Singapore SS 648:2019, ISO 22192, sai số cho phép tối đa MPE +/-0.5%, phát hiện hiện tượng sục khí cappuccino qua Drive Gain >= 80% hoặc sụt giảm khối lượng riêng >= 2%, kiểm tra hàm lượng lưu huỳnh MARPOL Annex VI 0.50% toàn cầu / 0.10% vùng ECA, tự động lập Biên bản Khiếu nại Notice of Protest NoP), Kiểm soát Hóa nghiệm Nước Nồi hơi Tàu biển & Định mức Xả đáy Blowdown (ISO 5814, BS 2486, tiêu chuẩn phân cấp tàu cho nồi hơi phụ và nồi hơi cao áp, kiểm soát dải pH 9.5–11.0, giới hạn clorua Cl- <= 300 ppm, P-Alkalinity 100–300 ppm, Phosphate đệm bùn 20–50 ppm, Hydrazine khử oxy hòa tan 0.05–0.25 ppm, tự động tính tỷ lệ xả đáy liên tục/định kỳ blowdown % để ngăn ngừa cáu cặn và ăn mòn điểm), và Quyết toán Tài khoản Chi phí Đại lý Tàu biển PDA vs FDA (FONASBA Standard Port Agency Agreement, Thông tư 39/2023/TT-BGTVT biểu cước cảng biển Việt Nam, đối soát chi phí thực tế cầu bến, hoa tiêu, lai dắt, buộc mở dây, thu gom rác so với tạm ứng cash advance và dự toán ban đầu PDA, cảnh báo vượt ngân sách > 5%, xác định số dư thanh toán bù trừ hoàn trả hoặc đòi thêm Chủ tàu). Kiến trúc Hybrid Modular Facade (<200 LOC per file), 4 Typer CLI apps, 8 bilingual Vietnamese aliases (`ecdis`, `haidodientu`, `mfmbunker`, `dodaucoriolis`, `noihoint`, `hoanoihotau`, `portagency`, `quyettoancangg`), 4 FastMCP tools, và 17 zero-mock unit & CLI/MCP tests xanh 100%.

## Phase 347–350: Impressed Current Cathodic Protection (ICCP), Marine Engine SCR NOx Tier III, Port Anchorage Windlass Holding & e-BL MLETR Title Transfer T (Tháng 10/2026)
- Tình trạng: **Hoàn thành 100%**
- Nội dung: Hệ thống Giám sát Ăn mòn Ca-tốt Vỏ tàu & Dòng điện Cưỡng bức ICCP cùng Anode Hy sinh (NACE SP0176, DNV-RP-B401, kiểm soát điện thế tham chiếu chuẩn Ag/AgCl an toàn [-1050 mV, -800 mV], cảnh báo ăn mòn dưới bảo vệ và rộp sơn bong tróc hydro quá bảo vệ, tính diện tích thấm ướt wetted surface area, nhu cầu dòng điện Amperes và định mức khối lượng anode Zn/Al), Giám sát Khí xả Động cơ Diesel Thủy SCR & Động cơ Nhiên liệu Kép ME-GI (IMO MARPOL Annex VI Reg 13 NOx Tier III NECA limit piecewise curves, khóa liên động nhiệt độ xúc tác catalyst >= 300°C ngăn kết tinh muối amoni bisulfate, định mức định lượng dung dịch Urê AUS 40 stoichiometric dosing, và giám sát rò rỉ khí mê-tan methane slip <= 2.5 g/kWh), Đánh giá Khả năng Giữ Neo Cảng biển & Sức bền Thiết bị Kéo Neo Windlass (IACS UR A1 Equipment Number EN, tính toán tỷ lệ độ dài xích thả/độ sâu nước scope ratio >= 4:1, lực giữ nền đáy biển bùn cát/đá theo catenary, kiểm tra tải trọng môi trường gió bão & dòng thủy triều, phát hiện nguy cơ kéo rê neo dragging anchor alarm), và Chuyển nhượng Quyền sở hữu Vận đơn Điện tử e-BL & Hợp đồng Vận chuyển Container theo MLETR (UNCITRAL Model Law on Electronic Transferable Records 2017, chuẩn dữ liệu DCSA e-BL, kiểm tra chuỗi kiểm soát độc quyền exclusive control lineage hash SHA-256, xác thực điều kiện giải phóng hàng lawful cargo release authorization). Kiến trúc Hybrid Modular Facade (<200 LOC per file), 4 Typer CLI apps, 8 bilingual Vietnamese aliases (`iccp`, `chongannmon`, `scrnox`, `khixatier3`, `anchorwindlass`, `neocang`, `eblmletr`, `vandonso`), 4 FastMCP tools, và 16 zero-mock unit & CLI/MCP tests xanh 100%.

## Phase 351–354: Kế hoạch Tiếp theo (Next Horizon)
- Tình trạng: **Sẵn sàng Triển khai (Ready to Implement)**
- Focus: Hàng hải & Khai thác Cảng biển Nâng cao U: Giám sát Trạng thái Ổn định Tĩnh & Động Tàu Hàng Rời Bulk Carrier Loading Computer (SOLAS XII/11, IACS UR S1/S1A, Intact Stability Code 2008 GZ curve, Bending Moment BM & Shear Force SF limits), Hệ thống Cảnh báo Sớm Hiện tượng Trôi Dạt Dầu & Phân tán Hóa chất Độc hại HNS (OPRC-HNS Protocol 2000, CEDRE SEACARAMB drift trajectory, CHEMMAC hazard zones), Kiểm soát Hệ thống Làm mát Nước Biển Trung tâm Central Cooling Water System (plate heat exchangers, bio-fouling marine growth prevention MGPS Cu/Al ion dosing, energy-saving seawater scoop & VFD pump curves), và Tự động hóa Giám sát Chứng nhận Điện tử Thân tàu E-Certificates Verifiable Credentials (IMO FAL.5/Circ.39/Rev.2, W3C DID / Verifiable Credentials, QR/blockchain verification for Class, Safety, & Load Line certificates).
