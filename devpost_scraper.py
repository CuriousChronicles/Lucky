"""
Scrapes Devpost for upcoming and online hackathons.
Devpost renders content with Vue.js, so we need a headless browser.

TODO: actually check if your eligible to participate in the hackathon (some have age limit, see hackathon link)
"""

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import pandas as pd
from database import upsert_hackathon

URL = "https://devpost.com/hackathons?challenge_type[]=online&status[]=upcoming"

def fetch_rendered_html(url, max_scrolls=10):
    """Use a headless browser to load the page and let JS run.
    Devpost uses infinte scrolling, so we need to scroll to the bottom.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(url)
        # Wait for the cards to actually appear in the DOM
        page.wait_for_selector("div.hackathon-tile", timeout=15000)

        for i in range(max_scrolls):
            current_count = len(page.query_selector_all("div.hackathon-tile"))

            end_marker = page.query_selector("div.text-center")
            end_visible = end_marker.is_visible() if end_marker else False
            print(f"  Scroll {i}: {current_count} cards | end marker: {end_visible}")

            if end_visible:
                print(f"Reached end of list after {i} scrolls, {current_count} cards found.")
                break

            # page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.mouse.wheel(0, 1500)  # Scroll down by 1500 pixels
            page.wait_for_timeout(1000) 
        else:
            print("You've hit the max scroll limit")

        # Final screenshot for debugging
        page.screenshot(path="debug_final.png", full_page=True)
        html = page.content()
        browser.close()
    return html

def parse_hackathons(html):
    soup = BeautifulSoup(html, "lxml")
    
    # Note: select tiles directly, not the container
    cards = soup.select("div.hackathon-tile")
    print(f"DEBUG: found {len(cards)} cards")
    
    hackathons = []
    for card in cards:
        title_el = card.select_one("h3")
        link_el = card.select_one("a")
        date_el = card.select_one("div.submission-period")
        tags_el = card.select("span.theme-label")

        #TODO: Need to fix start and end date. e.g Jun 6-10, 2026 is read as Jun 6 and 10, 2026 atm
        start_date = deadline = None
        if date_el:
            parts = [p.strip() for p in date_el.text.strip().split(" - ")]
            if len(parts) == 2:
                start_date, deadline = parts
            elif len(parts) == 1:
                start_date = parts[0]
                deadline = parts[0]

        hackathons.append({
            "url": link_el.get("href") if link_el else None,
            "title": title_el.text.strip() if title_el else None,
            "event_type": "hackathon",
            "source": "devpost",
            "deadline": deadline,
            "start_date": start_date,
            "location": "online",
            "themes": ", ".join(el["title"] for el in tags_el) if tags_el else None,
        })

    return hackathons

def main():
    print("Fetching page ...")
    html = fetch_rendered_html(URL)
    
    hackathons = parse_hackathons(html)
    print(f"\nFound {len(hackathons)} hackathons:\n")
    for h in hackathons:
        print(f"  • {h['title']}")
        print(f"    {h['url']}\n")
        print(f"    Submission period: {h['deadline']}")
        print(f"    Themes: {h['themes']}\n")

    # TODO: upsert hackathons into the database
    upsert_hackathon(hackathons)


if __name__ == "__main__":
    main()