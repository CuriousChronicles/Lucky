import json
import os
import time
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types


MODEL = "gemini-2.5-flash"
BASE_DIR = Path(__file__).parent
PROFILE_PATH = BASE_DIR / "profile.md"
RATE_LIMIT_BACKOFF_SECONDS = (2, 4, 8)


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


def _is_rate_limit_error(error: Exception) -> bool:
    status = getattr(error, "status_code", None) or getattr(error, "code", None)
    if status == 429:
        return True

    message = str(error).lower()
    return "429" in message or "rate limit" in message or "resource_exhausted" in message


def _failure_result(status: str, error: Exception) -> dict:
    return {
        "score": 0,
        "reasoning": f"scoring failed: {error}",
        "status": status,
    }


def score_event(event: dict) -> dict:
    """Score an event for relevance. Never raises for LLM/API failures."""
    try:
        profile = _load_profile()
        client = _get_client()
        prompt = _build_prompt(profile, event)
    except Exception as error:
        return _failure_result("api_error", error)

    for attempt in range(len(RATE_LIMIT_BACKOFF_SECONDS) + 1):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json"),
            )
            return {**_validate_result(json.loads(response.text)), "status": "ok"}
        except (json.JSONDecodeError, ValueError) as error:
            return _failure_result("parse_error", error)
        except Exception as error:
            if not _is_rate_limit_error(error):
                return _failure_result("api_error", error)

            if attempt == len(RATE_LIMIT_BACKOFF_SECONDS):
                return _failure_result("rate_limited", error)

            time.sleep(RATE_LIMIT_BACKOFF_SECONDS[attempt])
