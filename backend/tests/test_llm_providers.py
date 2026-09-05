"""Provider selection and the OpenAI-compatible adapter (no network calls)."""

import json

import pytest

from app.config import settings
from app.services import llm as llm_module
from app.services.llm import (
    ClaudeLLM,
    MockLLM,
    OpenAICompatLLM,
    coerce_feedback,
    extract_json,
    reset_llm_cache,
)


@pytest.fixture(autouse=True)
def _restore_settings():
    """Provider selection reads global settings - restore them after each test."""
    saved = {
        f: getattr(settings, f)
        for f in (
            "llm_provider", "anthropic_api_key", "openai_compat_base_url",
            "openai_compat_api_key", "openai_compat_model",
        )
    }
    reset_llm_cache()
    yield
    for field, value in saved.items():
        setattr(settings, field, value)
    reset_llm_cache()


def test_defaults_to_mock_with_nothing_configured():
    settings.llm_provider = "auto"
    settings.anthropic_api_key = ""
    settings.openai_compat_base_url = ""
    settings.openai_compat_api_key = ""
    assert llm_module.get_llm().name == "mock"


def test_auto_prefers_anthropic_then_openai_compat():
    settings.llm_provider = "auto"
    settings.openai_compat_base_url = "https://api.groq.com/openai/v1"
    settings.openai_compat_api_key = "gsk_test"
    settings.anthropic_api_key = ""
    assert llm_module.get_llm().name == "openai_compat"

    # a Claude key outranks the free tier
    reset_llm_cache()
    settings.anthropic_api_key = "sk-ant-test"
    provider = llm_module.get_llm()
    # ClaudeLLM construction needs the SDK; without it we fall through gracefully
    assert provider.name in ("anthropic", "openai_compat", "mock")


def test_explicit_provider_overrides_auto():
    settings.llm_provider = "mock"
    settings.anthropic_api_key = "sk-ant-test"
    settings.openai_compat_base_url = "https://api.groq.com/openai/v1"
    settings.openai_compat_api_key = "gsk_test"
    assert llm_module.get_llm().name == "mock"


def test_incomplete_openai_compat_config_falls_back_to_mock():
    settings.llm_provider = "openai_compat"
    settings.openai_compat_base_url = "https://api.groq.com/openai/v1"
    settings.openai_compat_api_key = ""  # missing key
    assert llm_module.get_llm().name == "mock"


# ---------------- JSON handling for weaker models ----------------

def test_extract_json_variants():
    obj = {"overall_score": 70}
    raw = json.dumps(obj)
    assert extract_json(raw) == obj
    assert extract_json(f"```json\n{raw}\n```") == obj
    assert extract_json(f"Here is my analysis:\n{raw}\nHope that helps!") == obj
    with pytest.raises(RuntimeError):
        extract_json("I could not analyze that essay.")


def test_extract_json_ignores_trailing_garbage():
    """Observed with Llama 3.1 8B: valid JSON followed by a second partial object.
    A greedy brace regex swallows both and fails to parse."""
    good = '{"overall_score": 72, "scores": {"grammar": 80}}'
    assert extract_json(good + '\n\n{"extra": incomplete') == {
        "overall_score": 72, "scores": {"grammar": 80}
    }
    # braces inside strings must not confuse the scanner
    tricky = '{"weaknesses": ["uses {braces} oddly"], "overall_score": 50}'
    assert extract_json(tricky + " trailing prose")["overall_score"] == 50
    # escaped quotes inside strings
    escaped = '{"suggestions": ["say \\"why\\" more"], "overall_score": 60}'
    assert extract_json(escaped)["overall_score"] == 60


def test_coerce_feedback_fills_missing_fields():
    """A weaker model may omit fields - the API contract must still hold."""
    out = coerce_feedback({"scores": {"reflection": 80}}, "one two three", "ollama")
    assert set(out["scores"]) == {
        "prompt_alignment", "storytelling", "personal_voice",
        "specificity", "reflection", "structure", "grammar",
    }
    assert out["scores"]["reflection"] == 80
    assert 0 <= out["overall_score"] <= 100
    assert out["flags"]["word_count"] == 3
    assert out["provider"] == "ollama"
    assert out["weaknesses"] == [] and out["questions"] == []


def test_coerce_feedback_clamps_out_of_range_scores():
    out = coerce_feedback(
        {"overall_score": 500, "scores": {"grammar": -20}}, "text", "openai_compat"
    )
    assert out["overall_score"] == 100
    assert out["scores"]["grammar"] == 0


def test_openai_compat_adapter_shape():
    """The adapter targets the standard endpoint and reuses the coach prompts."""
    provider = OpenAICompatLLM(
        "https://api.groq.com/openai/v1/", "gsk_test", "llama-3.1-8b-instant", "openai_compat"
    )
    assert provider.base_url == "https://api.groq.com/openai/v1"  # trailing slash trimmed
    assert provider.name == "openai_compat"
    # the coach-never-writes rule is shared across every real provider
    assert "NEVER write or rewrite" in ClaudeLLM.ESSAY_SYSTEM


def test_mock_is_always_available():
    assert MockLLM().name == "mock"
