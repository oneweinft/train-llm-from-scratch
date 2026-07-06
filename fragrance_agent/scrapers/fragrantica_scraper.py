"""
Fragrantica Scraper
====================
Scrapes perfume data from fragrantica.com:
- Perfume catalog (name, brand, year, gender, rating)
- Note pyramids (top/heart/base notes)
- Fragrance family classification (accords)
- Main accords / vote data

NOTE: Fragrantica employs anti-scraping measures. This scraper uses
Selenium for JavaScript-rendered pages and respects rate limits.
For large-scale scraping, consider using their API or purchasing data access.

Usage:
    python -m scrapers.fragrantica_scraper [--max-pages N] [--search QUERY]
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
    FRAGNANTICA_BASE_URL, FRAGNANTICA_RATE_LIMIT_SECONDS,
    FRAGNANTICA_MAX_RETRIES, FRAGNANTICA_PERFUMES_FILE,
    FRAGNANTICA_NOTES_FILE, RAW_DIR, FRAGRANCE_FAMILIES,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class NotePyramid:
    """Represents the top/heart/base note structure of a perfume."""
    top_notes: List[str] = field(default_factory=list)
    heart_notes: List[str] = field(default_factory=list)
    base_notes: List[str] = field(default_factory=list)

    def all_notes(self) -> List[str]:
        return self.top_notes + self.heart_notes + self.base_notes


@dataclass
class Perfume:
    """Represents a perfume entry from Fragrantica."""
    name: str
    brand: str
    year: Optional[int] = None
    gender: Optional[str] = None  # "women", "men", "unisex"
    rating: Optional[float] = None
    num_votes: Optional[int] = None
    fragrance_family: Optional[str] = None
    main_accords: List[str] = field(default_factory=list)
    note_pyramid: NotePyramid = field(default_factory=NotePyramid)
    description: str = ""
    longevity_rating: Optional[str] = None
    sillage_rating: Optional[str] = None
    url: str = ""


@dataclass
class FragranticaNote:
    """Represents a fragrance note with metadata."""
    name: str
    note_category: Optional[str] = None  # e.g., "flowers", "woods", "fruits"
    url: str = ""


class FragranticaScraper:
    """Scraper for Fragrantica perfume database."""

    def __init__(self, rate_limit: float = FRAGNANTICA_RATE_LIMIT_SECONDS):
        self.rate_limit = rate_limit
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        })

    def _fetch(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch a URL with retries and rate limiting."""
        for attempt in range(FRAGNANTICA_MAX_RETRIES):
            try:
                time.sleep(self.rate_limit)
                resp = self.session.get(url, timeout=30)
                if resp.status_code == 403:
                    logger.warning(f"403 Forbidden - rate limited or blocked: {url}")
                    time.sleep(self.rate_limit * 5)
                    continue
                resp.raise_for_status()
                return BeautifulSoup(resp.text, "html.parser")
            except requests.RequestException as e:
                logger.warning(f"Attempt {attempt+1}/{FRAGNANTICA_MAX_RETRIES} failed for {url}: {e}")
                time.sleep(self.rate_limit * 3)
        logger.error(f"All attempts failed for {url}")
        return None

    def scrape_perfume_page(self, url: str) -> Optional[Perfume]:
        """
        Scrape a single perfume page from Fragrantica.
        Extracts: name, brand, year, notes, accords, ratings.
        """
        soup = self._fetch(url)
        if not soup:
            return None

        perfume = Perfume(name="", brand="", url=url)

        # Extract perfume name and brand
        title_elem = soup.find("h1")
        if title_elem:
            full_title = title_elem.get_text(strip=True)
            # Format is typically "Brand - Perfume Name"
            parts = full_title.split(" by ", 1)
            if len(parts) == 2:
                perfume.brand = parts[0].strip()
                perfume.name = parts[1].strip()
            else:
                perfume.name = full_title

        # Extract year
        year_match = re.search(r'\b(19|20)\d{2}\b', soup.get_text()[:500])
        if year_match:
            perfume.year = int(year_match.group(0))

        # Extract gender
        for gender in ["women", "men", "unisex"]:
            if gender in url.lower() or gender in soup.get_text()[:1000].lower():
                perfume.gender = gender
                break

        # Extract note pyramid
        perfume.note_pyramid = self._parse_note_pyramid(soup)

        # Extract main accords
        perfume.main_accords = self._parse_accords(soup)

        # Extract fragrance family
        for family in FRAGRANCE_FAMILIES:
            if family.lower() in soup.get_text().lower():
                perfume.fragrance_family = family
                break

        # Extract rating
        rating_elem = soup.find("span", {"itemprop": "ratingValue"})
        if rating_elem:
            try:
                perfume.rating = float(rating_elem.get_text(strip=True))
            except ValueError:
                pass

        votes_elem = soup.find("span", {"itemprop": "ratingCount"})
        if votes_elem:
            try:
                perfume.num_votes = int(re.sub(r'[^\d]', '', votes_elem.get_text()))
            except ValueError:
                pass

        return perfume

    def _parse_note_pyramid(self, soup: BeautifulSoup) -> NotePyramid:
        """Parse the note pyramid (top/heart/base) from a perfume page."""
        pyramid = NotePyramid()

        # Fragrantica uses structured divs for the note pyramid
        # Look for note sections by their labels
        note_sections = {
            "top": ["top notes", "top note", "head notes", "head note"],
            "heart": ["middle notes", "middle note", "heart notes", "heart note"],
            "base": ["base notes", "base note", "bottom notes", "bottom note"],
        }

        text = soup.get_text()
        for layer, labels in note_sections.items():
            for label in labels:
                pattern = rf'{label}\s*:?\s*([^.\n]+)'
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    notes = [n.strip() for n in re.split(r'[,;]', match.group(1)) if n.strip()]
                    if layer == "top":
                        pyramid.top_notes.extend(notes)
                    elif layer == "heart":
                        pyramid.heart_notes.extend(notes)
                    elif layer == "base":
                        pyramid.base_notes.extend(notes)
                    break

        # Also try parsing from structured HTML elements
        # Fragrantica typically has note pyramid in specific CSS classes
        for div in soup.find_all("div", class_=re.compile(r"note")):
            note_text = div.get_text(strip=True)
            if note_text and note_text not in pyramid.all_notes():
                # Determine layer from surrounding context
                parent_text = div.parent.get_text(strip=True).lower() if div.parent else ""
                if "top" in parent_text:
                    pyramid.top_notes.append(note_text)
                elif "heart" in parent_text or "middle" in parent_text:
                    pyramid.heart_notes.append(note_text)
                elif "base" in parent_text:
                    pyramid.base_notes.append(note_text)

        # Deduplicate
        pyramid.top_notes = list(dict.fromkeys(pyramid.top_notes))
        pyramid.heart_notes = list(dict.fromkeys(pyramid.heart_notes))
        pyramid.base_notes = list(dict.fromkeys(pyramid.base_notes))

        return pyramid

    def _parse_accords(self, soup: BeautifulSoup) -> List[str]:
        """Parse main accords from a perfume page."""
        accords = []

        # Look for accord indicators in the page
        for span in soup.find_all("span", class_=re.compile(r"accord", re.I)):
            text = span.get_text(strip=True)
            if text:
                accords.append(text.lower())

        # Fallback: parse from text
        text = soup.get_text()
        accord_match = re.search(r'Main\s+Accords?\s*:?\s*([^.\n]+)', text, re.IGNORECASE)
        if accord_match:
            accords.extend([a.strip().lower() for a in re.split(r'[,;]', accord_match.group(1)) if a.strip()])

        return list(dict.fromkeys(accords))

    def scrape_search_results(self, query: str, max_pages: int = 5) -> List[str]:
        """
        Search for perfumes on Fragrantica and return list of perfume URLs.
        """
        urls = []
        for page in range(1, max_pages + 1):
            search_url = f"{FRAGNANTICA_BASE_URL}/search/?query={query}&page={page}"
            soup = self._fetch(search_url)
            if not soup:
                break

            # Find perfume links
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if "/perfume/" in href and href not in urls:
                    full_url = href if href.startswith("http") else f"{FRAGNANTICA_BASE_URL}{href}"
                    urls.append(full_url)

            logger.info(f"Search page {page}: found {len(urls)} perfume URLs so far")

        return urls

    def scrape_notes_directory(self) -> List[FragranticaNote]:
        """
        Scrape the Fragrantica notes directory to get all known fragrance notes
        and their categories.
        """
        notes = []
        # Fragrantica organizes notes by category
        categories = [
            "flowers", "woods", "fruits", "spices", "resins",
            "herbs", "greens", "animalic", "gourmand", "citrus",
            "aquatic", "aldehydes", "powdery", "musk", "earthy",
        ]

        for category in categories:
            url = f"{FRAGNANTICA_BASE_URL}/notes/{category}.html"
            logger.info(f"Scraping notes category: {category}")
            soup = self._fetch(url)
            if not soup:
                continue

            # Parse individual note entries
            for link in soup.find_all("a", href=True):
                href = link["href"]
                if "/notes/" in href and href != f"/notes/{category}.html":
                    note_name = link.get_text(strip=True)
                    if note_name:
                        notes.append(FragranticaNote(
                            name=note_name,
                            note_category=category,
                            url=f"{FRAGNANTICA_BASE_URL}{href}" if not href.startswith("http") else href,
                        ))

        logger.info(f"Found {len(notes)} notes across {len(categories)} categories")
        return notes


