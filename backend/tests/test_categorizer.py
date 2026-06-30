"""Tests for categorizer prompts and validator."""

import json


from backend.categorizer.prompts import VALID_CATEGORIES, build_categorization_prompt
from backend.categorizer.validator import (
    parse_llm_response,
    validate_category,
    validate_response,
)


class TestBuildCategorizationPrompt:
    def test_contains_all_dimensions(self):
        prompt = build_categorization_prompt("some transcription")
        for dim in VALID_CATEGORIES:
            assert dim in prompt

    def test_contains_transcription(self):
        transcription = "Hola, somos una clínica dental"
        prompt = build_categorization_prompt(transcription)
        assert transcription in prompt

    def test_contains_valid_categories(self):
        prompt = build_categorization_prompt("test")
        for cats in VALID_CATEGORIES.values():
            for cat in cats:
                assert cat in prompt

    def test_contains_few_shot_example(self):
        prompt = build_categorization_prompt("test")
        assert "Few-shot" in prompt
        assert '"sector": "Health"' in prompt

    def test_asks_for_json_only(self):
        prompt = build_categorization_prompt("test")
        assert "JSON" in prompt


class TestParseLLMResponse:
    def test_valid_json(self):
        raw = json.dumps({"sector": "Health", "size": "Micro"})
        result = parse_llm_response(raw)
        assert result["sector"] == "Health"
        assert result["size"] == "Micro"

    def test_json_in_code_fences(self):
        raw = '```json\n{"sector": "Health"}\n```'
        result = parse_llm_response(raw)
        assert result["sector"] == "Health"

    def test_json_in_plain_fences(self):
        raw = '```\n{"sector": "Health"}\n```'
        result = parse_llm_response(raw)
        assert result["sector"] == "Health"

    def test_malformed_json_returns_empty(self):
        raw = "not json at all"
        result = parse_llm_response(raw)
        assert result == {}

    def test_empty_string_returns_empty(self):
        result = parse_llm_response("")
        assert result == {}

    def test_partial_json_returns_empty(self):
        raw = '{"sector": "Health"'
        result = parse_llm_response(raw)
        assert result == {}


class TestValidateCategory:
    def test_valid_category_passes(self):
        assert validate_category("sector", "Health") == "Health"

    def test_case_insensitive_match(self):
        assert validate_category("sector", "health") == "Health"

    def test_invalid_sector_mapped_to_other(self):
        assert validate_category("sector", "InvalidSector") == "Other"

    def test_none_mapped_to_other(self):
        assert validate_category("sector", None) == "Other"

    def test_none_size_mapped_to_not_specified(self):
        assert validate_category("size", None) == "Not specified"

    def test_none_inquiry_volume_mapped_to_not_specified(self):
        assert validate_category("inquiry_volume", None) == "Not specified"

    def test_invalid_size_mapped_to_not_specified(self):
        assert validate_category("size", "Huge") == "Not specified"

    def test_invalid_inquiry_volume_mapped_to_not_specified(self):
        assert validate_category("inquiry_volume", "Ultra") == "Not specified"

    def test_all_valid_sectors_pass(self):
        for cat in VALID_CATEGORIES["sector"]:
            assert validate_category("sector", cat) == cat

    def test_all_valid_sizes_pass(self):
        for cat in VALID_CATEGORIES["size"]:
            assert validate_category("size", cat) == cat

    def test_valid_channel(self):
        assert validate_category("channel", "WhatsApp") == "WhatsApp"

    def test_invalid_channel(self):
        assert validate_category("channel", "Fax") == "Other"


class TestValidateResponse:
    def test_valid_response_passes(self):
        raw = json.dumps(
            {
                "sector": "Health",
                "size": "Medium",
                "inquiry_volume": "High",
                "channel": "WhatsApp",
                "source": "Google/Search",
                "integrations": "CRM",
                "tone": "Professional",
                "usage_type": "Scheduling",
                "pain": "High message volume",
                "concreteness": "Concrete/Actionable",
            }
        )
        result = validate_response(raw)
        assert result["sector"] == "Health"
        assert result["size"] == "Medium"
        assert result["inquiry_volume"] == "High"
        assert result["channel"] == "WhatsApp"

    def test_invalid_categories_mapped(self):
        raw = json.dumps(
            {
                "sector": "Aliens",
                "size": "Huge",
                "inquiry_volume": "Ultra",
                "channel": "Fax",
                "source": "Unknown",
                "integrations": "Blockchain",
                "tone": "Angry",
                "usage_type": "Gaming",
                "pain": "Boredom",
                "concreteness": "Shy",
            }
        )
        result = validate_response(raw)
        assert result["sector"] == "Other"
        assert result["size"] == "Not specified"
        assert result["channel"] == "Other"
        assert result["source"] == "Other"
        assert result["integrations"] == "Other"
        assert result["tone"] == "Other"
        assert result["usage_type"] == "Other"
        assert result["pain"] == "Other"
        assert result["concreteness"] == "Other"

    def test_malformed_json_returns_empty(self):
        result = validate_response("not json")
        assert result == {}

    def test_empty_response_returns_empty(self):
        result = validate_response("")
        assert result == {}

    def test_missing_fields_filled_with_fallback(self):
        raw = json.dumps({"sector": "Health"})
        result = validate_response(raw)
        assert result["sector"] == "Health"
        # All other dims should be fallback
        assert result["size"] == "Not specified"
        assert result["channel"] == "Other"
        assert result["pain"] == "Other"

    def test_inquiry_volume_kept_as_string(self):
        raw = json.dumps(
            {
                "sector": "Health",
                "size": "Micro",
                "inquiry_volume": "Low",
                "channel": "WhatsApp",
                "source": "LinkedIn",
                "integrations": "CRM",
                "tone": "Professional",
                "usage_type": "Scheduling",
                "pain": "High message volume",
                "concreteness": "Mixed",
            }
        )
        result = validate_response(raw)
        assert isinstance(result["inquiry_volume"], str)
        assert result["inquiry_volume"] == "Low"

    def test_inquiry_volume_not_specified_stored(self):
        raw = json.dumps(
            {
                "sector": "Health",
                "size": "Micro",
                "inquiry_volume": "Not specified",
                "channel": "WhatsApp",
                "source": "LinkedIn",
                "integrations": "CRM",
                "tone": "Professional",
                "usage_type": "Scheduling",
                "pain": "High message volume",
                "concreteness": "Mixed",
            }
        )
        result = validate_response(raw)
        assert result["inquiry_volume"] == "Not specified"

    def test_code_fenced_response_validated(self):
        raw = '```json\n{"sector": "Education", "size": "Small", "inquiry_volume": "Medium", "channel": "Instagram", "source": "Social Media", "integrations": "POS", "tone": "Fun/Young", "usage_type": "Lead qualification", "pain": "Slow response", "concreteness": "Tentative/Exploratory"}\n```'
        result = validate_response(raw)
        assert result["sector"] == "Education"
        assert result["size"] == "Small"
        assert result["inquiry_volume"] == "Medium"
