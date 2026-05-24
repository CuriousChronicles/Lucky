import json
import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types


MODEL = "gemini-2.5-flash"
BASE_DIR = Path(__file__).parent
PROFILE_PATH = BASE_DIR / "profile.md"


@lru_cache(maxsize=1)
def _load_profile() -> str:
    return PROFILE_PATH.read_text(encoding="utf-8")


@lru_cache(maxsize=1)
def _get_client() -> genai.Client:
    load_dotenv(BASE_DIR / ".env")
    api_key = os.environ["GEMINI_API_KEY"]
    return genai.Client(api_key=api_key)


def _format_event(event: dict) -> str:
    fields = [
        ("Title", event.get("title")),
        ("Type", event.get("event_type")),
        ("Source", event.get("source")),
        ("URL", event.get("url")),
        ("Deadline", event.get("deadline")),
        ("Start date", event.get("start_date")),
        ("Location", event.get("location")),
        ("Themes", event.get("themes")),
    ]
    return "\n".join(f"{label}: {value}" for label, value in fields if value)


def _build_prompt(profile: str, event: dict) -> str:
    return (
        "You are scoring event relevance for a user.\n"
        "Return only JSON in this exact shape: "
        '{"score": <integer 1-10>, "reasoning": "<one sentence>"}.\n'
        "Use the user's scoring rubric and preferences from their profile.\n\n"
        f"User profile:\n{profile}\n\n"
        f"Event details:\n{_format_event(event)}"
    )


def _validate_result(result: dict) -> dict:
    if not isinstance(result, dict):
        raise ValueError("response JSON was not an object")
    if "score" not in result:
        raise ValueError("response missing score")
    if "reasoning" not in result:
        raise ValueError("response missing reasoning")

    score = int(result["score"])
    if not 1 <= score <= 10:
        raise ValueError(f"score out of range: {score}")

    reasoning = str(result["reasoning"]).strip()
    if not reasoning:
        raise ValueError("reasoning was empty")

    return {"score": score, "reasoning": reasoning}


def score_event(event: dict) -> dict:
    """Score an event for relevance. Never raises for LLM/API failures."""
    try:
        profile = _load_profile()
        client = _get_client()
        response = client.models.generate_content(
            model=MODEL,
            contents=_build_prompt(profile, event),
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )
        return _validate_result(json.loads(response.text))
    except Exception as error:
        return {"score": 0, "reasoning": f"scoring failed: {error}"}
