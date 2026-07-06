"""
Leffingwell & Associates Odor Reference Scraper
=================================================
Scrapes the Leffingwell odor reference database, which contains
~800 odorant molecules with odor descriptors, chemical names,
and CAS numbers. One of the oldest and most respected fragrance
chemical databases.

URL: http://www.leffingwell.com
"""

import re
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict, field

import requests
from bs4 import BeautifulSoup

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import RAW_DIR, ODOR_TYPE_TO_FAMILY

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

LEFFINGWELL_BASE = "http://www.leffingwell.com"


@dataclass
class LeffingwellMolecule:
    """A molecule entry from Leffingwell's database."""
    name: str
    cas_number: str = ""
    odor_descriptors: List[str] = field(default_factory=list)
    odor_families: List[str] = field(default_factory=list)
    molecular_formula: str = ""
    source_url: str = ""


class LeffingwellScraper:
    """Scraper for Leffingwell odor reference data."""

    def __init__(self, rate_limit: float = 1.0):
        self.rate_limit = rate_limit
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        })

    def _fetch(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch a URL with rate limiting."""
        try:
            time.sleep(self.rate_limit)
            resp = self.session.get(url, timeout=30)
            resp.raise_for_status()
            return BeautifulSoup(resp.text, "html.parser")
        except Exception as e:
            logger.warning(f"Failed to fetch {url}: {e}")
            return None

    def scrape_odor_directory(self) -> List[LeffingwellMolecule]:
        """
        Scrape the Leffingwell odor directory pages.
        Leffingwell organizes molecules by odor type with pages like:
        - /odors.htm (main listing)
        - /floral.htm, /fruity.htm, etc.
        """
        molecules = []
        seen_cas = set()

        # Main odor listing page
        soup = self._fetch(f"{LEFFINGWELL_BASE}/odors.htm")
        if not soup:
            # Try alternate URLs
            soup = self._fetch(f"{LEFFINGWELL_BASE}/odorref.htm")
        if not soup:
            logger.warning("Could not reach Leffingwell main page, trying individual odor pages")

        if soup:
            # Parse the main table for molecule entries
            for row in soup.find_all("tr"):
                cells = row.find_all("td")
                if len(cells) >= 2:
                    name_text = cells[0].get_text(strip=True)
                    odor_text = cells[1].get_text(strip=True) if len(cells) > 1 else ""

                    # Look for CAS numbers
                    cas_match = re.search(r'(\d{2,7}-\d{2}-\d)', name_text)
                    if cas_match:
                        cas = cas_match.group(1)
                        name = name_text.replace(cas, "").strip().rstrip(",").strip()
                        if cas not in seen_cas:
                            seen_cas.add(cas)
                            descriptors = [d.strip().lower() for d in re.split(r'[;,]', odor_text) if d.strip()]
                            families = []
                            for desc in descriptors:
                                family = ODOR_TYPE_TO_FAMILY.get(desc, None)
                                if family and family not in families:
                                    families.append(family)

                            molecules.append(LeffingwellMolecule(
                                name=name,
                                cas_number=cas,
                                odor_descriptors=descriptors,
                                odor_families=families,
                                source_url=f"{LEFFINGWELL_BASE}/odors.htm",
                            ))

        # Also scrape individual odor-type pages
        odor_pages = [
            "floral", "fruity", "citrus", "spicy", "woody", "green",
            "herbal", "amber", "musk", "earthy", "powdery", "leather",
            "aldehydic", "aquatic", "gourmand",
        ]

        for odor_type in odor_pages:
            url = f"{LEFFINGWELL_BASE}/{odor_type}.htm"
            soup = self._fetch(url)
            if not soup:
                continue

            # Parse tables on each page
            for row in soup.find_all("tr"):
                cells = row.find_all("td")
                if len(cells) >= 2:
                    full_text = row.get_text()
                    cas_match = re.search(r'(\d{2,7}-\d{2}-\d)', full_text)
                    if cas_match:
                        cas = cas_match.group(1)
                        if cas in seen_cas:
                            continue
                        seen_cas.add(cas)

                        # Extract name from first cell
                        name = cells[0].get_text(strip=True)
                        # Clean up name (remove CAS, brackets, etc.)
                        name = re.sub(r'\d{2,7}-\d{2}-\d', '', name).strip()
                        name = re.sub(r'[()[\]]', '', name).strip()

                        # Extract odor descriptors from all text
                        descriptors = [d.strip().lower() for d in re.split(r'[;,]', full_text)
                                       if d.strip() and len(d.strip()) > 1 and not re.match(r'\d', d.strip())]

                        # Map to families
                        families = [odor_type]
                        for desc in descriptors:
                            family = ODOR_TYPE_TO_FAMILY.get(desc, None)
                            if family and family not in families:
                                families.append(family)

                        molecules.append(LeffingwellMolecule(
                            name=name,
                            cas_number=cas,
                            odor_descriptors=descriptors,
                            odor_families=families,
                            source_url=url,
                        ))

            # Also check for links to molecule sub-pages
            for link in soup.find_all("a", href=True):
                href = link["href"]
                if href.endswith(".htm") and "data" not in href.lower():
                    name = link.get_text(strip=True)
                    if name and len(name) > 2:
                        cas_match = re.search(r'(\d{2,7}-\d{2}-\d)', name)
                        if cas_match:
                            cas = cas_match.group(1)
                            if cas not in seen_cas:
                                seen_cas.add(cas)
                                molecules.append(LeffingwellMolecule(
                                    name=name.replace(cas, "").strip(),
                                    cas_number=cas,
                                    odor_descriptors=[odor_type],
                                    odor_families=[odor_type],
                                    source_url=f"{LEFFINGWELL_BASE}/{href}",
                                ))

        logger.info(f"Leffingwell: found {len(molecules)} molecules")
        return molecules

    def scrape_olfaction_charts(self) -> List[LeffingwellMolecule]:
        """
        Scrape the Leffingwell olfaction/chemoreception charts.
        These contain additional molecules with odor thresholds.
        """
        molecules = []
        seen_cas = set()

        # Olfaction chart page
        url = f"{LEFFINGWELL_BASE}/olfact3.htm"
        soup = self._fetch(url)
        if not soup:
            url = f"{LEFFINGWELL_BASE}/olfaction.htm"
            soup = self._fetch(url)

        if not soup:
            logger.warning("Could not fetch olfaction charts")
            return molecules

        # Parse tables
        for row in soup.find_all("tr"):
            text = row.get_text()
            cas_match = re.search(r'(\d{2,7}-\d{2}-\d)', text)
            if cas_match:
                cas = cas_match.group(1)
                if cas not in seen_cas:
                    seen_cas.add(cas)
                    cells = row.find_all("td")
                    name = cells[0].get_text(strip=True) if cells else ""
                    name = re.sub(r'\d{2,7}-\d{2}-\d', '', name).strip()

                    odor_text = " ".join(c.get_text() for c in cells[1:]) if len(cells) > 1 else ""
                    descriptors = [d.strip().lower() for d in re.split(r'[;,]', odor_text) if d.strip()]

                    families = []
                    for desc in descriptors:
                        family = ODOR_TYPE_TO_FAMILY.get(desc, None)
                        if family and family not in families:
                            families.append(family)

                    molecules.append(LeffingwellMolecule(
                        name=name,
                        cas_number=cas,
                        odor_descriptors=descriptors,
                        odor_families=families,
                        source_url=url,
                    ))

        logger.info(f"Leffingwell olfaction charts: found {len(molecules)} molecules")
        return molecules


def save_leffingwell(molecules: List[LeffingwellMolecule], filepath: str):
    """Save Leffingwell molecules to JSONL."""
    with open(filepath, "w", encoding="utf-8") as f:
        for mol in molecules:
            f.write(json.dumps(asdict(mol), ensure_ascii=False) + "\n")
    logger.info(f"Saved {len(molecules)} Leffingwell molecules to {filepath}")


if __name__ == "__main__":
    scraper = LeffingwellScraper()
    molecules = scraper.scrape_odor_directory()
    output_file = os.path.join(RAW_DIR, "leffingwell_molecules.jsonl")
    save_leffingwell(molecules, output_file)

import os