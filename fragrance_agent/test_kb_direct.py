"""Direct test of knowledge base context generation."""
import sys
sys.path.insert(0, ".")

from knowledge.knowledge_base import FragranceKnowledgeBase

kb = FragranceKnowledgeBase()
kb.load()

print(f"Molecules: {len(kb.molecules)}")
print(f"Notes: {len(kb.notes)}")
print(f"Odor index keys: {list(kb._molecule_by_odor.keys())}")

# Test search
for q in ["floral", "rose", "muguet", "chypre", "oakmoss"]:
    results = kb.search(q)
    print(f"\nQuery: '{q}'")
    print(f"  molecules: {len(results['molecules'])}")
    print(f"  notes: {len(results['notes'])}")
    print(f"  accords: {len(results['accords'])}")
    print(f"  history: {len(results['history'])}")
    print(f"  perfumers: {len(results['perfumers'])}")
    print(f"  ifra: {len(results['ifra'])}")

# Test context generation
for q in ["What molecules give a floral rose odor?"]:
    ctx = kb.get_context_for_agent(q)
    print(f"\nContext for '{q}': {len(ctx)} chars")
    if ctx:
        print(ctx[:500])
