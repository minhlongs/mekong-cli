"""Domain command group registrations (part 06)."""

from __future__ import annotations

import typer


def register_groups_06(root: typer.Typer) -> None:
    """Register domain command groups part 06 on root."""
    from src.cli.commands.adminlaw_command import adminlaw_app  # noqa: E402
    root.add_typer(
        adminlaw_app,
        name="adminlaw",
        help="AdminLaw — Vietnamese Legal Normative Documents, RIA & State Compensation Liability Suite (Luật VBQPPL & Luật TNBTNN)",
    )
    from src.cli.commands.procuracy_command import procuracy_app  # noqa: E402
    root.add_typer(
        procuracy_app,
        name="procuracy",
        help="Procuracy — Vietnamese People's Procuracy, Public Prosecution & Judicial Supervision Suite (Luật Tổ chức VKSND 2014)",
    )
    from src.cli.commands.judicialassist_command import judicialassist_app  # noqa: E402
    root.add_typer(
        judicialassist_app,
        name="judicialassist",
        help="JudicialAssist — Vietnamese Mutual Legal Assistance, Extradition & Cross-Border Judicial Cooperation Suite (Luật Tương trợ tư pháp 2007)",
    )
    root.add_typer(
        judicialassist_app,
        name="extradition",
        help="Extradition — Alias for Vietnamese Mutual Legal Assistance & Extradition Suite (Luật Tương trợ tư pháp 2007)",
    )
    from src.cli.commands.nationality_command import nationality_app  # noqa: E402
    root.add_typer(
        nationality_app,
        name="nationality",
        help="Nationality — Vietnamese Nationality, Naturalization, Renunciation & Dual Citizenship Suite (Luật Quốc tịch Việt Nam 2008/2014)",
    )
    root.add_typer(
        nationality_app,
        name="citizenship",
        help="Citizenship — Alias for Vietnamese Nationality & Citizenship Rights Suite (Luật Quốc tịch Việt Nam 2008/2014)",
    )
    from src.cli.commands.immigration_command import immigration_app  # noqa: E402
    root.add_typer(
        immigration_app,
        name="immigration",
        help="Immigration — Vietnamese Immigration, Entry, Exit, Transit, Residence & Visa Management Suite (Luật Xuất nhập cảnh & Cư trú 2014/2023)",
    )
    root.add_typer(
        immigration_app,
        name="entryexit",
        help="EntryExit — Alias for Vietnamese Immigration, Entry, Exit & Border Control Suite",
    )
    from src.cli.commands.civilstatus_command import civilstatus_app  # noqa: E402
    root.add_typer(
        civilstatus_app,
        name="civilstatus",
        help="CivilStatus — Vietnamese Civil Status, Vital Statistics & Population Registration Suite (Luật Hộ tịch 2014 & Nghị định 123/2015/NĐ-CP)",
    )
    root.add_typer(
        civilstatus_app,
        name="hothich",
        help="HoThich — Alias for Vietnamese Civil Status, Vital Statistics & Electronic Civil Database Suite",
    )
    from src.cli.commands.adoption_command import adoption_app  # noqa: E402
    root.add_typer(
        adoption_app,
        name="adoption",
        help="Adoption — Vietnamese Child Adoption & Hague Intercountry Adoption Suite (Luật Nuôi con nuôi 2010)",
    )
    root.add_typer(
        adoption_app,
        name="connuoi",
        help="ConNuoi — Alias for Vietnamese Child Adoption & Hague Intercountry Adoption Suite",
    )
    from src.cli.commands.judicialrecord_command import judicialrecord_app  # noqa: E402
    root.add_typer(
        judicialrecord_app,
        name="judicialrecord",
        help="JudicialRecord — Vietnamese Judicial Records & Criminal Clearance Suite (Luật Lý lịch tư pháp 2009)",
    )
    root.add_typer(
        judicialrecord_app,
        name="lylich",
        help="LyLich — Alias for Vietnamese Judicial Records & Criminal Clearance Suite",
    )
    root.add_typer(
        judicialrecord_app,
        name="criminalrecord",
        help="CriminalRecord — Alias for Vietnamese Judicial Records & Criminal Clearance Suite",
    )
    from src.cli.commands.securedtransactions_command import securedtransactions_app  # noqa: E402
    root.add_typer(
        securedtransactions_app,
        name="securedtransactions",
        help="SecuredTransactions — Vietnamese Registration of Security Interests & Secured Transactions Suite (Nghị định 99/2022)",
    )
    root.add_typer(
        securedtransactions_app,
        name="baodam",
        help="BaoDam — Alias for Vietnamese Registration of Security Interests & Secured Transactions Suite",
    )
    root.add_typer(
        securedtransactions_app,
        name="giaodichbaodam",
        help="GiaoDichBaoDam — Alias for Vietnamese Registration of Security Interests & Secured Transactions Suite",
    )
    from src.cli.commands.marriage_command import marriage_app  # noqa: E402
    root.add_typer(
        marriage_app,
        name="marriage",
        help="Marriage — Vietnamese Marriage, Matrimonial Property Regimes & Family Law Suite (Luật HNGĐ 2014)",
    )
    root.add_typer(
        marriage_app,
        name="honnhan",
        help="HonNhan — Alias for Vietnamese Marriage, Matrimonial Property & Family Law Suite",
    )
    root.add_typer(
        marriage_app,
        name="giadinh",
        help="GiaDinh — Alias for Vietnamese Marriage, Matrimonial Property & Family Law Suite",
    )
