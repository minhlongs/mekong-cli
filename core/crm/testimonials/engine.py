"""
Testimonial Generator engine and showcase logic.
"""
from typing import List

from .models import Testimonial


class TestimonialEngine:
    def __init__(self, agency_name: str):
        self.agency_name = agency_name
        self.testimonials: List[Testimonial] = []

    def add_testimonial(self, testimonial: Testimonial):
        """Add a testimonial."""
        self.testimonials.append(testimonial)

    def generate_request_email(self, client_name: str, project_name: str) -> str:
        """Generate testimonial request email."""
        return f"""Subject: Quick favor? Share your experience with {self.agency_name}

Hi {client_name}! 👋

I hope you're doing great! We've loved working with you on {project_name}.

I have a quick favor to ask - would you mind sharing a brief testimonial about your experience working with us?

Just a few sentences about:
✅ What you liked most
✅ Results you achieved
✅ Would you recommend us?

Your feedback helps other businesses discover us!

Reply to this email with your thoughts, or I can schedule a quick 5-min call if easier.

Thanks so much! 🙏

Best,
{self.agency_name} Team 🏯

P.S. As a thank you, you'll get 10% off your next project! 💰
"""

    def format_testimonial(self, testimonial: Testimonial) -> str:
        """Format single testimonial."""
        stars = "★" * testimonial.rating.value + "☆" * (5 - testimonial.rating.value)
        lines = [
            "╔═══════════════════════════════════════════════════════════╗",
            f"║  ⭐ {stars}                                            ║",
            "╠═══════════════════════════════════════════════════════════╣",
        ]
        quote = testimonial.quote
        while len(quote) > 50:
            lines.append(f'║  "{quote[:50]}"              ║')
            quote = quote[50:]
        if quote:
            lines.append(f'║  "{quote}"{"·" * (52 - len(quote))}║')
        lines.append("║                                                           ║")
        lines.append(f"║  — {testimonial.client_name:<40}       ║")
        lines.append(f"║    {testimonial.role}, {testimonial.company:<35}  ║")
        if testimonial.results:
            lines.append("║                                                           ║")
            lines.append("║  📊 RESULTS:                                              ║")
            for key, value in list(testimonial.results.items())[:3]:
                lines.append(f"║    ✓ {key}: {value:<40}  ║")
        lines.append("╚═══════════════════════════════════════════════════════════╝")
        return "\n".join(lines)
