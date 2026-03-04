"""
⭐ Testimonial Generator - Social Proof Engine (Proxy)
===============================================
This file is now a proxy for the modularized version in ./testimonials/
Please import from core.crm.testimonials instead.
"""
import warnings


# Issue a deprecation warning
warnings.warn(
    "core.crm.testimonial is deprecated. "
    "Use core.crm.testimonials instead.",
    DeprecationWarning,
    stacklevel=2
)
