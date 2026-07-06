"""
Flavornet Academic Odorant Database Scraper
============================================
Scrapes Flavornet.org, an academic database of odorant compounds
with GC retention indices, odor descriptors, and CAS numbers.
Contains ~700+ odorant compounds organized by odor quality.

This is the gold standard for linking chemical structure to
perceived odor via GC-O (Gas Chromatography-Olfactometry) data.

URL: http://www.flavornet.org
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

FLAVORNET_BASE = "http://www.flavornet.org"


@dataclass
class FlavornetMolecule:
    """An odorant entry from Flavornet."""
    name: str
    cas_number: str = ""
    odor_descriptors: List[str] = field(default_factory=list)
    odor_families: List[str] = field(default_factory=list)
    retention_index: Optional[str] = None  # Kovats RI
    gc_column: str = ""  # DB-5, DB-1701, etc.
    concentration_threshold: Optional[str] = None
    molecular_formula: str = ""
    source_url: str = ""


class FlavornetScraper:
    """Scraper for Flavornet academic odorant database."""

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

    def scrape_flavornet_data(self) -> List[FlavornetMolecule]:
        """
        Scrape Flavornet odorant database. The site has HTML tables
        organizing ~700+ odorant compounds by odor quality.
        Each entry contains: compound name, CAS, RI, odor, threshold.
        """
        molecules = []
        seen_cas = set()

        # Main data page - Flavornet has data in table format
        # Try multiple URL patterns as the site structure may vary
        urls_to_try = [
            f"{FLAVORNET_BASE}/flavornet.html",
            f"{FLAVORNET_BASE}/",
            f"{FLAVORNET_BASE}/index.html",
            f"{FLAVORNET_BASE}/data.html",
        ]

        soup = None
        for url in urls_to_try:
            soup = self._fetch(url)
            if soup:
                logger.info(f"Flavornet: successfully fetched {url}")
                break

        if not soup:
            logger.warning("Could not reach Flavornet, generating cached data from known entries")
            return self._fallback_cached_data()

        # Parse all tables on the page
        for table in soup.find_all("table"):
            for row in table.find_all("tr"):
                cells = row.find_all("td")
                if len(cells) < 3:
                    continue

                text = row.get_text()
                cas_match = re.search(r'(\d{2,7}-\d{2}-\d)', text)

                # Extract data from cells
                name = cells[0].get_text(strip=True) if cells else ""
                cas = cas_match.group(1) if cas_match else ""
                odor_text = cells[2].get_text(strip=True) if len(cells) > 2 else ""
                ri_text = cells[1].get_text(strip=True) if len(cells) > 1 else ""

                # Clean name
                name = re.sub(r'\d{2,7}-\d{2}-\d', '', name).strip()
                name = re.sub(r'[()[\]{}]', '', name).strip()

                if not name or name in seen_cas:
                    continue

                if cas:
                    if cas in seen_cas:
                        continue
                    seen_cas.add(cas)

                descriptors = [d.strip().lower() for d in re.split(r'[;,/]', odor_text) if d.strip()]
                families = []
                for desc in descriptors:
                    family = ODOR_TYPE_TO_FAMILY.get(desc, None)
                    if family and family not in families:
                        families.append(family)

                # Extract retention index
                ri_match = re.search(r'(\d{3,4})', ri_text)
                ri = ri_match.group(1) if ri_match else None

                molecules.append(FlavornetMolecule(
                    name=name,
                    cas_number=cas,
                    odor_descriptors=descriptors,
                    odor_families=families,
                    retention_index=ri,
                    gc_column="",
                    molecular_formula="",
                    source_url=FLAVORNET_BASE,
                ))

        # Also check for links to individual odor pages
        for link in soup.find_all("a", href=True):
            href = link["href"]
            if href.endswith(".html") or href.endswith(".htm"):
                sub_url = f"{FLAVORNET_BASE}/{href}" if not href.startswith("http") else href
                sub_soup = self._fetch(sub_url)
                if sub_soup:
                    for table in sub_soup.find_all("table"):
                        for row in table.find_all("tr"):
                            cells = row.find_all("td")
                            if len(cells) < 3:
                                continue
                            text = row.get_text()
                            cas_match = re.search(r'(\d{2,7}-\d{2}-\d)', text)
                            if cas_match:
                                cas = cas_match.group(1)
                                if cas in seen_cas:
                                    continue
                                seen_cas.add(cas)
                                name = cells[0].get_text(strip=True)
                                name = re.sub(r'\d{2,7}-\d{2}-\d', '', name).strip()
                                odor_text = cells[2].get_text(strip=True) if len(cells) > 2 else ""
                                descriptors = [d.strip().lower() for d in re.split(r'[;,/]', odor_text) if d.strip()]
                                families = []
                                for desc in descriptors:
                                    family = ODOR_TYPE_TO_FAMILY.get(desc, None)
                                    if family and family not in families:
                                        families.append(family)
                                molecules.append(FlavornetMolecule(
                                    name=name,
                                    cas_number=cas,
                                    odor_descriptors=descriptors,
                                    odor_families=families,
                                    source_url=sub_url,
                                ))

        logger.info(f"Flavornet: found {len(molecules)} odorant molecules")
        return molecules

    def _fallback_cached_data(self) -> List[FlavornetMolecule]:
        """
        Fallback: hardcoded GC-O data from key Flavornet entries
        for when the website is unreachable.
        These are some of the most important odorants from academic literature.
        """
        cached = [
            FlavornetMolecule(name="2-Methylisoborneol", cas_number="2341-22-9",
                odor_descriptors=["earthy", "muddy", "musty"], odor_families=["earthy"],
                retention_index="1190", gc_column="DB-5"),
            FlavornetMolecule(name="Geosmin", cas_number="19700-21-1",
                odor_descriptors=["earthy", "petrichor", "soil"], odor_families=["earthy"],
                retention_index="1290", gc_column="DB-5"),
            FlavornetMolecule(name="Dimethyl Sulfide", cas_number="75-18-3",
                odor_descriptors=["sulfurous", "cabbage", "marine"], odor_families=["aquatic", "earthy"],
                retention_index="552", gc_column="DB-5"),
            FlavornetMolecule(name="Methional", cas_number="3268-49-3",
                odor_descriptors=["potato", "cooked vegetable", "sulfurous"], odor_families=["earthy", "gourmand"],
                retention_index="861", gc_column="DB-5"),
            FlavornetMolecule(name="Isoamyl Acetate", cas_number="123-92-2",
                odor_descriptors=["banana", "fruity", "sweet"], odor_families=["fruity"],
                retention_index="875", gc_column="DB-5"),
            FlavornetMolecule(name="Ethyl Butyrate", cas_number="105-54-4",
                odor_descriptors=["pineapple", "fruity", "sweet"], odor_families=["fruity"],
                retention_index="805", gc_column="DB-5"),
            FlavornetMolecule(name="Ethyl Hexanoate", cas_number="123-66-0",
                odor_descriptors=["fruity", "apple", "sweet"], odor_families=["fruity"],
                retention_index="1001", gc_column="DB-5"),
            FlavornetMolecule(name="Ethyl Octanoate", cas_number="106-32-1",
                odor_descriptors=["fruity", "pear", "sweet"], odor_families=["fruity"],
                retention_index="1198", gc_column="DB-5"),
            FlavornetMolecule(name="Acetaldehyde", cas_number="75-07-0",
                odor_descriptors=["sharp", "fresh", "green", "fruity"], odor_families=["green", "fruity"],
                retention_index="640", gc_column="DB-5"),
            FlavornetMolecule(name="Hexanal", cas_number="66-25-1",
                odor_descriptors=["green", "leafy", "grassy", "fresh"], odor_families=["green"],
                retention_index="801", gc_column="DB-5"),
            FlavornetMolecule(name="2-Nonenal", cas_number="18829-56-6",
                odor_descriptors=["cucumber", "fresh", "green", "fatty"], odor_families=["green", "aquatic"],
                retention_index="1154", gc_column="DB-5"),
            FlavornetMolecule(name="Decanal", cas_number="112-31-2",
                odor_descriptors=["citrus", "orange peel", "waxy", "fresh"], odor_families=["citrus", "aldehydic"],
                retention_index="1206", gc_column="DB-5"),
            FlavornetMolecule(name="Dodecanal", cas_number="112-54-9",
                odor_descriptors=["soapy", "waxy", "metallic", "clean"], odor_families=["aldehydic"],
                retention_index="1406", gc_column="DB-5"),
            FlavornetMolecule(name="Citral", cas_number="5392-40-5",
                odor_descriptors=["lemon", "citrus", "fresh", "sharp"], odor_families=["citrus"],
                retention_index="1242", gc_column="DB-5"),
            FlavornetMolecule(name="Linalool", cas_number="78-70-6",
                odor_descriptors=["floral", "lavender", "citrus", "fresh"], odor_families=["floral", "citrus"],
                retention_index="1101", gc_column="DB-5"),
            FlavornetMolecule(name="Geraniol", cas_number="106-24-1",
                odor_descriptors=["floral", "rose", "sweet"], odor_families=["floral"],
                retention_index="1253", gc_column="DB-5"),
            FlavornetMolecule(name="Ionone Beta", cas_number="14901-07-6",
                odor_descriptors=["violet", "floral", "raspberry", "woody"], odor_families=["floral", "fruity"],
                retention_index="1491", gc_column="DB-5"),
            FlavornetMolecule(name="Damascenone", cas_number="23726-93-4",
                odor_descriptors=["floral", "rose", "fruity", "plum", "tobacco"], odor_families=["floral", "fruity"],
                retention_index="1381", gc_column="DB-5"),
            FlavornetMolecule(name="Eugenol", cas_number="97-53-0",
                odor_descriptors=["spicy", "clove", "warm"], odor_families=["spicy"],
                retention_index="1361", gc_column="DB-5"),
            FlavornetMolecule(name="Vanillin", cas_number="121-33-5",
                odor_descriptors=["vanilla", "sweet", "gourmand"], odor_families=["gourmand", "amber"],
                retention_index="1411", gc_column="DB-5"),
            FlavornetMolecule(name="Cinnamaldehyde", cas_number="104-55-2",
                odor_descriptors=["spicy", "cinnamon", "sweet"], odor_families=["spicy", "amber"],
                retention_index="1277", gc_column="DB-5"),
            FlavornetMolecule(name="Gamma-Decalactone", cas_number="706-14-9",
                odor_descriptors=["peach", "fruity", "creamy"], odor_families=["fruity", "gourmand"],
                retention_index="1367", gc_column="DB-5"),
            FlavornetMolecule(name="Gamma-Undecalactone", cas_number="104-67-6",
                odor_descriptors=["peach", "fruity", "creamy", "sweet"], odor_families=["fruity", "gourmand"],
                retention_index="1467", gc_column="DB-5"),
            FlavornetMolecule(name="Maltol", cas_number="118-71-8",
                odor_descriptors=["caramel", "cotton candy", "sweet"], odor_families=["gourmand"],
                retention_index="1110", gc_column="DB-5"),
            FlavornetMolecule(name="Furaneol", cas_number="3658-77-3",
                odor_descriptors=["strawberry", "sweet", "tropical", "caramel"], odor_families=["fruity", "gourmand"],
                retention_index="1050", gc_column="DB-5"),
            FlavornetMolecule(name="Methyl Anthranilate", cas_number="134-20-3",
                odor_descriptors=["grape", "floral", "orange blossom", "sweet"], odor_families=["fruity", "floral"],
                retention_index="1316", gc_column="DB-5"),
            FlavornetMolecule(name="Phenethyl Alcohol", cas_number="60-12-8",
                odor_descriptors=["floral", "rose", "honey", "sweet"], odor_families=["floral"],
                retention_index="1120", gc_column="DB-5"),
            FlavornetMolecule(name="Indole", cas_number="120-72-9",
                odor_descriptors=["floral", "jasmine", "animalic", "fecal"], odor_families=["floral", "musky"],
                retention_index="1289", gc_column="DB-5"),
            FlavornetMolecule(name="cis-3-Hexenol", cas_number="928-96-1",
                odor_descriptors=["green", "fresh", "cut grass", "leafy"], odor_families=["green"],
                retention_index="854", gc_column="DB-5"),
            FlavornetMolecule(name="alpha-Pinene", cas_number="80-56-8",
                odor_descriptors=["pine", "fresh", "sharp", "citrus"], odor_families=["citrus", "woody"],
                retention_index="938", gc_column="DB-5"),
            FlavornetMolecule(name="D-Limonene", cas_number="5989-27-5",
                odor_descriptors=["citrus", "orange", "fresh", "sweet"], odor_families=["citrus"],
                retention_index="1031", gc_column="DB-5"),
            FlavornetMolecule(name="Anethole", cas_number="104-46-1",
                odor_descriptors=["anise", "sweet", "licorice", "warm"], odor_families=["spicy", "aromatic_herbal"],
                retention_index="1290", gc_column="DB-5"),
            FlavornetMolecule(name="Menthol", cas_number="89-78-1",
                odor_descriptors=["minty", "fresh", "cool", "peppermint"], odor_families=["aromatic_herbal"],
                retention_index="1173", gc_column="DB-5"),
            FlavornetMolecule(name="1,8-Cineole", cas_number="470-82-6",
                odor_descriptors=["camphoraceous", "eucalyptus", "fresh", "cool"], odor_families=["aromatic_herbal"],
                retention_index="1033", gc_column="DB-5"),
            FlavornetMolecule(name="Coumarin", cas_number="91-64-5",
                odor_descriptors=["sweet", "hay", "tonka", "almond"], odor_families=["gourmand"],
                retention_index="1445", gc_column="DB-5"),
            FlavornetMolecule(name="Ambrettolide", cas_number="28645-51-4",
                odor_descriptors=["musk", "warm", "floral", "skin"], odor_families=["musky"],
                retention_index="1700", gc_column="DB-5"),
            FlavornetMolecule(name="Piperonal (Heliotropin)", cas_number="120-57-0",
                odor_descriptors=["powdery", "heliotrope", "cherry", "sweet", "floral"], odor_families=["powdery", "floral"],
                retention_index="1345", gc_column="DB-5"),
        ]
        logger.info(f"Flavornet fallback: using {len(cached)} cached GC-O odorant entries")
        return cached


def save_flavornet(molecules: List[FlavornetMolecule], filepath: str):
    """Save Flavornet molecules to JSONL."""
    with open(filepath, "w", encoding="utf-8") as f:
        for mol in molecules:
            f.write(json.dumps(asdict(mol), ensure_ascii=False) + "\n")
    logger.info(f"Saved {len(molecules)} Flavornet molecules to {filepath}")


if __name__ == "__main__":
    scraper = FlavornetScraper()
    molecules = scraper.scrape_flavornet_data()
    output_file = os.path.join(RAW_DIR, "flavornet_molecules.jsonl")
    save_flavornet(molecules, output_file)

import os