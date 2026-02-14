from fastapi import FastAPI
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from readability import Document
import requests
import re

app = FastAPI()

def get_google_results(keyword):
    results = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage"]
            )
            page = browser.new_page()
            page.goto(f"https://www.google.com/search?q={keyword}", timeout=60000)
            page.wait_for_timeout(5000)

            links = page.query_selector_all("h3")
            for link in links[:10]:
                parent = link.evaluate_handle("node => node.closest('a')")
                if parent:
                    url = parent.get_attribute("href")
                    if url and url.startswith("http"):
                        results.append(url)

            browser.close()

    except Exception as e:
        print("ERROR:", e)

    return results


def analyze_page(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        html = requests.get(url, headers=headers, timeout=10).text

        doc = Document(html)
        content_html = doc.summary()

        soup = BeautifulSoup(content_html, "html.parser")

        title = doc.title()

        h1 = [h.get_text().strip() for h in soup.find_all("h1")]
        h2 = [h.get_text().strip() for h in soup.find_all("h2")]
        h3 = [h.get_text().strip() for h in soup.find_all("h3")]

        text = soup.get_text()
        words = len(re.findall(r"\w+", text))

        return {
            "title": title,
            "h1": h1,
            "h2": h2,
            "h3": h3,
            "word_count": words,
            "url": url
        }

    except:
        return None


def generate_blueprint(pages):
    all_h2 = []
    word_counts = []

    for page in pages:
        all_h2.extend(page["h2"])
        word_counts.append(page["word_count"])

    common_sections = list(set(all_h2))[:10]
    avg_words = int(sum(word_counts) / len(word_counts))

    return {
        "recommended_word_count": avg_words,
        "recommended_sections": common_sections
    }


@app.get("/analyze")
def analyze_keyword(keyword: str):
    urls = get_google_results(keyword)

    pages = []
    for url in urls:
        data = analyze_page(url)
        if data:
            pages.append(data)

    blueprint = generate_blueprint(pages)

    return {
        "keyword": keyword,
        "competitor_analysis": pages,
        "content_blueprint": blueprint
    }
@app.get("/")
def home():
    return {"message": "SEO Reverse Engineer Tool is running"}



