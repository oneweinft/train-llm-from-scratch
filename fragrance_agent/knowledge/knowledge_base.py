"""
Fragrance Knowledge Base & Retrieval Interface
================================================
Combines scraped data, processed graphs, and curated reference knowledge
into a unified retrieval system for the expert agent.

Supports:
- Note similarity queries (co-occurrence graph)
- Molecule-odor queries (typed compound graph)
- Perfume lookups (note pyramids, accords, families)
- Reference knowledge retrieval (history, perfumers, accords, regulations)
- Formulation suggestions (based on accord templates)
"""

import json
import math
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import (
    PROCESSED_DIR, KNOWLEDGE_DIR,
    CANONICAL_MOLECULES_FILE, CANONICAL_NOTES_FILE, CANONICAL_PERFUMES_FILE,
    COOCCURRENCE_GRAPH_FILE, MOLECULE_ODOR_GRAPH_FILE,
    KNOWLEDGE_BASE_FILE, ODOR_FAMILIES,
)
from knowledge.reference_data import get_all_reference_data, search_reference

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


class FragranceKnowledgeBase:
    """
    Unified fragrance knowledge base with retrieval interface.
    Combines graph-based note/molecule data with curated reference knowledge.
    """

    def __init__(self, data_dir: str = PROCESSED_DIR):
        self.data_dir = data_dir
        self.molecules = {}
        self.notes = {}
        self.perfumes = []
        self.cooccurrence_graph = {}
        self.molecule_odor_graph = {}
        self.reference_data = {}

        self._note_neighbors = defaultdict(list)  # note -> [(neighbor, npmi)]
        self._molecule_by_odor = defaultdict(list)  # odor_family -> [molecule_cas]
        self._perfume_by_note = defaultdict(list)    # note -> [perfume_index]

    def load(self):
        """Load all data sources into memory."""
        # Load canonical molecules
        self._load_json(CANONICAL_MOLECULES_FILE, "molecules")

        # Load canonical notes
        try:
            with open(CANONICAL_NOTES_FILE, "r", encoding="utf-8") as f:
                self.notes = json.load(f)
        except FileNotFoundError:
            logger.warning("Canonical notes file not found; using empty vocab")

        # Load canonical perfumes
        try:
            with open(CANONICAL_PERFUMES_FILE, "r", encoding="utf-8") as f:
                self.perfumes = json.load(f)
        except FileNotFoundError:
            logger.warning("Canonical perfumes file not found")

        # Load co-occurrence graph
        self._load_json(COOCCURRENCE_GRAPH_FILE, "cooccurrence_graph")

        # Load molecule-odor graph
        self._load_json(MOLECULE_ODOR_GRAPH_FILE, "molecule_odor_graph")

        # Load reference data
        self.reference_data = get_all_reference_data()
        
        # Always load seed molecules as backbone (these are always available)
        self._load_seed_molecules()

        # Build indexes
        self._build_indexes()

        logger.info(f"Knowledge base loaded: {len(self.molecules)} molecules, "
                     f"{len(self.notes)} notes, {len(self.perfumes)} perfumes")

    def _load_json(self, filepath: str, attr: str):
        """Load a JSON file into an attribute."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                setattr(self, attr, json.load(f))
        except FileNotFoundError:
            logger.warning(f"File not found: {filepath}")

    def _load_seed_molecules(self):
        """Load seed molecules into the knowledge base as backbone data."""
        from knowledge.seed_molecules import get_seed_molecules
        seeds = get_seed_molecules()
        added = 0
        for mol in seeds:
            cas = mol.get("cas", "")
            key = cas if cas and cas != "N/A" else mol.get("name", "")
            if key and key not in self.molecules:
                self.molecules[key] = {
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
                added += 1
        
        # Also extract notes from seed molecules
        for mol in seeds:
            for desc in mol.get("odor_descriptors", []):
                if desc and desc not in self.notes:
                    self.notes[desc] = {"name": desc, "source": "seed_molecules"}
            for family in mol.get("odor_families", []):
                if family and family not in self.notes:
                    self.notes[family] = {"name": family, "source": "seed_molecules", "type": "odor_family"}
        
        logger.info(f"Loaded {added} seed molecules + {len(seeds)} note entries into KB")

    def _build_indexes(self):
        """Build lookup indexes for fast retrieval."""
        # Co-occurrence neighbors index
        for edge in self.cooccurrence_graph.get("edges", []):
            self._note_neighbors[edge["source"]].append(
                (edge["target"], edge["npmi"])
            )
            self._note_neighbors[edge["target"]].append(
                (edge["source"], edge["npmi"])
            )
        # Sort each note's neighbors by NPMI descending
        for note in self._note_neighbors:
            self._note_neighbors[note].sort(key=lambda x: x[1], reverse=True)
    
        # Molecule -> odor family index (from graph file)
        for edge in self.molecule_odor_graph.get("molecule_family_edges", []):
            self._molecule_by_odor[edge["odor_family"]].append(edge["molecule_cas"])
            
        # Also build molecule-odor index from seed molecules directly
        for cas, mol in self.molecules.items():
            for family in mol.get("odor_families", []):
                key = cas if cas else mol.get("name", "")
                if key not in self._molecule_by_odor.get(family, []):
                    self._molecule_by_odor[family].append(key)
    
        # Perfume -> note reverse index
        for i, perfume in enumerate(self.perfumes):
            for note in perfume.get("all_notes", []):
                self._perfume_by_note[note].append(i)

    # ---------------------------------------------------------------
    # Query Interface
    # ---------------------------------------------------------------

    def query_note_pairings(self, note: str, top_k: int = 10) -> List[Dict]:
        """
        Find notes that co-occur with the given note (Epicure-style pairings).
        Returns top-K neighbors from the NPMI co-occurrence graph.
        """
        neighbors = self._note_neighbors.get(note, [])
        return [
            {"note": n, "npmi": round(score, 4)}
            for n, score in neighbors[:top_k]
        ]

    def query_molecules_by_odor(self, odor_family: str) -> List[Dict]:
        """
        Find all molecules associated with a given odor family.
        Uses the typed molecule-odor graph (Epicure-style Chem queries).
        """
        cas_list = self._molecule_by_odor.get(odor_family, [])
        results = []
        for cas in cas_list:
            mol = self.molecules.get(cas, {})
            if mol:
                results.append({
                    "cas": cas,
                    "name": mol.get("name", ""),
                    "odor_descriptors": mol.get("odor_descriptors", []),
                    "odor_families": mol.get("odor_families", []),
                    "molecular_weight": mol.get("molecular_weight"),
                    "boiling_point": mol.get("boiling_point"),
                })
        return results

    def query_perfumes_by_notes(self, notes: List[str], min_matches: int = 1) -> List[Dict]:
        """
        Find perfumes containing the specified notes.
        Returns perfumes sorted by number of matching notes.
        """
        perfume_scores = defaultdict(int)
        for note in notes:
            for idx in self._perfume_by_note.get(note, []):
                perfume_scores[idx] += 1

        # Filter by minimum matches
        results = []
        for idx, score in sorted(perfume_scores.items(), key=lambda x: x[1], reverse=True):
            if score >= min_matches:
                perfume = self.perfumes[idx]
                results.append({
                    "brand": perfume.get("brand", ""),
                    "name": perfume.get("name", ""),
                    "year": perfume.get("year"),
                    "matching_notes": score,
                    "all_notes": perfume.get("all_notes", []),
                    "top_notes": perfume.get("top_notes", []),
                    "heart_notes": perfume.get("heart_notes", []),
                    "base_notes": perfume.get("base_notes", []),
                    "fragrance_family": perfume.get("fragrance_family"),
                    "main_accords": perfume.get("main_accords", []),
                })
        return results

    def query_accord_template(self, accord_name: str) -> Optional[Dict]:
        """Get a classical accord template by name."""
        accords = self.reference_data.get("classical_accords", {})
        # Fuzzy match
        for key, accord in accords.items():
            if accord_name.lower() in key.lower() or accord_name.lower() in accord.get("name", "").lower():
                return accord
        return None

    def query_perfumer(self, name: str) -> List[Dict]:
        """Find a perfumer by name (fuzzy match)."""
        results = []
        for perfumer in self.reference_data.get("master_perfumers", []):
            if name.lower() in perfumer.get("name", "").lower():
                results.append(perfumer)
        return results

    def query_history(self, period: str = None) -> List[Dict]:
        """Query perfume history, optionally filtered by period name."""
        history = self.reference_data.get("perfume_history", [])
        if period:
            return [h for h in history if period.lower() in h.get("period", "").lower()]
        return history

    def query_ifra(self, substance: str = None) -> Dict:
        """Query IFRA restrictions, optionally filtered by substance name."""
        restrictions = self.reference_data.get("ifra_restrictions", {})
        if substance:
            return {k: v for k, v in restrictions.items() if substance.lower() in k.lower() or substance.lower() in v.get("substance", "").lower()}
        return restrictions

    def query_cultural_tradition(self, tradition: str = None) -> Dict:
        """Query cultural fragrance traditions."""
        traditions = self.reference_data.get("cultural_traditions", {})
        if tradition:
            return {k: v for k, v in traditions.items() if tradition.lower() in k.lower() or tradition.lower() in v.get("name", "").lower()}
        return traditions

    def query_raw_materials(self, category: str = None) -> Dict:
        """Query raw material categories."""
        materials = self.reference_data.get("raw_material_categories", {})
        if category:
            return {k: v for k, v in materials.items() if category.lower() in k.lower() or category.lower() in v.get("name", "").lower()}
        return materials

    def formulate_suggestion(self, brief: Dict) -> Dict:
        """
        Generate a formulation suggestion based on a brief.
        Brief can specify: fragrance_family, key_notes, mood, target_gender, etc.
        Uses accord templates as starting points and augments with co-occurrence data.
        """
        family = brief.get("fragrance_family", "").lower()
        key_notes = brief.get("key_notes", [])
        mood = brief.get("mood", "")

        suggestion = {
            "brief": brief,
            "accord_base": None,
            "suggested_top_notes": [],
            "suggested_heart_notes": [],
            "suggested_base_notes": [],
            "co_occurrence_pairings": {},
            "reference_perfumes": [],
            "ifra_notes": [],
        }

        # Find matching accord template
        for key, accord in self.reference_data.get("classical_accords", {}).items():
            if family and (family in key or family in accord.get("name", "").lower()):
                suggestion["accord_base"] = accord
                break

        # Augment key notes with co-occurrence pairings
        for note in key_notes:
            pairings = self.query_note_pairings(note, top_k=5)
            if pairings:
                suggestion["co_occurrence_pairings"][note] = pairings

        # Find reference perfumes with matching notes
        if key_notes:
            suggestion["reference_perfumes"] = self.query_perfumes_by_notes(key_notes, min_matches=1)[:5]

        # IFRA notes for common restricted materials
        for note in key_notes:
            ifra = self.query_ifra(note)
            if ifra:
                suggestion["ifra_notes"].append({"note": note, "restrictions": ifra})

        return suggestion

    def search(self, query: str) -> Dict:
        """
        General search across the entire knowledge base.
        Returns results from all matching categories.
        """
        results = {
            "notes": [],
            "molecules": [],
            "perfumes": [],
            "accords": [],
            "perfumers": [],
            "history": [],
            "ifra": {},
            "cultural_traditions": {},
            "raw_materials": {},
        }

        query_lower = query.lower()

        # Search notes
        for name, note_data in self.notes.items():
            if query_lower in name.lower() or query_lower in str(note_data).lower():
                results["notes"].append(note_data)

        # Search molecules
        for cas, mol in self.molecules.items():
            mol_name = mol.get("name", "")
            mol_odors = mol.get("odor_descriptors", [])
            mol_families = mol.get("odor_families", [])
            search_text = f"{mol_name} {cas} {' '.join(mol_odors)} {' '.join(mol_families)} {mol.get('notes', '')}"
            if query_lower in search_text.lower():
                results["molecules"].append({"cas": cas, **mol})

        # Search perfumes
        for perfume in self.perfumes:
            if (query_lower in perfume.get("name", "").lower() or
                query_lower in perfume.get("brand", "").lower() or
                query_lower in str(perfume.get("all_notes", [])).lower()):
                results["perfumes"].append(perfume)

        # Search reference data
        ref_results = search_reference(query)
        for r in ref_results:
            cat = r["category"]
            if cat == "classical_accords":
                results["accords"].append(r["data"])
            elif cat == "master_perfumers":
                results["perfumers"].append(r["data"])
            elif cat == "perfume_history":
                results["history"].append(r["data"])
            elif cat == "ifra_restrictions":
                results["ifra"][r.get("key", "")] = r["data"]
            elif cat == "cultural_traditions":
                results["cultural_traditions"][r.get("key", "")] = r["data"]
            elif cat == "raw_material_categories":
                results["raw_materials"][r.get("key", "")] = r["data"]

        return results

    def get_context_for_agent(self, query: str, max_tokens: int = 6000) -> str:
        """
        Retrieve relevant context for the expert agent based on a user query.
        Returns a formatted string that can be injected into the agent's prompt.
        """
        results = self.search(query)
        context_parts = []

        # Add relevant accords
        if results["accords"]:
            context_parts.append("## Relevant Accord Structures")
            for accord in results["accords"][:3]:
                context_parts.append(f"- **{accord.get('name', '')}**: {accord.get('description', '')}")
                if "typical_proportions" in accord:
                    for mat, pct in accord["typical_proportions"].items():
                        context_parts.append(f"  - {mat}: {pct}")

        # Add relevant notes and pairings
        if results["notes"]:
            context_parts.append("\n## Matching Fragrance Notes")
            for note in results["notes"][:10]:
                name = note.get("name", "")
                pairings = self.query_note_pairings(name, top_k=5)
                pairing_str = ", ".join([f"{p['note']} (npmi={p['npmi']})" for p in pairings])
                context_parts.append(f"- **{name}**: pairs with {pairing_str}")

        # Add relevant molecules
        if results["molecules"]:
            context_parts.append("\n## Relevant Aroma Molecules")
            for mol in results["molecules"][:10]:
                context_parts.append(
                    f"- **{mol.get('name', '')}** (CAS {mol.get('cas', '')}): "
                    f"odor = {', '.join(mol.get('odor_descriptors', [])[:5])}"
                )

        # Add reference perfumes
        if results["perfumes"]:
            context_parts.append("\n## Reference Perfumes")
            for p in results["perfumes"][:5]:
                notes_str = ", ".join(p.get("all_notes", [])[:8])
                context_parts.append(
                    f"- **{p.get('brand', '')} - {p.get('name', '')}** "
                    f"({p.get('year', 'n/a')}): {notes_str}"
                )

        # Add perfumer info
        if results["perfumers"]:
            context_parts.append("\n## Master Perfumers")
            for p in results["perfumers"][:3]:
                context_parts.append(
                    f"- **{p.get('name', '')}** ({p.get('era', '')}): "
                    f"{p.get('signature', '')}. Masterpieces: {', '.join(p.get('masterpieces', [])[:3])}"
                )

        # Add IFRA restrictions
        if results["ifra"]:
            context_parts.append("\n## IFRA / Regulatory Notes")
            for key, restriction in results["ifra"].items():
                context_parts.append(
                    f"- **{restriction.get('substance', key)}**: "
                    f"{restriction.get('restriction', '')} — {restriction.get('reason', '')}"
                )

        # Add cultural tradition info
        if results["cultural_traditions"]:
            context_parts.append("\n## Cultural Fragrance Traditions")
            for key, tradition in results["cultural_traditions"].items():
                context_parts.append(
                    f"- **{tradition.get('name', key)}** ({tradition.get('period', '')}): "
                    f"{tradition.get('characteristics', '')[:200]}..."
                )

        # Add history
        if results["history"]:
            context_parts.append("\n## Historical Context")
            for h in results["history"][:2]:
                landmarks = ", ".join(h.get("landmark_fragrances", [])[:3])
                context_parts.append(
                    f"- **{h.get('period', '')}**: {h.get('description', '')[:200]}... "
                    f"Landmarks: {landmarks}"
                )

        # Truncate to max tokens (rough estimate: 4 chars per token)
        full_context = "\n".join(context_parts)
        max_chars = max_tokens * 4
        if len(full_context) > max_chars:
            full_context = full_context[:max_chars] + "\n\n[Context truncated]"

        return full_context
