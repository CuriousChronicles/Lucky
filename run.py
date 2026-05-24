"""
Main orchestrator for Jarvis. Runs all scrapers and reports results.
This is what gets called by the scheduler every morning.
"""
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

from database import get_unscored_events, mark_all_seen, remove_expired_events, update_event_score
from devpost_scraper import scrape_devpost
from llm_client import score_event
from notifier import send_notification

# TODO: 
# - Be able to know how many new events were found today 

# ============================================================================
# Logging setup
# ============================================================================
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / f"lucky_{datetime.now():%Y-%m-%d}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        # logging.StreamHandler(sys.stdout),
    ]
)
log = logging.getLogger("lucky")


# ============================================================================
# Scraper registry
# Add new scrapers here.
# ============================================================================
SCRAPERS = [
    ("devpost", scrape_devpost),
]
SCORE_DELAY_SECONDS = 7


def notify_run_complete(results, total_tiles, total_new, failed):
    """Send a phone notification summarizing the run."""
    if failed:
        send_notification(
            title="Lucky run completed with errors",
            message=f"{len(failed)} scraper(s) failed — check the logs.",
            priority="default",
            tags=["warning"],
        )
    else:
        send_notification(
            title="Lucky run complete",
            message=f"{total_new} new events found ({total_tiles} total across {len(results)} sites).",
            priority="default",
            tags=["white_check_mark"],
        )

def score_unscored_events() -> int:
    """Score events that were inserted without relevance data."""
    unscored_events = get_unscored_events()
    if not unscored_events:
        log.info("No unscored events found")
        return 0

    log.info(f"Scoring {len(unscored_events)} unscored event(s)...")
    scored_count = 0

    for index, event in enumerate(unscored_events):
        url = event.get("url")
        title = event.get("title", url)
        if not url:
            log.warning(f"Skipping unscored event without URL: {title}")
            continue

        result = score_event(event)
        status = result.get("status", "ok")
        score = result["score"] if status == "ok" else None
        update_event_score(url, score, result["reasoning"], status)

        if status == "ok":
            scored_count += 1
            log.info(f"Scored event {title or url}: {result['score']}/10")
        else:
            log.warning(f"Scoring failed for {title or url}: {status}")

        if index < len(unscored_events) - 1:
            time.sleep(SCORE_DELAY_SECONDS)

    return scored_count

def run_all():
    """Run every scraper. One failure doesn't stop the others."""
    run_start = datetime.now()

    log.info("=" * 60)
    log.info(f"Lucky run started - {run_start:%Y-%m-%d %H:%M:%S}")
    seen_count = mark_all_seen()
    log.info(f"Marked {seen_count} existing event(s) as seen")

    expired_count = remove_expired_events()
    log.info(f"Removed {expired_count} expired event(s)")

    results = []

    for name, scraper_fn in SCRAPERS:
        log.info(f"[{name}] Starting scraper...")
        scraper_start = datetime.now()
        try:
            result = scraper_fn()
            elapsed = (datetime.now() - scraper_start).total_seconds()
            tiles = result.get("total_found", 0)
            new = result.get("new_found", 0)
            log.info(f"[{name}] Done - {tiles} tiles found ({new} new) in {elapsed:.1f}s")
            results.append(result)
        except Exception as e:
            elapsed = (datetime.now() - scraper_start).total_seconds()
            log.error(f"[{name}] FAILED after {elapsed:.1f}s - {e}", exc_info=True)
            results.append({"scraper": name, "error": str(e)})

    scored_count = score_unscored_events()

    # Summary
    total_elapsed = (datetime.now() - run_start).total_seconds()
    total_tiles = sum(r.get("total_found", 0) for r in results)
    total_new = sum(r.get("new_found", 0) for r in results)
    failed = [r["scraper"] for r in results if "error" in r]

    log.info("-" * 60)
    log.info(f"Run finished in {total_elapsed:.1f}s")
    log.info(f"  Tiles found : {total_tiles} ({total_new} new)")
    log.info(f"  Scored      : {scored_count}")
    log.info(f"  Scrapers run: {len(results)}")
    if failed:
        log.error(f"  Failed      : {', '.join(failed)}")
    else:
        log.info(f"  Errors      : none")
    log.info("=" * 60)


    notify_run_complete(results, total_tiles, total_new, failed)

    return results

if __name__ == "__main__":
    run_all()