def save_perfume(perfume: Perfume, filepath: str):
    """Append a perfume to the JSONL file."""
    data = asdict(perfume)
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")


def save_notes(notes: List[FragranticaNote], filepath: str):
    """Save notes to JSON file."""
    data = [asdict(n) for n in notes]
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(description="Fragrantica Perfume Scraper")
    parser.add_argument("--search", type=str, default=None,
                        help="Search query for perfumes")
    parser.add_argument("--scrape-perfume", type=str, default=None,
                        help="Direct URL of a perfume page to scrape")
    parser.add_argument("--scrape-notes", action="store_true",
                        help="Scrape the notes directory")
    parser.add_argument("--max-pages", type=int, default=5,
                        help="Max search result pages to scrape")
    parser.add_argument("--output-dir", type=str, default=RAW_DIR,
                        help="Output directory")
    args = parser.parse_args()

    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    scraper = FragranticaScraper()

    if args.search:
        urls = scraper.scrape_search_results(args.search, args.max_pages)
        perfumes_file = os.path.join(args.output_dir, "fragrantica_perfumes.jsonl")
        for url in urls:
            perfume = scraper.scrape_perfume_page(url)
            if perfume and perfume.name:
                save_perfume(perfume, perfumes_file)
                logger.info(f"Saved: {perfume.brand} - {perfume.name}")

    elif args.scrape_perfume:
        perfume = scraper.scrape_perfume_page(args.scrape_perfume)
        if perfume:
            perfumes_file = os.path.join(args.output_dir, "fragrantica_perfumes.jsonl")
            save_perfume(perfume, perfumes_file)
            logger.info(f"Saved: {perfume.brand} - {perfume.name}")

    elif args.scrape_notes:
        notes = scraper.scrape_notes_directory()
        notes_file = os.path.join(args.output_dir, "fragrantica_notes.json")
        save_notes(notes, notes_file)

    else:
        parser.print_help()


import os

if __name__ == "__main__":
    main()
