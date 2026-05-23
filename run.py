"""
Main orchestrator for Jarvis. Runs all scrapers and reports results.
This is what gets called by the scheduler every morning.
"""
import logging
import sys
from datetime import datetime
from pathlib import Path

from database import mark_all_seen, remove_expired_events
from devpost_scraper import scrape_devpost
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

    # Summary
    total_elapsed = (datetime.now() - run_start).total_seconds()
    total_tiles = sum(r.get("total_found", 0) for r in results)
    total_new = sum(r.get("new_found", 0) for r in results)
    failed = [r["scraper"] for r in results if "error" in r]

    log.info("-" * 60)
    log.info(f"Run finished in {total_elapsed:.1f}s")
    log.info(f"  Tiles found : {total_tiles} ({total_new} new)")
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
