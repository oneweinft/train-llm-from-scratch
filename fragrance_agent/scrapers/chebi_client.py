"""
ChEBI Chemical Ontology Enrichment Client
==========================================
Uses the ChEBI (Chemicals of Biological Interest) REST API
to enrich molecule data with:
- Ontological classification (what type of chemical)
- Synonyms (trade names, IUPAC, systematic names)
- Cross-references to other databases (PubChem, KEGG, etc.)
- Chemical structure relationships (parents, children)

URL: https://www.ebi.ac.uk/chebi/
API: https://www.ebi.ac.uk/chebi/api/
Rate limit: No API key needed, ~5 requests/second
"""

import json
import time
import logging
from typing import Dict, List, Optional
from pathlib import Path

import requests

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

CHEBI_API_BASE = "https://www.ebi.ac.uk/chebi/api/data"


class ChEBIClient:
    """Client for ChEBI chemical ontology API."""

    def __init__(self, rate_limit: float = 0.25):
        self.rate_limit = rate_limit
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Epicure-Fragrance-Agent/1.0",
            "Accept": "application/json",
        })

    def _get(self, url: str) -> Optional[dict]:
        """GET request with rate limiting."""
        time.sleep(self.rate_limit)
        try:
            resp = self.session.get(url, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.warning(f"ChEBI API error for {url}: {e}")
            return None

    def search_by_name(self, name: str) -> Optional[Dict]:
        """Search ChEBI by compound name. Returns matching ChEBI IDs."""
        url = f"{CHEBI_API_BASE}/search?searchString={name}&maximumResults=5"
        data = self._get(url)
        if not data:
            return None
        results = data.get("searchResults", data) if isinstance(data, dict) else data
        if isinstance(results, list) and results:
            return results[0]
        return None

    def get_chebi_entity(self, chebi_id: str) -> Optional[Dict]:
        """Get full entity data for a ChEBI ID."""
        # ChEBI IDs like "CHEBI:15377" -> strip "CHEBI:" for API
        clean_id = chebi_id.replace("CHEBI:", "")
        url = f"{CHEBI_API_BASE}/chebiId/{clean_id}"
        data = self._get(url)
        if not data:
            return None
        return data

    def get_chebi_complete(self, chebi_id: str) -> Optional[Dict]:
        """Get complete entity data including ontology and references."""
        clean_id = chebi_id.replace("CHEBI:", "")
        url = f"{CHEBI_API_BASE}/completeEntity/{clean_id}"
        data = self._get(url)
        if not data:
            return None
        return data

    def enrich_molecule(self, name: str, cas: str = "") -> Optional[Dict]:
        """
        Enrich a molecule using ChEBI data.
        Returns combined data: ChEBI ID, ontology, synonyms, cross-references.
        """
        # Try name search first
        search_result = self.search_by_name(name)
        if not search_result:
            return None

        chebi_id = search_result.get("chebiId", "")
        if not chebi_id:
            return None

        # Get complete entity data
        entity = self.get_chebi_complete(chebi_id)
        if not entity:
            # Try basic entity
            entity = self.get_chebi_entity(chebi_id)

        result = {
            "name": name,
            "cas": cas,
            "chebi_id": chebi_id,
            "chebi_name": entity.get("chebiAsciiName", "") if entity else "",
            "definition": entity.get("definition", "") if entity else "",
        }

        if entity:
            # Extract ontology classification
            ontology = []
            for parent in entity.get("CompoundOntologyParents", []):
                ont_name = parent.get("chebiAsciiName", "")
                if ont_name:
                    ontology.append(ont_name)
            result["ontology_parents"] = ontology

            # Extract synonyms
            synonyms = []
            for syn in entity.get("Synonyms", []):
                syn_data = syn.get("data", "")
                if syn_data:
                    synonyms.append(syn_data)
            result["synonyms"] = synonyms[:30]  # Limit

            # Extract cross-references
            xrefs = {}
            for ref in entity.get("DatabaseLinks", []):
                ref_type = ref.get("type", "")
                ref_data = ref.get("data", "")
                if ref_type and ref_data:
                    xrefs[ref_type] = ref_data
            result["cross_references"] = xrefs

            # Extract formula and mass
            result["formula"] = entity.get("Formula", "")
            result["mass"] = entity.get("Mass", "")

            # Extract InChI and InChIKey
            result["inchi"] = entity.get("inChI", "")
            result["inchikey"] = entity.get("inChIKey", "")

            # Extract SMILES
            for struct in entity.get("Structure", []):
                if struct.get("type") == "SMILES":
                    result["smiles"] = struct.get("data", "")
                    break

        return result

    def batch_enrich(self, molecules: list, output_file: str = None) -> list:
        """
        Enrich a batch of molecules by name or CAS.
        molecules: list of dicts with 'name' and optionally 'cas'.
        """
        results = []
        for i, mol in enumerate(molecules):
            name = mol.get("name", "")
            cas = mol.get("cas", mol.get("cas_number", ""))
            if not name:
                continue

            logger.info(f"  [{i+1}/{len(molecules)}] ChEBI enrichment for {name}...")
            data = self.enrich_molecule(name, cas)
            if data:
                results.append(data)
                if output_file:
                    with open(output_file, "a", encoding="utf-8") as f:
                        f.write(json.dumps(data, ensure_ascii=False) + "\n")

        logger.info(f"ChEBI: enriched {len(results)}/{len(molecules)} molecules")
        return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="ChEBI Chemical Ontology Client")
    parser.add_argument("--name", type=str, help="Single compound name to look up")
    parser.add_argument("--batch", type=str, help="JSONL file with molecule data")
    parser.add_argument("--output", type=str, default=None, help="Output JSONL file")
    args = parser.parse_args()

    client = ChEBIClient()
    if args.name:
        result = client.enrich_molecule(args.name)
        if result:
            print(json.dumps(result, indent=2))
    elif args.batch:
        molecules = []
        with open(args.batch, "r") as f:
            for line in f:
                if line.strip():
                    molecules.append(json.loads(line))
        results = client.batch_enrich(molecules, args.output)