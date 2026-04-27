"""
Scrapes Devpost for upcoming hackathons.
Devpost renders content with Vue.js, so we need a headless browser.
"""

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

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
        
        hackathons.append({
            "title": title_el.text.strip() if title_el else None,
            "url": link_el.get("href") if link_el else None,
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

if __name__ == "__main__":
    main()