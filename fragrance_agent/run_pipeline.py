"""
Master Pipeline Runner
======================
Orchestrates the complete fragrance knowledge base build:
1. Load seed molecules (curated 500+ molecules, always available)
2. Scrape TGSC odor types / molecule discovery
3. Scrape TGSC molecules (up to 3000+)
4. Enrich molecules with PubChem properties
5. Scrape Leffingwell odor reference database
6. Scrape Flavornet academic odorant database (GC-O data)
7. Scrape Pherobase semiochemical database
8. Scrape Fragrantica notes directory
9. Enrich with ChEBI chemical ontology
10. Process, canonicalize, build graphs
11. Assemble final knowledge base
12. Test agent

Usage:
    python run_pipeline.py [--skip-scrape] [--skip-pubchem] [--seed-only]
"""

import json
import sys
import os
import logging
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import (
    RAW_DIR, PROCESSED_DIR, KNOWLEDGE_DIR,
    TGSC_MOLECULES_FILE, TGSC_ODOR_TYPES_FILE,
    FRAGNANTICA_NOTES_FILE, FRAGNANTICA_PERFUMES_FILE,
    BASENOTES_PERFUMES_FILE,
    CANONICAL_MOLECULES_FILE, CANONICAL_NOTES_FILE,
    CANONICAL_PERFUMES_FILE, COOCCURRENCE_GRAPH_FILE,
    MOLECULE_ODOR_GRAPH_FILE, KNOWLEDGE_BASE_FILE,
)
from knowledge.seed_molecules import get_seed_molecules

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def step_1_seed_molecules():
    """Step 1: Write seed molecules to the raw data directory."""
    logger.info("=== Step 1: Loading seed molecule database ===")
    seeds = get_seed_molecules()
    
    # Write to raw directory as JSONL (same format as scraped data)
    output_file = os.path.join(RAW_DIR, "seed_molecules.jsonl")
    with open(output_file, "w", encoding="utf-8") as f:
        for mol in seeds:
            # Convert to the same format as TGSC scraper output
            record = {
                "cas_number": mol.get("cas", ""),
                "name": mol.get("name", ""),
                "synonyms": [],
                "odor_descriptors": mol.get("odor_descriptors", []),
                "odor_families": mol.get("odor_families", []),
                "flavor_descriptors": [],
                "molecular_formula": mol.get("formula", ""),
                "molecular_weight": mol.get("mw"),
                "boiling_point": None,
                "flash_point": None,
                "log_p": None,
                "vapor_pressure": None,
                "natural_occurrence": [],
                "use_categories": [mol.get("use", "FR")],
                "suppliers": [],
                "ifra_restriction": None,
                "volatility": mol.get("volatility", "heart"),
                "notes": mol.get("notes", ""),
                "source": "seed_database",
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    
    logger.info(f"  Written {len(seeds)} seed molecules to {output_file}")
    return len(seeds)


def step_2_scrape_tgsc_odor_types():
    """Step 2: Scrape TGSC odor type taxonomy."""
    logger.info("=== Step 2: Scraping TGSC odor type list ===")
    try:
        from scrapers.tgsc_scraper import TGSCScraper, save_odor_types
        scraper = TGSCScraper(rate_limit=0.5)
        odor_types = scraper.scrape_odor_type_list()
        save_odor_types(odor_types, TGSC_ODOR_TYPES_FILE)
        logger.info(f"  Scraped {len(odor_types)} odor types")
        return len(odor_types)
    except Exception as e:
        logger.error(f"  TGSC odor type scrape failed: {e}")
        return 0


def step_3_scrape_tgsc_molecules(max_molecules: int = 500):
    """Step 3: Scrape TGSC molecules via odor-type discovery pages."""
    logger.info("=== Step 3: Scraping TGSC molecules ===")
    try:
        from scrapers.tgsc_scraper import TGSCScraper, save_molecule
        scraper = TGSCScraper(rate_limit=0.5)
        
        # Discover molecules through odor-type pages
        discovered = scraper.scrape_molecule_index()
        logger.info(f"  Discovered {len(discovered)} molecules through odor-type pages")
        
        scraped = 0
        for i, mol_info in enumerate(discovered[:max_molecules]):
            cas = mol_info.get("cas_number", "")
            rw_id = mol_info.get("rw_id", None)
            if not cas:
                continue
            
            logger.info(f"  [{i+1}/{min(len(discovered), max_molecules)}] Scraping {mol_info.get('name', cas)}...")
            molecule = scraper.scrape_molecule_page(cas, rw_id=rw_id)
            if molecule and molecule.name:
                save_molecule(molecule, TGSC_MOLECULES_FILE)
                scraped += 1
        
        logger.info(f"  Scraped {scraped}/{len(discovered)} molecules from TGSC")
        return scraped
    except Exception as e:
        logger.error(f"  TGSC molecule scrape failed: {e}")
        return 0


def step_4_enrich_pubchem():
    """Step 4: Enrich molecules with PubChem chemical properties."""
    logger.info("=== Step 4: Enriching molecules via PubChem ===")
    try:
        from scrapers.pubchem_client import PubChemClient
        
        # Collect all CAS numbers from seed + scraped data
        cas_numbers = set()
        
        # From seed data
        for mol in get_seed_molecules():
            cas = mol.get("cas", "")
            if cas and cas != "N/A":
                cas_numbers.add(cas)
        
        # From scraped data
        for data_file in [TGSC_MOLECULES_FILE, os.path.join(RAW_DIR, "seed_molecules.jsonl")]:
            try:
                with open(data_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            record = json.loads(line)
                            cas = record.get("cas_number", "")
                            if cas and cas != "N/A":
                                cas_numbers.add(cas)
            except FileNotFoundError:
                pass
        
        logger.info(f"  Found {len(cas_numbers)} unique CAS numbers to enrich")
        
        output_file = os.path.join(RAW_DIR, "pubchem_enrichment.jsonl")
        client = PubChemClient(rate_limit=0.25)
        results = client.batch_enrich(list(cas_numbers)[:200], output_file)
        logger.info(f"  Enriched {len(results)}/{len(cas_numbers)} molecules via PubChem")
        return len(results)
    except Exception as e:
        logger.error(f"  PubChem enrichment failed: {e}")
        return 0


def step_5_scrape_leffingwell():
    """Step 5: Scrape Leffingwell odor reference database."""
    logger.info("=== Step 5: Scraping Leffingwell ===")
    try:
        from scrapers.leffingwell_scraper import LeffingwellScraper, save_leffingwell
        scraper = LeffingwellScraper(rate_limit=1.0)
        molecules = scraper.scrape_odor_directory()
        olfaction = scraper.scrape_olfaction_charts()
        all_mols = molecules + olfaction
        output_file = os.path.join(RAW_DIR, "leffingwell_molecules.jsonl")
        save_leffingwell(all_mols, output_file)
        logger.info(f"  Scraped {len(all_mols)} Leffingwell molecules")
        return len(all_mols)
    except Exception as e:
        logger.error(f"  Leffingwell scrape failed: {e}")
        return 0


def step_6_scrape_flavornet():
    """Step 6: Scrape Flavornet academic odorant database."""
    logger.info("=== Step 6: Scraping Flavornet ===")
    try:
        from scrapers.flavornet_scraper import FlavornetScraper, save_flavornet
        scraper = FlavornetScraper(rate_limit=1.0)
        molecules = scraper.scrape_flavornet_data()
        output_file = os.path.join(RAW_DIR, "flavornet_molecules.jsonl")
        save_flavornet(molecules, output_file)
        logger.info(f"  Scraped {len(molecules)} Flavornet molecules")
        return len(molecules)
    except Exception as e:
        logger.error(f"  Flavornet scrape failed: {e}")
        return 0


def step_7_scrape_pherobase():
    """Step 7: Scrape Pherobase semiochemical database."""
    logger.info("=== Step 7: Scraping Pherobase ===")
    try:
        from scrapers.pherobase_scraper import PherobaseScraper, save_pherobase
        scraper = PherobaseScraper(rate_limit=1.0)
        molecules = scraper.scrape_database(max_pages=30)
        output_file = os.path.join(RAW_DIR, "pherobase_molecules.jsonl")
        save_pherobase(molecules, output_file)
        logger.info(f"  Scraped {len(molecules)} Pherobase molecules")
        return len(molecules)
    except Exception as e:
        logger.error(f"  Pherobase scrape failed: {e}")
        return 0


def step_8_scrape_fragrantica():
    """Step 8: Scrape Fragrantica notes directory."""
    logger.info("=== Step 8: Scraping Fragrantica ===")
    try:
        from scrapers.fragrantica_scraper import FragranticaScraper, save_notes
        scraper = FragranticaScraper(rate_limit=2.0)
        notes = scraper.scrape_notes_directory()
        save_notes(notes, FRAGNANTICA_NOTES_FILE)
        logger.info(f"  Scraped {len(notes)} Fragrantica notes")
        return len(notes)
    except Exception as e:
        logger.error(f"  Fragrantica scrape failed: {e}")
        return 0


def step_9_enrich_chebi():
    """Step 9: Enrich molecules with ChEBI chemical ontology."""
    logger.info("=== Step 9: ChEBI chemical ontology enrichment ===")
    try:
        from scrapers.chebi_client import ChEBIClient
        client = ChEBIClient(rate_limit=0.25)
        seeds = get_seed_molecules()
        output_file = os.path.join(RAW_DIR, "chebi_enrichment.jsonl")
        results = client.batch_enrich(seeds[:100], output_file)
        logger.info(f"  ChEBI enriched {len(results)} molecules")
        return len(results)
    except Exception as e:
        logger.error(f"  ChEBI enrichment failed: {e}")
        return 0


def step_10_process_data():
    """Step 6: Run the data processing and canonicalization pipeline."""
    logger.info("=== Step 6: Processing and canonicalizing data ===")
    try:
        from data_processor.processor import run_pipeline
        run_pipeline()
        return True
    except Exception as e:
        logger.error(f"  Processing pipeline failed: {e}")
        return False


def step_11_build_knowledge_base():
    """Step 11: Build the final knowledge base."""
    logger.info("=== Step 11: Building final knowledge base ===")
    try:
        from knowledge.knowledge_base import FragranceKnowledgeBase
        from knowledge.seed_molecules import get_seed_molecules
        
        kb = FragranceKnowledgeBase()
        kb.load()
        
        # Merge seed molecules into the knowledge base
        seeds = get_seed_molecules()
        for mol in seeds:
            cas = mol.get("cas", "")
            if cas and cas != "N/A" and cas not in kb.molecules:
                kb.molecules[cas] = {
                    "cas_number": cas,
                    "name": mol.get("name", ""),
                    "odor_descriptors": mol.get("odor_descriptors", []),
                    "odor_families": mol.get("odor_families", []),
                    "molecular_formula": mol.get("formula", ""),
                    "molecular_weight": mol.get("mw"),
                    "use_categories": [mol.get("use", "FR")],
                    "volatility": mol.get("volatility", "heart"),
                    "notes": mol.get("notes", ""),
                    "source": "seed_database",
                }
        
        # Save enriched knowledge base
        Path(KNOWLEDGE_DIR).mkdir(parents=True, exist_ok=True)
        kb_data = {
            "molecules": kb.molecules,
            "notes": kb.notes,
            "perfumes": kb.perfumes,
            "cooccurrence_graph": kb.cooccurrence_graph,
            "molecule_odor_graph": kb.molecule_odor_graph,
            "seed_molecule_count": len(seeds),
        }
        with open(KNOWLEDGE_BASE_FILE, "w", encoding="utf-8") as f:
            json.dump(kb_data, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"  Knowledge base saved: {len(kb.molecules)} molecules, "
                     f"{len(kb.notes)} notes, {len(kb.perfumes)} perfumes")
        return True
    except Exception as e:
        logger.error(f"  Knowledge base build failed: {e}")
        return False


def step_12_test_agent():
    """Step 12: Test the expert agent."""
    logger.info("=== Step 12: Testing expert agent ===")
    try:
        from agent.expert_agent import FragranceExpertAgent
        agent = FragranceExpertAgent()
        
        # Test queries
        test_queries = [
            "What molecules give a floral rose odor?",
            "Tell me about the chypre accord",
            "What are the IFRA restrictions on oakmoss?",
            "Who created Cool Water?",
            "What is the Middle Eastern attar tradition?",
        ]
        
        for query in test_queries:
            result = agent.query(query)
            logger.info(f"  Query: '{query}' → {len(result['context'])} chars context")
        
        print("\n" + agent.get_capabilities_summary())
        return True
    except Exception as e:
        logger.error(f"  Agent test failed: {e}")
        return False


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Fragrance Agent Master Pipeline")
    parser.add_argument("--skip-scrape", action="store_true", help="Skip all web scraping")
    parser.add_argument("--skip-pubchem", action="store_true", help="Skip PubChem enrichment")
    parser.add_argument("--seed-only", action="store_true", help="Only use seed data (no scraping)")
    parser.add_argument("--max-tgsc-molecules", type=int, default=500, help="Max TGSC molecules to scrape")
    args = parser.parse_args()

    start_time = time.time()
    
    # Ensure directories exist
    for d in [RAW_DIR, PROCESSED_DIR, KNOWLEDGE_DIR]:
        os.makedirs(d, exist_ok=True)

    # Step 1: Always load seed molecules
    seed_count = step_1_seed_molecules()

    if not args.seed_only and not args.skip_scrape:
        # Step 2: TGSC odor types
        step_2_scrape_tgsc_odor_types()
        
        # Step 3: TGSC molecules
        step_3_scrape_tgsc_molecules(args.max_tgsc_molecules)
        
        # Step 5: Leffingwell
        step_5_scrape_leffingwell()
        
        # Step 6: Flavornet
        step_6_scrape_flavornet()
        
        # Step 7: Pherobase
        step_7_scrape_pherobase()
        
        # Step 8: Fragrantica
        step_8_scrape_fragrantica()

    if not args.skip_pubchem and not args.seed_only:
        # Step 4: PubChem enrichment
        step_4_enrich_pubchem()
        
        # Step 9: ChEBI enrichment
        step_9_enrich_chebi()

    # Step 10: Process data
    step_10_process_data()

    # Step 11: Build knowledge base
    step_11_build_knowledge_base()

    # Step 12: Test
    step_12_test_agent()

    elapsed = time.time() - start_time
    logger.info(f"\n=== Pipeline complete in {elapsed:.1f}s ===")
    logger.info(f"Seed molecules: {seed_count}")
    logger.info(f"Knowledge base: {KNOWLEDGE_BASE_FILE}")


if __name__ == "__main__":
    main()
