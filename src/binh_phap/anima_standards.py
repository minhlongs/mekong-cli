"""
ANIMA 119 Industry Standards
Defines the specialized checks for the pharma-ecommerce premium standard.
"""

import subprocess
from pathlib import Path
from typing import Dict
from .standards import StandardCheck

# Resolve APP_ROOT relative to mekong-cli structure
# mekong-cli/apps/anima119
APP_ROOT = Path("/Users/macbookprom1/mekong-cli/apps/anima119")


class AnimaBuildCheck(StandardCheck):
    """Check that the Anima 119 Next.js project builds successfully."""

    def __init__(self) -> None:
        """Initialize AnimaBuildCheck with preset name."""
        super().__init__("Anima Build Health")

    def run(self) -> bool:
        """Run 'npm run build' and verify exit code is 0.

        Returns:
            True if build succeeds, False otherwise.
        """
        try:
            result = subprocess.run(
                ["npm", "run", "build"],
                cwd=str(APP_ROOT),
                capture_output=True,
                text=True,
                timeout=300,
            )
            if result.returncode == 0:
                self.status = True
                self.details = "Next.js build successful."
            else:
                self.status = False
                self.details = f"Build failed: {result.stderr[:100]}..."
        except Exception as e:
            self.status = False
            self.details = str(e)
        return self.status


class AnimaSEOCheck(StandardCheck):
    """Check that SEO essentials (sitemap.xml, robots.txt) are present."""

    def __init__(self) -> None:
        """Initialize AnimaSEOCheck with preset name."""
        super().__init__("Anima SEO & Meta")

    def run(self) -> bool:
        """Verify sitemap.xml and robots.txt exist in public/.

        Returns:
            True if all SEO files are present, False otherwise.
        """
        checks = ["public/sitemap.xml", "public/robots.txt"]
        missing = []
        for c in checks:
            if not (APP_ROOT / c).exists():
                missing.append(c)

        if not missing:
            self.status = True
            self.details = "Sitemap and Robots.txt present."
        else:
            self.status = False
            self.details = f"Missing: {', '.join(missing)}"
        return self.status


class Animai18nCheck(StandardCheck):
    """Check that Vietnamese i18n translation file exists."""

    def __init__(self) -> None:
        """Initialize Animai18nCheck with preset name."""
        super().__init__("Anima i18n VI Coverage")

    def run(self) -> bool:
        """Verify messages/vi.json exists in the app directory.

        Returns:
            True if Vietnamese locale file is present, False otherwise.
        """
        vi_path = APP_ROOT / "messages/vi.json"
        if vi_path.exists():
            self.status = True
            self.details = "Vietnamese message file detected."
        else:
            self.status = False
            self.details = "Missing messages/vi.json."
        return self.status


class AnimaImageCheck(StandardCheck):
    """Check that brand image assets are properly integrated."""

    def __init__(self) -> None:
        """Initialize AnimaImageCheck with preset name."""
        super().__init__("Anima Image Assets")

    def run(self) -> bool:
        """Verify public/images/brand/ contains at least 5 PNG files.

        Returns:
            True if sufficient brand images exist, False otherwise.
        """
        brand_path = APP_ROOT / "public/images/brand"
        if brand_path.exists():
            files = list(brand_path.glob("*.png"))
            if len(files) >= 5:
                self.status = True
                self.details = f"Detected {len(files)} brand images."
            else:
                self.status = False
                self.details = f"Poor image integration: {len(files)} found."
        else:
            self.status = False
            self.details = "public/images/brand missing."
        return self.status


class AnimaMobileCheck(StandardCheck):
    """Check that Tailwind responsive classes are used sufficiently."""

    def __init__(self) -> None:
        """Initialize AnimaMobileCheck with preset name."""
        super().__init__("Anima Mobile Responsive")

    def run(self) -> bool:
        """Grep src/ for 'md:' responsive breakpoint classes.

        Returns:
            True if responsive class density is adequate, False otherwise.
        """
        try:
            result = subprocess.run(
                ["grep", "-r", "md:", "src"],
                cwd=str(APP_ROOT),
                capture_output=True,
                text=True,
            )
            if len(result.stdout) > 100:
                self.status = True
                self.details = "Responsive classes detected."
            else:
                self.status = False
                self.details = "Low responsive class density."
        except Exception as e:
            self.status = False
            self.details = str(e)
        return self.status


class AnimaA11yCheck(StandardCheck):
    """Check that image accessibility alt attributes are present."""

    def __init__(self) -> None:
        """Initialize AnimaA11yCheck with preset name."""
        super().__init__("Anima Accessibility (a11y)")

    def run(self) -> bool:
        """Grep src/ for 'alt=' attributes and require more than 20 hits.

        Returns:
            True if sufficient alt text definitions exist, False otherwise.
        """
        try:
            result = subprocess.run(
                ["grep", "-r", "alt=", "src"],
                cwd=str(APP_ROOT),
                capture_output=True,
                text=True,
            )
            count = len(result.stdout.splitlines())
            if count > 20:
                self.status = True
                self.details = f"Found {count} alt text definitions."
            else:
                self.status = False
                self.details = f"Only {count} alt tags found. Audit required."
        except Exception as e:
            self.status = False
            self.details = str(e)
        return self.status


def get_anima_standards() -> Dict[str, StandardCheck]:
    """Return all Anima 119 pharma-ecommerce quality checks.

    Returns:
        Dict mapping check keys to StandardCheck instances for build,
        SEO, i18n, images, mobile, and accessibility.
    """
    return {
        "build": AnimaBuildCheck(),
        "seo": AnimaSEOCheck(),
        "i18n": Animai18nCheck(),
        "images": AnimaImageCheck(),
        "mobile": AnimaMobileCheck(),
        "a11y": AnimaA11yCheck(),
    }
