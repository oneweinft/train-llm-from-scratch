"""
Basenotes Scraper
==================
Scrapes supplementary perfume data from basenotes.net:
- Perfume directory with note listings
- Fragrance reviews and community ratings
- Community discussions on fragrance composition

Usage:
    python -m scrapers.basenotes_scraper [--search QUERY] [--max-pages N]
"""

import re
import json
import time
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict, field

import requests
from bs4 import BeautifulSoup

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import (
    BASENOTES_BASE_URL, BASENOTES_RATE_LIMIT_SECONDS,
    BASENOTES_PERFUMES_FILE, RAW_DIR,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class BasenotesPerfume:
    """Supplementary perfume data from Basenotes."""
    name: str
    brand: str
    year: Optional[int] = None
    gender: Optional[str] = None
    fragrance_family: Optional[str] = None
    top_notes: List[str] = field(default_factory=list)
    middle_notes: List[str] = field(default_factory=list)
    base_notes: List[str] = field(default_factory=list)
    description: str = ""
    average_rating: Optional[float] = None
    num_reviews: Optional[int] = None
    url: str = ""


class BasenotesScraper:
    """Scraper for Basenotes fragrance database."""

    def __init__(self, rate_limit: float = BASENOTES_RATE_LIMIT_SECONDS):
        self.rate_limit = rate_limit
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        })

    def _fetch(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch a URL with retries and rate limiting."""
        for attempt in range(3):
            try:
                time.sleep(self.rate_limit)
                resp = self.session.get(url, timeout=30)
                if resp.status_code == 403:
                    time.sleep(self.rate_limit * 5)
                    continue
                resp.raise_for_status()
                return BeautifulSoup(resp.text, "html.parser")
            except requests.RequestException as e:
                logger.warning(f"Attempt {attempt+1} failed for {url}: {e}")
                time.sleep(self.rate_limit * 2)
        return None

    def scrape_directory_page(self, page: int = 1) -> List[str]:
        """Scrape a directory listing page and return perfume URLs."""
        url = f"{BASENOTES_BASE_URL}/fragrances/?page={page}"
        soup = self._fetch(url)
        if not soup:
            return []

        perfume_urls = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "/fragrances/" in href and href not in perfume_urls:
                full_url = href if href.startswith("http") else f"{BASENOTES_BASE_URL}{href}"
                perfume_urls.append(full_url)

        return perfume_urls

    def scrape_perfume_page(self, url: str) -> Optional[BasenotesPerfume]:
        """Scrape a single perfume page from Basenotes."""
        soup = self._fetch(url)
        if not soup:
            return None

        perfume = BasenotesPerfume(name="", brand="", url=url)
        text = soup.get_text()

        # Extract name and brand from title
        title = soup.find("h1")
        if title:
            full_title = title.get_text(strip=True)
            parts = full_title.split(" by ", 1)
            if len(parts) == 2:
                perfume.brand = parts[0].strip()
                perfume.name = parts[1].strip()
            else:
                perfume.name = full_title

        # Extract notes
        for label, attr in [("top", "top_notes"), ("middle", "middle_notes"), ("base", "base_notes")]:
            pattern = rf'{label}\s+notes?\s*:?\s*([^.\n]+)'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                notes = [n.strip() for n in re.split(r'[,;]', match.group(1)) if n.strip()]
                getattr(perfume, attr).extend(notes)

        # Extract rating
        rating_match = re.search(r'(\d+\.?\d*)\s*/\s*5', text)
        if rating_match:
            perfume.average_rating = float(rating_match.group(1))

        return perfume


def save_perfume(perfume: BasenotesPerfume, filepath: str):
    """Append a perfume to the JSONL file."""
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(perfume), ensure_ascii=False) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Basenotes Perfume Scraper")
    parser.add_argument("--search", type=str, default=None)
    parser.add_argument("--max-pages", type=int, default=5)
    parser.add_argument("--output-dir", type=str, default=RAW_DIR)
    args = parser.parse_args()

    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    scraper = BasenotesScraper()
    output_file = os.path.join(args.output_dir, "basenotes_perfumes.jsonl")

    for page in range(1, args.max_pages + 1):
        logger.info(f"Scraping directory page {page}...")
        urls = scraper.scrape_directory_page(page)
        for url in urls:
            perfume = scraper.scrape_perfume_page(url)
            if perfume and perfume.name:
                save_perfume(perfume, output_file)
                logger.info(f"Saved: {perfume.brand} - {perfume.name}")


import os

if __name__ == "__main__":
    main()
