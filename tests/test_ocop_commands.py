"""Tests for OCOP Commands - AI-powered agricultural export tools."""

import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.commands.ocop_commands import (
    _generate_analysis,
    _generate_fallback_analysis,
    _generate_listing,
    _generate_fallback_listing,
)


class TestGenerateAnalysis(unittest.TestCase):
    """Test AI-powered product analysis generation."""

    def setUp(self):
        """Set up test fixtures."""
        self.sample_product_data = {
            "name": "Vietnamese Robusta Coffee",
            "origin": "Dak Lak, Vietnam",
            "type": "coffee_beans",
        }
        self.test_file = Path("/tmp/test_product.jpg")

    @patch("src.commands.ocop_commands.get_client")
    def test_analysis_with_llm_success(self, mock_get_client):
        """Test analysis generation with successful LLM response."""
        mock_client = MagicMock()
        mock_client.generate_json.return_value = {
            "hs_code": "0901.11",
            "category": "Agricultural Product",
            "subcategory": "Coffee, not roasted",
            "grade": "A",
            "certifications": ["VietGAP", "GlobalGAP", "ISO 22000"],
            "shelf_life_days": 365,
            "phytosanitary_required": True,
            "food_safety_required": True,
            "origin_certificate_required": True,
            "suggested_markets": ["Japan", "EU", "USA", "South Korea"],
            "estimated_fob_usd_kg": 4.50,
        }
        mock_get_client.return_value = mock_client

        result = _generate_analysis(self.sample_product_data, self.test_file)

        self.assertTrue(result["classification"]["hs_code"])
        self.assertEqual(result["quality"]["grade"], "A")
        self.assertIn("VietGAP", result["quality"]["certifications"])
        self.assertTrue(result["export_compliance"]["phytosanitary"])
        self.assertIn("Japan", result["suggested_markets"])
        self.assertEqual(result["estimated_fob_usd_kg"], 4.50)

    @patch("src.commands.ocop_commands.get_client")
    def test_analysis_with_llm_partial_response(self, mock_get_client):
        """Test analysis with partial LLM response - should use defaults."""
        mock_client = MagicMock()
        mock_client.generate_json.return_value = {
            "hs_code": "0901.21",
            "category": "Agricultural Product",
        }
        mock_get_client.return_value = mock_client

        result = _generate_analysis(self.sample_product_data, self.test_file)

        self.assertEqual(result["classification"]["hs_code"], "0901.21")
        self.assertEqual(result["quality"]["grade"], "A")  # Default
        self.assertEqual(result["quality"]["shelf_life_days"], 365)  # Default

    @patch("src.commands.ocop_commands.get_client")
    def test_analysis_llm_failure_uses_fallback(self, mock_get_client):
        """Test analysis when LLM fails - should use fallback."""
        mock_client = MagicMock()
        mock_client.generate_json.side_effect = Exception("LLM unavailable")
        mock_get_client.return_value = mock_client

        result = _generate_analysis(self.sample_product_data, self.test_file)

        self.assertEqual(result["classification"]["hs_code"], "0901.11")
        self.assertEqual(result["quality"]["grade"], "A")
        self.assertIn("VietGAP", result["quality"]["certifications"])

    def test_fallback_analysis_structure(self):
        """Test fallback analysis returns correct structure."""
        result = _generate_fallback_analysis(self.sample_product_data, self.test_file)

        self.assertIn("source", result)
        self.assertIn("classification", result)
        self.assertIn("quality", result)
        self.assertIn("export_compliance", result)
        self.assertIn("suggested_markets", result)
        self.assertIn("estimated_fob_usd_kg", result)

        self.assertEqual(result["classification"]["hs_code"], "0901.11")
        self.assertEqual(result["quality"]["grade"], "A")
        self.assertTrue(result["export_compliance"]["phytosanitary"])


