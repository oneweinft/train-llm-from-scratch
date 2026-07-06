"""Quick validation of the full knowledge base."""
import sys
sys.path.insert(0, ".")

from knowledge.knowledge_base import FragranceKnowledgeBase

kb = FragranceKnowledgeBase()
kb.load()

print(f"Molecules: {len(kb.molecules)}")
print(f"Notes: {len(kb.notes)}")
print(f"Co-occurrence edges: {len(kb.cooccurrence_graph.get('edges', []))}")
print(f"Molecule-odor edges: {len(kb.molecule_odor_graph.get('molecule_odor_edges', []))}")

# Test molecule queries by odor family
for family in ["floral", "woody", "citrus", "spicy", "amber", "musky", "aquatic", "gourmand"]:
    mols = kb.query_molecules_by_odor(family)
    print(f"  {family}: {len(mols)} molecules")

# Test reference queries
chypre = kb.query_accord_template("chypre")
print(f"\nChypre accord: {chypre['name'] if chypre else 'not found'}")

ifra = kb.query_ifra("oakmoss")
print(f"IFRA oakmoss entries: {len(ifra)}")

perfumers = kb.query_perfumer("Ellena")
print(f"Perfumer Ellena: {perfumers[0]['masterpieces'][:2] if perfumers else 'not found'}")

traditions = kb.query_cultural_tradition("middle eastern")
print(f"Middle Eastern tradition: {list(traditions.keys())}")

# Test agent end-to-end
from agent.expert_agent import FragranceExpertAgent
agent = FragranceExpertAgent()

queries = [
    "What molecules give a floral rose odor?",
    "Tell me about Iso E Super",
    "What is the chypre accord?",
    "IFRA restrictions on oakmoss",
    "Who created Cool Water?",
]
print("\n=== Agent Query Tests ===")
for q in queries:
    result = agent.query(q)
    context_len = len(result["context"])
    raw = result["raw_results"]
    hits = sum(len(v) if isinstance(v, (list, dict)) else 0 for v in raw.values())
    print(f"  Q: {q}")
    print(f"     Context: {context_len} chars, Search hits: {hits}")

print("\n=== VALIDATION COMPLETE ===")
