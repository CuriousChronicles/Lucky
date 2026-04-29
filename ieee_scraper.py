from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

URL = "https://linktr.ee/ieee.uoa"

def fetch_rendered_html(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(url)

        page.wait_for_selector('[data-testid="NewLinkContainer"]', timeout=15000)

        page.screenshot(path="debug_final.png", full_page=True)
        html = page.content()
        browser.close()
    return html

def parse_links(html):
    # TODO: currently this gives me all the links available, I only want the links to
    #       the event sign-ups
    soup = BeautifulSoup(html, "lxml")
    containers = soup.select('[data-testid="NewLinkContainer"]')
    print(f"DEBUG: found {len(containers)} link containers")

    links = []
    for container in containers:
        anchor = container.select_one('[data-testid="LinkClickTriggerLink"]')
        chin = container.select_one('[data-testid="NewLinkChin"]')
        title_el = chin.select_one('div.line-clamp-2') if chin else None

        links.append({
            "title": title_el.text.strip() if title_el else None,
            "url": anchor.get("href") if anchor else None,
        })

    return links

def main():
    print("Fetching Linktree page...")
    html = fetch_rendered_html(URL)

    links = parse_links(html)
    print(f"\nFound {len(links)} links:\n")
    for link in links:
        print(f"  • {link['title']}")
        print(f"    {link['url']}\n")

if __name__ == "__main__":
    main()
