"""
PubChem API Integration
========================
Fetches chemical properties from PubChem's REST API for any CAS number.
Provides: molecular formula, molecular weight, IUPAC name, InChI,
2D/3D structure, and basic physicochemical properties.

Rate limit: 5 requests/second (no API key needed).
"""

import json
import time
import logging
from typing import Dict, Optional
from pathlib import Path

import requests

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

PUBCHEM_BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"


class PubChemClient:
    """Client for PubChem REST API. No API key needed."""

    def __init__(self, rate_limit: float = 0.25):
        self.rate_limit = rate_limit  # 5 req/sec max
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Epicure-Fragrance-Agent/1.0",
        })

    def _get(self, url: str) -> Optional[dict]:
        """GET request with rate limiting and error handling."""
        time.sleep(self.rate_limit)
        try:
            resp = self.session.get(url, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.warning(f"PubChem API error for {url}: {e}")
            return None

    def lookup_by_cas(self, cas: str) -> Optional[Dict]:
        """Look up a compound by CAS number. Returns CID and basic info."""
        url = f"{PUBCHEM_BASE}/compound/name/{cas}/cids/JSON"
        data = self._get(url)
        if not data or "IdentifierList" not in data:
            return None
        cids = data["IdentifierList"].get("CID", [])
        if not cids:
            return None
        return {"cas": cas, "cid": cids[0]}

    def get_properties(self, cid: int) -> Optional[Dict]:
        """Get chemical properties for a PubChem CID."""
        props = "MolecularFormula,MolecularWeight,IUPACName,InChI,InChIKey,CanonicalSMILES,XLogP,ExactMass,TPSA,Complexity,HBondDonorCount,HBondAcceptorCount,RotatableBondCount"
        url = f"{PUBCHEM_BASE}/compound/cid/{cid}/property/{props}/JSON"
        data = self._get(url)
        if not data or "PropertyTable" not in data:
            return None
        props_list = data["PropertyTable"].get("Properties", [])
        if not props_list:
            return None
        return props_list[0]

    def get_synonyms(self, cid: int) -> list:
        """Get synonyms (trade names, systematic names) for a CID."""
        url = f"{PUBCHEM_BASE}/compound/cid/{cid}/synonyms/JSON"
        data = self._get(url)
        if not data or "InformationList" not in data:
            return []
        info = data["InformationList"].get("Information", [])
        if not info:
            return []
        return info[0].get("Synonym", [])[:50]  # Limit to 50

    def enrich_molecule(self, cas: str) -> Optional[Dict]:
        """
        Full enrichment pipeline for a molecule by CAS number.
        Returns combined data: CID, properties, synonyms.
        """
        lookup = self.lookup_by_cas(cas)
        if not lookup:
            return None

        cid = lookup["cid"]
        props = self.get_properties(cid)
        synonyms = self.get_synonyms(cid)

        result = {"cas": cas, "cid": cid}
        if props:
            result.update({
                "molecular_formula": props.get("MolecularFormula"),
                "molecular_weight": props.get("MolecularWeight"),
                "iupac_name": props.get("IUPACName"),
                "inchi": props.get("InChI"),
                "inchikey": props.get("InChIKey"),
                "smiles": props.get("CanonicalSMILES"),
                "log_p": props.get("XLogP"),
                "tpsa": props.get("TPSA"),
                "complexity": props.get("Complexity"),
                "h_bond_donors": props.get("HBondDonorCount"),
                "h_bond_acceptors": props.get("HBondAcceptorCount"),
                "rotatable_bonds": props.get("RotatableBondCount"),
            })
        if synonyms:
            result["synonyms"] = synonyms

        return result

    def batch_enrich(self, cas_list: list, output_file: str = None) -> list:
        """
        Enrich a batch of CAS numbers. Optionally save to JSONL.
        """
        results = []
        for i, cas in enumerate(cas_list):
            logger.info(f"  [{i+1}/{len(cas_list)}] Enriching CAS {cas}...")
            data = self.enrich_molecule(cas)
            if data:
                results.append(data)
                if output_file:
                    with open(output_file, "a", encoding="utf-8") as f:
                        f.write(json.dumps(data, ensure_ascii=False) + "\n")
        return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="PubChem API Client")
    parser.add_argument("--cas", type=str, help="Single CAS number to look up")
    parser.add_argument("--batch", type=str, help="File with CAS numbers (one per line)")
    parser.add_argument("--output", type=str, default=None, help="Output JSONL file")
    args = parser.parse_args()

    client = PubChemClient()
    if args.cas:
        result = client.enrich_molecule(args.cas)
        if result:
            print(json.dumps(result, indent=2))
        else:
            print(f"No data found for CAS {args.cas}")
    elif args.batch:
        with open(args.batch, "r") as f:
            cas_list = [line.strip() for line in f if line.strip()]
        results = client.batch_enrich(cas_list, args.output)
        print(f"Enriched {len(results)}/{len(cas_list)} molecules")
