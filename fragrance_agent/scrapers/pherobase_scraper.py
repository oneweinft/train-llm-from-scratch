"""
Pherobase Semiochemical Database Scraper
========================================
Scrapes Pherobase.com, the world's largest database of semiochemicals
(pheromones, allomones, kairomones). Contains ~7000+ compounds with
odor descriptors, CAS numbers, and biological activity data.

Many semiochemicals overlap with fragrance molecules (volatile organic
compounds detected by olfactory receptors). This adds significant
breadth to the agent's molecule knowledge.

URL: http://www.pherobase.net
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

PHEROBASE_BASE = "http://www.pherobase.net"


@dataclass
class PherobaseMolecule:
    """A molecule entry from Pherobase."""
    name: str
    cas_number: str = ""
    odor_descriptors: List[str] = field(default_factory=list)
    odor_families: List[str] = field(default_factory=list)
    molecular_formula: str = ""
    biological_activity: str = ""  # pheromone, allomone, kairomone
    organism: str = ""  # which organism uses it
    source_url: str = ""


class PherobaseScraper:
    """Scraper for Pherobase semiochemical database."""

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

    def scrape_database(self, max_pages: int = 50) -> List[PherobaseMolecule]:
        """
        Scrape Pherobase for semiochemical/odorant molecules.
        The database is organized by compound family and organism.
        """
        molecules = []
        seen_cas = set()

        # Try the main database pages
        urls_to_try = [
            f"{PHEROBASE_BASE}/database/compound.php",
            f"{PHEROBASE_BASE}/",
            f"{PHEROBASE_BASE}/index.html",
        ]

        # Try scraping compound index pages
        for url in urls_to_try:
            soup = self._fetch(url)
            if not soup:
                continue

            # Parse tables
            for table in soup.find_all("table"):
                for row in table.find_all("tr"):
                    cells = row.find_all("td")
                    if len(cells) < 3:
                        continue

                    text = row.get_text()
                    cas_match = re.search(r'(\d{2,7}-\d{2}-\d)', text)
                    if not cas_match:
                        continue

                    cas = cas_match.group(1)
                    if cas in seen_cas:
                        continue
                    seen_cas.add(cas)

                    name = cells[0].get_text(strip=True)
                    name = re.sub(r'\d{2,7}-\d{2}-\d', '', name).strip()

                    formula = ""
                    for cell in cells:
                        formula_match = re.search(r'C\d+H\d+(?:O\d+|N\d+|S\d+)*', cell.get_text())
                        if formula_match:
                            formula = formula_match.group(0)
                            break

                    odor_text = ""
                    for cell in cells[2:]:
                        cell_text = cell.get_text(strip=True).lower()
                        if any(kw in cell_text for kw in ["odor", "smell", "aroma", "volatile", "pheromone"]):
                            odor_text = cell_text

                    descriptors = [d.strip() for d in re.split(r'[;,]', odor_text) if d.strip()]
                    families = []
                    for desc in descriptors:
                        family = ODOR_TYPE_TO_FAMILY.get(desc, None)
                        if family and family not in families:
                            families.append(family)

                    molecules.append(PherobaseMolecule(
                        name=name,
                        cas_number=cas,
                        odor_descriptors=descriptors,
                        odor_families=families,
                        molecular_formula=formula,
                        source_url=url,
                    ))

        # Try family-specific pages
        compound_families = [
            "alcohol", "aldehyde", "ketone", "ester", "acid",
            "terpene", "lactone", "amine", "sulfur", "phenol",
        ]

        for family in compound_families:
            url = f"{PHEROBASE_BASE}/database/{family}.php"
            soup = self._fetch(url)
            if not soup:
                continue

            for table in soup.find_all("table"):
                for row in table.find_all("tr"):
                    cells = row.find_all("td")
                    text = row.get_text()
                    cas_match = re.search(r'(\d{2,7}-\d{2}-\d)', text)
                    if not cas_match:
                        continue

                    cas = cas_match.group(1)
                    if cas in seen_cas:
                        continue
                    seen_cas.add(cas)

                    name = cells[0].get_text(strip=True) if cells else ""
                    name = re.sub(r'\d{2,7}-\d{2}-\d', '', name).strip()

                    # Extract odor info from remaining cells
                    odor_text = ""
                    for cell in cells:
                        ct = cell.get_text(strip=True).lower()
                        if any(kw in ct for kw in ["odor", "smell", "pheromone", "attractant"]):
                            odor_text += ct + " "

                    descriptors = [d.strip() for d in re.split(r'[;,]', odor_text) if d.strip()]
                    families = [family]
                    for desc in descriptors:
                        f = ODOR_TYPE_TO_FAMILY.get(desc, None)
                        if f and f not in families:
                            families.append(f)

                    molecules.append(PherobaseMolecule(
                        name=name,
                        cas_number=cas,
                        odor_descriptors=descriptors,
                        odor_families=families,
                        biological_activity="semiochemical",
                        source_url=url,
                    ))

            if len(molecules) > 3000:
                logger.info(f"Pherobase: reached 3000 molecules, stopping")
                break

        logger.info(f"Pherobase: found {len(molecules)} molecules")
        return molecules

    def _fallback_cached_data(self) -> List[PherobaseMolecule]:
        """
        Fallback cached data for key semiochemicals that are
        also important fragrance/odor molecules.
        """
        cached = [
            PherobaseMolecule(name="Linalool", cas_number="78-70-6",
                odor_descriptors=["floral", "lavender", "fresh"],
                odor_families=["floral", "citrus"], biological_activity="kairomone",
                organism="Multiple insects"),
            PherobaseMolecule(name="Geraniol", cas_number="106-24-1",
                odor_descriptors=["floral", "rose", "sweet"],
                odor_families=["floral"], biological_activity="kairomone/allomone",
                organism="Bees, moths"),
            PherobaseMolecule(name="Citronellal", cas_number="106-23-0",
                odor_descriptors=["citrus", "lemon", "fresh", "aldehydic"],
                odor_families=["citrus", "aldehydic"], biological_activity="allomone",
                organism="Mosquito repellent"),
            PherobaseMolecule(name="Eugenol", cas_number="97-53-0",
                odor_descriptors=["spicy", "clove", "warm"],
                odor_families=["spicy"], biological_activity="attractant",
                organism="Bees (Euglossini)"),
            PherobaseMolecule(name="Methyl Salicylate", cas_number="119-36-8",
                odor_descriptors=["minty", "wintergreen", "sweet"],
                odor_families=["aromatic_herbal", "green"], biological_activity="kairomone",
                organism="Multiple insects"),
            PherobaseMolecule(name="Methyl Anthranilate", cas_number="134-20-3",
                odor_descriptors=["floral", "orange blossom", "grape"],
                odor_families=["floral", "fruity"], biological_activity="allomone",
                organism="Birds (repellent)"),
            PherobaseMolecule(name="beta-Caryophyllene", cas_number="87-44-5",
                odor_descriptors=["spicy", "woody", "pepper", "clove"],
                odor_families=["spicy", "woody"], biological_activity="kairomone",
                organism="Multiple insects"),
            PherobaseMolecule(name="alpha-Humulene", cas_number="6753-98-6",
                odor_descriptors=["woody", "hoppy", "herbal"],
                odor_families=["woody", "aromatic_herbal"], biological_activity="kairomone",
                organism="Multiple insects"),
            PherobaseMolecule(name="Limonene", cas_number="5989-27-5",
                odor_descriptors=["citrus", "orange", "fresh"],
                odor_families=["citrus"], biological_activity="kairomone",
                organism="Multiple insects"),
            PherobaseMolecule(name="alpha-Pinene", cas_number="80-56-8",
                odor_descriptors=["pine", "fresh", "sharp"],
                odor_families=["citrus", "woody"], biological_activity="kairomone",
                organism="Multiple insects"),
            PherobaseMolecule(name="Delta-3-Carene", cas_number="13466-78-9",
                odor_descriptors=["pine", "fresh", "sweet", "wood"],
                odor_families=["woody", "citrus"], biological_activity="kairomone",
                organism="Beetles"),
            PherobaseMolecule(name="Myrcene", cas_number="123-35-3",
                odor_descriptors=["citrus", "tropical", "balsamic"],
                odor_families=["citrus", "fruity"], biological_activity="kairomone",
                organism="Multiple insects"),
            PherobaseMolecule(name="Terpineol", cas_number="98-55-5",
                odor_descriptors=["pine", "lilac", "floral"],
                odor_families=["floral", "citrus"], biological_activity="kairomone",
                organism="Multiple insects"),
            PherobaseMolecule(name="Benzyl Alcohol", cas_number="100-51-6",
                odor_descriptors=["floral", "jasmine", "sweet"],
                odor_families=["floral"], biological_activity="kairomone",
                organism="Multiple insects"),
            PherobaseMolecule(name="Phenethyl Alcohol", cas_number="60-12-8",
                odor_descriptors=["floral", "rose", "honey"],
                odor_families=["floral"], biological_activity="attractant",
                organism="Bees"),
            PherobaseMolecule(name="Indole", cas_number="120-72-9",
                odor_descriptors=["floral", "jasmine", "animalic", "fecal"],
                odor_families=["floral", "musky"], biological_activity="attractant",
                organism="Moths (floral attractant)"),
            PherobaseMolecule(name="Vanillin", cas_number="121-33-5",
                odor_descriptors=["vanilla", "sweet", "gourmand"],
                odor_families=["gourmand"], biological_activity="attractant",
                organism="Bees (Euglossini)"),
        ]
        logger.info(f"Pherobase fallback: using {len(cached)} cached semiochemical entries")
        return cached


def save_pherobase(molecules: List[PherobaseMolecule], filepath: str):
    """Save Pherobase molecules to JSONL."""
    with open(filepath, "w", encoding="utf-8") as f:
        for mol in molecules:
            f.write(json.dumps(asdict(mol), ensure_ascii=False) + "\n")
    logger.info(f"Saved {len(molecules)} Pherobase molecules to {filepath}")


if __name__ == "__main__":
    scraper = PherobaseScraper()
    molecules = scraper.scrape_database()
    output_file = os.path.join(RAW_DIR, "pherobase_molecules.jsonl")
    save_pherobase(molecules, output_file)

import os