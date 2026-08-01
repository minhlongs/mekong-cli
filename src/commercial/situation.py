"""Ch2: Tình Hình — Situation assessment, five factors."""

class SituationAssessor:
    def assess(self, company: dict | str = "", **kwargs) -> dict:
        if isinstance(company, str) and not company:
            company = kwargs
        elif isinstance(company, dict):
            company = {**company, **kwargs}
        return {
            "chapter": 2,
            "command": "venture:five-factors",
            "factors": {
                "dao": {"score": None, "notes": "Ruler alignment — unknown"},
                "tian": {"score": None, "notes": "Weather/market conditions — unknown"},
                "di": {"score": None, "notes": "Terrain advantage — unknown"},
                "jiang": {"score": None, "notes": "Commander capability — unknown"},
                "fa": {"score": None, "notes": "Process/method — unknown"},
            },
            "overall_score": None,
            "stub": True,
            "recommendations": ["Run five-factors assessment — SituationAssessor stub"],
        }
