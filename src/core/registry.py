"""
Mekong CLI - Recipe Registry

Manages discovery and metadata of available recipes.
"""

from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
from rich.table import Table
from rich.console import Console

from .parser import RecipeParser, Recipe

@dataclass
class RegistryIndex:
    """Index entry for a recipe"""
    name: str
    description: str
    path: Path
    author: str = "Unknown"
    version: str = "0.1.0"
    tags: List[str] = None

class RecipeRegistry:
    """
    Manages the collection of available recipes.
    """

    def __init__(self, recipes_dir: Path = Path("recipes")):
        self.recipes_dir = recipes_dir
        self.parser = RecipeParser()
        self.console = Console()

    def scan(self) -> List[RegistryIndex]:
        """Scan recipes directory and return index of all valid recipes"""
        if not self.recipes_dir.exists():
            return []

        index = []
        for recipe_file in self.recipes_dir.glob("*.md"):
            try:
                recipe = self.parser.parse(recipe_file)

                # Extract metadata safely
                meta = recipe.metadata

                # Prefer description from metadata, fallback to body description
                description = meta.get("description", recipe.description) or "No description provided"

                entry = RegistryIndex(
                    name=recipe.name,
                    description=description,
                    path=recipe_file,
                    author=meta.get("author", "Unknown"),
                    version=meta.get("version", "0.1.0"),
                    tags=meta.get("tags", "").split(",") if meta.get("tags") else []
                )
                index.append(entry)
            except Exception as e:
                # Skip invalid recipes but log warning
                # self.console.print(f"[dim yellow]Warning: Could not parse {recipe_file.name}: {e}[/dim yellow]")
                pass

        return sorted(index, key=lambda x: x.name)

    def search(self, query: str) -> List[RegistryIndex]:
        """Search recipes by name, description or tags"""
        all_recipes = self.scan()
        query = query.lower()

        results = []
        for recipe in all_recipes:
            # Check name and description
            if query in recipe.name.lower() or query in recipe.description.lower():
                results.append(recipe)
                continue

            # Check tags
            if any(query in tag.lower().strip() for tag in recipe.tags):
                results.append(recipe)

        return results

    def get_recipe(self, name: str) -> Optional[Recipe]:
        """Get full parsed recipe by name or filename"""
        # Try exact filename match first
        path = self.recipes_dir / name
        if path.exists():
            return self.parser.parse(path)

        path = self.recipes_dir / f"{name}.md"
        if path.exists():
            return self.parser.parse(path)

        # Search by internal name
        all_recipes = self.scan()
        for entry in all_recipes:
            if entry.name == name:
                return self.parser.parse(entry.path)

        return None
