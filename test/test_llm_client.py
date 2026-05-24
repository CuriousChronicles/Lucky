"""Tests for llm_client.py — unit tests (no API) + integration test (real API)."""
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from llm_client import _format_event, _build_prompt, _validate_result, score_event


# ---------------------------------------------------------------------------
# _format_event
# ---------------------------------------------------------------------------

class TestFormatEvent:
    def test_all_fields_present(self):
        event = {
            "title": "AI Hackathon",
            "event_type": "hackathon",
            "source": "devpost.com",
            "url": "https://example.com",
            "deadline": "2026-06-01",
            "start_date": "2026-06-10",
            "location": "Auckland",
            "themes": "AI, ML",
        }
        result = _format_event(event)
        assert "Title: AI Hackathon" in result
        assert "Type: hackathon" in result
        assert "Location: Auckland" in result
        assert "Themes: AI, ML" in result

    def test_missing_fields_are_omitted(self):
        event = {"title": "Minimal Event"}
        result = _format_event(event)
        assert "Title: Minimal Event" in result
        assert "Type:" not in result
        assert "Location:" not in result

    def test_empty_event_returns_empty_string(self):
        assert _format_event({}) == ""

    def test_none_values_are_omitted(self):
        event = {"title": "Test", "location": None}
        result = _format_event(event)
        assert "Location:" not in result


# ---------------------------------------------------------------------------
# _build_prompt
# ---------------------------------------------------------------------------

class TestBuildPrompt:
    def test_contains_profile_and_event(self):
        profile = "ECE student, firmware focus"
        event = {"title": "Embedded Systems Workshop"}
        prompt = _build_prompt(profile, event)
        assert profile in prompt
        assert "Embedded Systems Workshop" in prompt

    def test_contains_json_instruction(self):
        prompt = _build_prompt("profile", {"title": "Event"})
        assert "score" in prompt
        assert "reasoning" in prompt
        assert "JSON" in prompt


# ---------------------------------------------------------------------------
# _validate_result
# ---------------------------------------------------------------------------

class TestValidateResult:
    def test_valid_result_passes_through(self):
        raw = {"score": 7, "reasoning": "Highly relevant to user interests."}
        result = _validate_result(raw)
        assert result == {"score": 7, "reasoning": "Highly relevant to user interests."}

    def test_score_coerced_to_int(self):
        raw = {"score": "8", "reasoning": "Good match."}
        result = _validate_result(raw)
        assert result["score"] == 8
        assert isinstance(result["score"], int)

    def test_reasoning_stripped(self):
        raw = {"score": 5, "reasoning": "  Some reasoning.  "}
        assert _validate_result(raw)["reasoning"] == "Some reasoning."

    def test_missing_score_raises(self):
        with pytest.raises(ValueError, match="missing score"):
            _validate_result({"reasoning": "ok"})

    def test_missing_reasoning_raises(self):
        with pytest.raises(ValueError, match="missing reasoning"):
            _validate_result({"score": 5})

    def test_score_below_range_raises(self):
        with pytest.raises(ValueError, match="out of range"):
            _validate_result({"score": 0, "reasoning": "too low"})

    def test_score_above_range_raises(self):
        with pytest.raises(ValueError, match="out of range"):
            _validate_result({"score": 11, "reasoning": "too high"})

    def test_empty_reasoning_raises(self):
        with pytest.raises(ValueError, match="reasoning was empty"):
            _validate_result({"score": 5, "reasoning": "   "})

    def test_non_dict_raises(self):
        with pytest.raises(ValueError, match="not an object"):
            _validate_result([1, 2, 3])


# ---------------------------------------------------------------------------
# score_event — unit tests with mocked API
# ---------------------------------------------------------------------------

class TestScoreEventMocked:
    def _mock_response(self, payload: dict):
        mock_resp = MagicMock()
        mock_resp.text = json.dumps(payload)
        return mock_resp

    def test_returns_valid_score_and_reasoning(self):
        payload = {"score": 8, "reasoning": "Great fit for user."}
        with patch("llm_client._get_client") as mock_client, \
             patch("llm_client._load_profile", return_value="test profile"):
            mock_client.return_value.models.generate_content.return_value = self._mock_response(payload)
            result = score_event({"title": "Test Event"})
        assert result["score"] == 8
        assert result["reasoning"] == "Great fit for user."

    def test_api_error_returns_fallback(self):
        with patch("llm_client._get_client") as mock_client, \
             patch("llm_client._load_profile", return_value="test profile"):
            mock_client.return_value.models.generate_content.side_effect = RuntimeError("network error")
            result = score_event({"title": "Test Event"})
        assert result["score"] == 0
        assert "scoring failed" in result["reasoning"]

    def test_malformed_json_returns_fallback(self):
        mock_resp = MagicMock()
        mock_resp.text = "not valid json {"
        with patch("llm_client._get_client") as mock_client, \
             patch("llm_client._load_profile", return_value="test profile"):
            mock_client.return_value.models.generate_content.return_value = mock_resp
            result = score_event({"title": "Test Event"})
        assert result["score"] == 0
        assert "scoring failed" in result["reasoning"]

    def test_out_of_range_score_returns_fallback(self):
        payload = {"score": 99, "reasoning": "way too high"}
        with patch("llm_client._get_client") as mock_client, \
             patch("llm_client._load_profile", return_value="test profile"):
            mock_client.return_value.models.generate_content.return_value = self._mock_response(payload)
            result = score_event({"title": "Test Event"})
        assert result["score"] == 0


# ---------------------------------------------------------------------------
# score_event — integration test
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestScoreEventIntegration:
    SAMPLE_EVENT = {
        "title": "Embedded Systems Hackathon",
        "event_type": "hackathon",
        "source": "devpost.com",
        "url": "https://example.com/embedded-hack",
        "deadline": "2026-07-01",
        "start_date": "2026-07-15",
        "location": "Auckland",
        "themes": "embedded systems, firmware, hardware",
    }

    def test_score_event_returns_valid_result(self):
        result = score_event(self.SAMPLE_EVENT)
        assert isinstance(result["score"], int), f"score not int: {result}"
        assert 1 <= result["score"] <= 10, f"score out of range: {result}"
        assert isinstance(result["reasoning"], str)
        assert len(result["reasoning"]) > 0

    def test_score_event_irrelevant_event(self):
        irrelevant = {
            "title": "Underwater Basket Weaving Championship",
            "event_type": "competition",
            "location": "Remote",
            "themes": "crafts, weaving",
        }
        result = score_event(irrelevant)
        assert 1 <= result["score"] <= 10
        assert result["reasoning"]