class TestGenerateListing(unittest.TestCase):
    """Test AI-powered export listing generation."""

    def setUp(self):
        """Set up test fixtures."""
        self.sample_product_data = {
            "classification": {
                "hs_code": "0901.11",
                "category": "Agricultural Product",
                "subcategory": "Coffee, not roasted",
            },
            "quality": {
                "grade": "A",
                "certifications": ["VietGAP", "GlobalGAP"],
            },
            "estimated_fob_usd_kg": 4.50,
        }

    @patch("src.commands.ocop_commands.get_client")
    def test_listing_alibaba_optimization(self, mock_get_client):
        """Test listing optimized for Alibaba B2B platform."""
        mock_client = MagicMock()
        mock_client.generate_json.return_value = {
            "title": "Premium Vietnamese Robusta Coffee Beans - Wholesale Bulk",
            "price": "$4.50/kg FOB Ho Chi Minh City",
            "moq": "1,000 kg",
            "origin": "Dak Lak, Vietnam",
            "shipping": "FOB, CIF available",
            "certifications": ["VietGAP", "GlobalGAP", "ISO 22000"],
            "description": "High-quality Robusta coffee from Vietnam's Central Highlands.",
            "keywords": ["robusta", "vietnam coffee", "bulk coffee", "wholesale"],
        }
        mock_get_client.return_value = mock_client

        result = _generate_listing("alibaba", self.sample_product_data)

        self.assertEqual(result["platform"], "alibaba")
        self.assertIn("title", result)
        self.assertIn("price", result)
        self.assertIn("moq", result)
        self.assertIn("certifications", result)

    @patch("src.commands.ocop_commands.get_client")
    def test_listing_shopee_optimization(self, mock_get_client):
        """Test listing optimized for Shopee SEA platform."""
        mock_client = MagicMock()
        mock_client.generate_json.return_value = {
            "title": "Cà Phê Robusta Việt Nam - Giao Hàng Miễn Phí",
            "price": "₫105,000/kg",
            "moq": "10 kg",
            "origin": "Vietnam",
            "shipping": "Free shipping, local warehouse",
            "certifications": ["VietGAP"],
        }
        mock_get_client.return_value = mock_client

        result = _generate_listing("shopee", self.sample_product_data)

        self.assertEqual(result["platform"], "shopee")

    @patch("src.commands.ocop_commands.get_client")
    def test_listing_tiki_optimization(self, mock_get_client):
        """Test listing optimized for Tiki Vietnam platform."""
        mock_client = MagicMock()
        mock_client.generate_json.return_value = {
            "title": "Cà Phê Hạt Robusta Dak Lak - Giao Nhanh TikiNOW",
            "price": "₫99,000/kg",
            "moq": "1 kg",
            "shipping": "TikiNOW same-day delivery",
        }
        mock_get_client.return_value = mock_client

        result = _generate_listing("tiki", self.sample_product_data)

        self.assertEqual(result["platform"], "tiki")

    @patch("src.commands.ocop_commands.get_client")
    def test_listing_llm_failure_uses_fallback(self, mock_get_client):
        """Test listing when LLM fails - should use fallback."""
        mock_client = MagicMock()
        mock_client.generate_json.side_effect = Exception("LLM unavailable")
        mock_get_client.return_value = mock_client

        result = _generate_listing("amazon", self.sample_product_data)

        self.assertEqual(result["platform"], "amazon")
        self.assertIn("Premium Vietnamese", result["title"])
        self.assertIn("VietGAP", result["certifications"])

    def test_fallback_listing_structure(self):
        """Test fallback listing returns correct structure."""
        result = _generate_fallback_listing("alibaba", self.sample_product_data)

        self.assertIn("title", result)
        self.assertIn("price", result)
        self.assertIn("moq", result)
        self.assertIn("origin", result)
        self.assertIn("shipping", result)
        self.assertIn("platform", result)
        self.assertIn("certifications", result)

        self.assertEqual(result["platform"], "alibaba")
        self.assertEqual(
            result["title"],
            "Premium Vietnamese Robusta Coffee Beans — Grade A, VietGAP Certified",
        )

    def test_fallback_listing_different_platforms(self):
        """Test fallback listing works for different platforms."""
        for platform in ["amazon", "alibaba", "shopee", "lazada", "tiki", "grab", "sendo"]:
            result = _generate_fallback_listing(platform, self.sample_product_data)
            self.assertEqual(result["platform"], platform)


class TestIntegration(unittest.TestCase):
    """Integration tests for OCOP analysis and listing flow."""

    @patch("src.commands.ocop_commands.get_client")
    def test_full_flow_analysis_to_listing(self, mock_get_client):
        """Test complete flow: analyze product then generate listing."""
        mock_client = MagicMock()
        mock_client.generate_json.side_effect = [
            # First call: analysis
            {
                "hs_code": "0901.11",
                "category": "Agricultural Product",
                "grade": "A",
                "certifications": ["VietGAP", "GlobalGAP"],
                "shelf_life_days": 365,
                "phytosanitary_required": True,
                "food_safety_required": True,
                "origin_certificate_required": True,
                "suggested_markets": ["Japan", "EU"],
                "estimated_fob_usd_kg": 4.50,
            },
            # Second call: listing
            {
                "title": "Premium Vietnamese Coffee - Direct from Farm",
                "price": "$4.50/kg FOB",
                "moq": "500 kg",
                "origin": "Dak Lak, Vietnam",
                "shipping": "FOB, CIF",
                "certifications": ["VietGAP", "GlobalGAP"],
            },
        ]
        mock_get_client.return_value = mock_client

        # Step 1: Analyze product
        product_file = Path("/tmp/coffee_sample.jpg")
        analysis = _generate_analysis({}, product_file)

        # Step 2: Generate listing from analysis
        listing = _generate_listing("alibaba", analysis)

        self.assertEqual(analysis["quality"]["grade"], "A")
        self.assertEqual(listing["platform"], "alibaba")
        self.assertEqual(mock_client.generate_json.call_count, 2)


if __name__ == "__main__":
    unittest.main()
