"""
TGSC (The Good Scents Company) Scraper
========================================
Scrapes aroma molecule data from thegoodscentscompany.com:
- Full odor type taxonomy (~500+ categories)
- Individual molecule pages (CAS, name, odor descriptors, physicochemical properties)
- Molecule-to-odor-type mapping

Usage:
    python -m scrapers.tgsc_scraper [--scrape-odor-list] [--scrape-molecules] [--cas-list FILE]
"""

import re
import json
import time
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict, field

import requests
from bs4 import BeautifulSoup

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import (
    TGSC_BASE_URL, TGSC_ODOR_LIST_URL, TGSC_RATE_LIMIT_SECONDS,
    TGSC_MAX_RETRIES, TGSC_MOLECULES_FILE, TGSC_ODOR_TYPES_FILE,
    RAW_DIR, ODOR_FAMILIES, ODOR_TYPE_TO_FAMILY,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class AromaMolecule:
    """Represents a single aroma molecule from TGSC."""
    cas_number: str
    name: str
    synonyms: List[str] = field(default_factory=list)
    odor_descriptors: List[str] = field(default_factory=list)
    odor_families: List[str] = field(default_factory=list)  # mapped to 15 families
    flavor_descriptors: List[str] = field(default_factory=list)
    molecular_formula: Optional[str] = None
    molecular_weight: Optional[float] = None
    boiling_point: Optional[float] = None
    flash_point: Optional[float] = None
    log_p: Optional[float] = None
    vapor_pressure: Optional[float] = None
    natural_occurrence: List[str] = field(default_factory=list)
    use_categories: List[str] = field(default_factory=list)  # FL, FR, FL/FR
    suppliers: List[str] = field(default_factory=list)
    ifra_restriction: Optional[str] = None
    source_url: str = ""


@dataclass
class OdorType:
    """Represents a single odor type category from TGSC."""
    name: str
    family: str  # mapped to one of 15 primary odor families
    url: str = ""
    molecule_count: int = 0


class TGSCScraper:
    """Scraper for The Good Scents Company aroma chemical database."""

    def __init__(self, rate_limit: float = TGSC_RATE_LIMIT_SECONDS):
        self.rate_limit = rate_limit
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        })

    def _fetch(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch a URL and return parsed BeautifulSoup, with retries and rate limiting."""
        for attempt in range(TGSC_MAX_RETRIES):
            try:
                time.sleep(self.rate_limit)
                resp = self.session.get(url, timeout=30)
                resp.raise_for_status()
                return BeautifulSoup(resp.text, "html.parser")
            except requests.RequestException as e:
                logger.warning(f"Attempt {attempt+1}/{TGSC_MAX_RETRIES} failed for {url}: {e}")
                time.sleep(self.rate_limit * 2)
        logger.error(f"All attempts failed for {url}")
        return None

    def scrape_odor_type_list(self) -> Dict[str, OdorType]:
        """
        Scrape the master odor type listing from TGSC.
        Returns dict mapping odor type name -> OdorType object.
        """
        logger.info("Scraping TGSC odor type list...")
        soup = self._fetch(TGSC_ODOR_LIST_URL)
        if not soup:
            logger.error("Failed to fetch odor type list")
            return {}

        odor_types = {}
        # Parse the table structure - TGSC uses simple text layout
        text = soup.get_text()
        lines = [l.strip() for l in text.split("\n") if l.strip()]

        # Find odor types between header and footer
        in_odor_section = False
        for line in lines:
            # Skip header/footer content
            if "Odor Type Listing" in line:
                in_odor_section = True
                continue
            if "Top of Page" in line or "Copyright" in line:
                break
            if not in_odor_section:
                continue

            # Each line may contain one or more odor types
            # TGSC lists them in table cells
            potential_types = re.split(r'\s{2,}', line)
            for ot in potential_types:
                ot = ot.strip().lower()
                if ot and len(ot) > 1:
                    family = ODOR_TYPE_TO_FAMILY.get(ot, "unclassified")
                    odor_types[ot] = OdorType(
                        name=ot,
                        family=family,
                        url=f"{TGSC_BASE_URL}/odor/{ot.replace(' ', '_')}.html",
                    )

        # Also parse HTML table cells directly
        for td in soup.find_all("td"):
            text = td.get_text(strip=True).lower()
            if text and len(text) > 1 and text not in odor_types:
                family = ODOR_TYPE_TO_FAMILY.get(text, "unclassified")
                odor_types[text] = OdorType(
                    name=text,
                    family=family,
                    url=f"{TGSC_BASE_URL}/odor/{text.replace(' ', '_')}.html",
                )

        logger.info(f"Found {len(odor_types)} odor types across "
                     f"{len(set(ot.family for ot in odor_types.values()))} families")
        return odor_types

    def scrape_molecule_page(self, cas_number: str, rw_id: str = None) -> Optional[AromaMolecule]:
        """
        Scrape an individual molecule page from TGSC.
        TGSC uses internal 'rw' IDs (e.g., rw1008311), NOT CAS numbers directly.
        If rw_id is provided, use it; otherwise attempt CAS-based URL.
        """
        if rw_id:
            url = f"{TGSC_BASE_URL}/data/{rw_id}.html"
        else:
            # TGSC uses an internal 7-digit numeric ID, not CAS.
            # Discovery must happen through odor-type pages or the raw material index.
            cas_stripped = cas_number.replace("-", "")
            url = f"{TGSC_BASE_URL}/data/rw{cas_stripped}.html"

        soup = self._fetch(url)
        if not soup:
            return None

        molecule = AromaMolecule(
            cas_number=cas_number,
            name="",
            source_url=url,
        )

        # Parse molecule name from title or heading
        title = soup.find("title")
        if title:
            name_match = re.search(r"(.+?)\s*[-,]?\s*\d", title.text)
            if name_match:
                molecule.name = name_match.group(1).strip()
            else:
                molecule.name = title.text.split("-")[0].strip()

        # Parse the main content area
        text = soup.get_text()

        # Extract odor descriptors - typically after "odor:" or "Odor Description:"
        odor_match = re.findall(r'odor[:\s]+([^.;\n]+)', text, re.IGNORECASE)
        for match in odor_match:
            descriptors = [d.strip().lower() for d in re.split(r'[,;]', match) if d.strip()]
            molecule.odor_descriptors.extend(descriptors)

        # Extract flavor descriptors
        flavor_match = re.findall(r'flavor[:\s]+([^.;\n]+)', text, re.IGNORECASE)
        for match in flavor_match:
            descriptors = [d.strip().lower() for d in re.split(r'[,;]', match) if d.strip()]
            molecule.flavor_descriptors.extend(descriptors)

        # Map odor descriptors to 15 families
        for desc in molecule.odor_descriptors:
            family = ODOR_TYPE_TO_FAMILY.get(desc, None)
            if family and family not in molecule.odor_families:
                molecule.odor_families.append(family)

        # Extract physicochemical properties
        mw_match = re.search(r'(?:Molecular\s*Weight|MW)[:\s]+(\d+\.?\d*)', text, re.IGNORECASE)
        if mw_match:
            molecule.molecular_weight = float(mw_match.group(1))

        bp_match = re.search(r'(?:Boiling\s*Point|BP)[:\s]+(\d+\.?\d*)', text, re.IGNORECASE)
        if bp_match:
            molecule.boiling_point = float(bp_match.group(1))

        fp_match = re.search(r'(?:Flash\s*Point|FP)[:\s]+(\d+\.?\d*)', text, re.IGNORECASE)
        if fp_match:
            molecule.flash_point = float(fp_match.group(1))

        formula_match = re.search(r'(?:Formula|Molecular\s*Formula)[:\s]+([A-Z0-9]+)', text)
        if formula_match:
            molecule.molecular_formula = formula_match.group(1)

        # Extract use categories (FL = flavor, FR = fragrance)
        if "FL/FR" in text:
            molecule.use_categories.append("FL/FR")
        elif "FL" in text and "FR" in text:
            molecule.use_categories.extend(["FL", "FR"])
        elif "FL" in text:
            molecule.use_categories.append("FL")
        elif "FR" in text:
            molecule.use_categories.append("FR")

        # Extract natural occurrence
        nat_match = re.findall(r'found\s+(?:in|naturally\s+in)\s+([^.;\n]+)', text, re.IGNORECASE)
        molecule.natural_occurrence = [n.strip() for n in nat_match]

        # Extract IFRA restrictions
        ifra_match = re.search(r'IFRA[:\s]+([^.;\n]+)', text, re.IGNORECASE)
        if ifra_match:
            molecule.ifra_restriction = ifra_match.group(1).strip()

        # Deduplicate lists
        molecule.odor_descriptors = list(dict.fromkeys(molecule.odor_descriptors))
        molecule.odor_families = list(dict.fromkeys(molecule.odor_families))
        molecule.flavor_descriptors = list(dict.fromkeys(molecule.flavor_descriptors))

        return molecule

    def scrape_odor_type_page(self, odor_type: str) -> List[Dict]:
        """
        Scrape a specific odor type page to find all molecules with that odor.
        Returns list of dicts with molecule name, CAS, and supplier info.
        """
        url = f"{TGSC_BASE_URL}/odor/{odor_type.replace(' ', '_')}.html"
        soup = self._fetch(url)
        if not soup:
            return []

        molecules = []
        # Parse table rows for molecule entries
        for row in soup.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) >= 2:
                name_text = cells[0].get_text(strip=True)
                cas_match = re.search(r'(\d{2,7}-\d{2}-\d)', name_text)
                if cas_match:
                    molecules.append({
                        "cas_number": cas_match.group(1),
                        "name": name_text.replace(cas_match.group(1), "").strip(),
                        "odor_type": odor_type,
                    })

        return molecules

    def scrape_molecule_index(self) -> List[Dict]:
        """
        Discover molecules through odor-type pages on TGSC.
        Returns list of dicts with cas_number, name, and rw_id (if found).
            
        TGSC uses internal 'rw' IDs for URLs, not CAS numbers directly.
        Discovery must happen through:
        1. Odor-type listing pages (/odor/TYPE.html)
        2. Raw material index pages (/rawmatRWID.html)
        3. Search by chemical name
        """
        molecules = []
        seen_cas = set()
        seen_names = set()
    
        # Strategy 1: Parse odor type pages
        logger.info("Using odor-type-based molecule discovery...")
        odor_types = self.scrape_odor_type_list()
    
        for ot_name, ot in odor_types.items():
            logger.info(f"  Scraping molecules for odor type: {ot_name}")
            ot_molecules = self.scrape_odor_type_page(ot_name)
            for mol in ot_molecules:
                cas = mol.get("cas_number", "")
                name = mol.get("name", "")
                if cas and cas not in seen_cas:
                    seen_cas.add(cas)
                    seen_names.add(name.lower())
                    molecules.append(mol)
    
        # Strategy 2: Scrape the raw material index by first letter
        # TGSC has pages like /rawmatRWID.html with alphabetical listings
        logger.info("Scanning raw material index...")
        for letter_page in range(1, 50):  # Paginated listing
            url = f"{TGSC_BASE_URL}/rawmat{letter_page}.html"
            soup = self._fetch(url)
            if not soup:
                break
            for link in soup.find_all("a", href=True):
                href = link["href"]
                if "/data/rw" in href:
                    # Extract rw ID from URL
                    rw_match = re.search(r'rw(\d+)', href)
                    if rw_match:
                        rw_id = f"rw{rw_match.group(1)}"
                        name = link.get_text(strip=True)
                        cas_match = re.search(r'(\d{2,7}-\d{2}-\d)', name)
                        cas = cas_match.group(1) if cas_match else ""
                        # Accept molecules with CAS OR unique name
                        if cas and cas not in seen_cas:
                            seen_cas.add(cas)
                            seen_names.add(name.lower())
                            molecules.append({
                                "cas_number": cas,
                                "name": name,
                                "rw_id": rw_id,
                            })
                        elif not cas and name.lower() not in seen_names and name:
                            seen_names.add(name.lower())
                            molecules.append({
                                "cas_number": "",
                                "name": name,
                                "rw_id": rw_id,
                            })
    
        # Strategy 3: Browse alphabetically by name
        # TGSC has pages like /rawmatRWID.html organized by letter
        logger.info("Browsing alphabetical listings...")
        for letter in 'abcdefghijklmnopqrstuvwxyz':
            url = f"{TGSC_BASE_URL}/rawmatRWID{letter}.html"
            soup = self._fetch(url)
            if not soup:
                continue
            for link in soup.find_all("a", href=True):
                href = link["href"]
                if "/data/rw" in href:
                    rw_match = re.search(r'rw(\d+)', href)
                    if rw_match:
                        rw_id = f"rw{rw_match.group(1)}"
                        name = link.get_text(strip=True)
                        cas_match = re.search(r'(\d{2,7}-\d{2}-\d)', name)
                        cas = cas_match.group(1) if cas_match else ""
                        if cas and cas not in seen_cas:
                            seen_cas.add(cas)
                            seen_names.add(name.lower())
                            molecules.append({"cas_number": cas, "name": name, "rw_id": rw_id})
                        elif not cas and name.lower() not in seen_names and name:
                            seen_names.add(name.lower())
                            molecules.append({"cas_number": "", "name": name, "rw_id": rw_id})
    
        logger.info(f"Discovered {len(molecules)} unique molecules from index pages")
        return molecules


def save_odor_types(odor_types: Dict[str, OdorType], filepath: str):
    """Save odor types to JSON."""
    data = {name: asdict(ot) for name, ot in odor_types.items()}
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved {len(data)} odor types to {filepath}")


def save_molecule(molecule: AromaMolecule, filepath: str):
    """Append a molecule to the JSONL file."""
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(molecule), ensure_ascii=False) + "\n")


def load_scraped_cas_numbers(filepath: str) -> set:
    """Load already-scraped CAS numbers from the JSONL file."""
    scraped = set()
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    scraped.add(data.get("cas_number", ""))
    except FileNotFoundError:
        pass
    return scraped


def main():
    parser = argparse.ArgumentParser(description="TGSC Aroma Molecule Scraper")
    parser.add_argument("--scrape-odor-list", action="store_true",
                        help="Scrape the full odor type taxonomy")
    parser.add_argument("--scrape-molecules", action="store_true",
                        help="Scrape individual molecule pages")
    parser.add_argument("--cas-list", type=str, default=None,
                        help="File with one CAS number per line (instead of auto-discovery)")
    parser.add_argument("--max-molecules", type=int, default=1000,
                        help="Maximum number of molecules to scrape (default: 1000)")
    parser.add_argument("--output-dir", type=str, default=RAW_DIR,
                        help="Output directory for scraped data")
    args = parser.parse_args()

    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    scraper = TGSCScraper()

    if args.scrape_odor_list:
        odor_types = scraper.scrape_odor_type_list()
        output_file = os.path.join(args.output_dir, "tgsc_odor_types.json")
        save_odor_types(odor_types, output_file)

    if args.scrape_molecules:
        # Get CAS numbers to scrape
        if args.cas_list:
            with open(args.cas_list, "r") as f:
                cas_numbers = [line.strip() for line in f if line.strip()]
        else:
            cas_numbers = scraper.scrape_molecule_index()

        # Filter out already-scraped molecules
        molecules_file = os.path.join(args.output_dir, "tgsc_molecules.jsonl")
        already_scraped = load_scraped_cas_numbers(molecules_file)
        cas_numbers = [c for c in cas_numbers if c not in already_scraped]

        # Limit
        cas_numbers = cas_numbers[:args.max_molecules]
        logger.info(f"Scraping {len(cas_numbers)} molecules...")

        for i, cas in enumerate(cas_numbers):
            logger.info(f"  [{i+1}/{len(cas_numbers)}] Scraping CAS {cas}...")
            molecule = scraper.scrape_molecule_page(cas)
            if molecule and molecule.name:
                save_molecule(molecule, molecules_file)
                logger.info(f"    Saved: {molecule.name}")
            else:
                logger.warning(f"    Skipped CAS {cas}: no data found")

    if not args.scrape_odor_list and not args.scrape_molecules:
        parser.print_help()


import os

if __name__ == "__main__":
    main()
