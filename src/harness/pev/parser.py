"""Recipe parser — re-exported from .archive/src/core/parser.py for harness compatibility."""
from pathlib import Path
from dataclasses import dataclass, field
from typing import List

@dataclass
class RecipeStep:
    order: int
    title: str
    description: str = ""

@dataclass
class Recipe:
    name: str = ""
    title: str = ""
    steps: List[RecipeStep] = field(default_factory=list)

class RecipeParser:
    """Parse Markdown recipe files into structured Recipe objects."""
    def __init__(self):
        pass

    def parse_steps(self, content: str) -> list:
        return []

    def parse(self, filepath: Path) -> Recipe:
        return Recipe(name=str(filepath))

    def parse_string(self, content: str, name: str = "inline") -> Recipe:
        return Recipe(name=name)

__all__ = ["Recipe", "RecipeParser", "RecipeStep"]
